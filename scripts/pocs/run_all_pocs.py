#!/usr/bin/env python3
"""
Orquestrador Geral de Execução de Verificação e Re-teste de Vulnerabilidades
Executa a suíte de verificação contra a stack local e consolida o relatório de re-teste.
"""

import sys
import subprocess
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
POCS_DIR = BASE_DIR / "scripts" / "pocs"
REPORT_FILE = BASE_DIR / "docs" / "evidencias" / "RELATORIO_EXECUCAO_RETESTE.md"

POCS = [
    ("VULN-01", "Broken Access Control & IDOR", "test_vuln01_idor.py"),
    ("VULN-02", "Debug Mode & Information Disclosure", "test_vuln02_debug_mode.py"),
    ("VULN-03", "SQL Injection em Consultas de Cursos", "test_vuln03_sqli.py"),
    ("VULN-04", "Hardcoded Credentials & Git Leakage", "test_vuln04_credentials.py"),
    ("VULN-05", "Outdated & Vulnerable Components", "test_vuln05_components.py"),
    ("VULN-06", "Permissive CORS & Token in Query String", "test_vuln06_cors_and_token.py"),
]

def main():
    print("=" * 70)
    print(" COURSESPHERE - EXECUÇÃO DE SUÍTE DE RE-TESTE DE SEGURANÇA")
    print("=" * 70)

    results = []

    for vid, name, script_name in POCS:
        script_path = POCS_DIR / script_name
        print(f"\n>>> Executando {vid}: {name} ({script_name})...")
        if not script_path.exists():
            print(f"[-] Script {script_name} não encontrado.")
            results.append((vid, name, "NÃO ENCONTRADO", "Script inexistente"))
            continue

        try:
            cmd = [sys.executable, str(script_path)]
            proc = subprocess.run(cmd, cwd=str(BASE_DIR), capture_output=True, text=True, timeout=30)
            status = "MITIGADA / CONTROLE EFETIVO" if proc.returncode == 0 else "VULNERABILIDADE DETECTADA"
            output = proc.stdout + "\n" + proc.stderr
            print(output)
            results.append((vid, name, status, output))
        except Exception as e:
            print(f"[-] Erro ao executar {script_name}: {e}")
            results.append((vid, name, "ERRO DE EXECUÇÃO", str(e)))

    # Gravar Relatório Consolidado de Re-teste
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("# Relatório de Re-teste de Segurança Pós-Remediação\n\n")
        f.write(f"- **Data da Execução:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("- **Ambiente:** Local Isolado (Docker Compose, Firebase Emulator Suite, SQLite Local)\n\n")
        f.write("## 1. Sumário Executivo de Re-teste\n\n")
        f.write("| ID | Vulnerabilidade | Status Pós-Remediação | Severidade Original |\n")
        f.write("|---|---|---|---|\n")

        severities = {
            "VULN-01": "Alta (CVSS 7.5)",
            "VULN-02": "Alta (CVSS 8.5)",
            "VULN-03": "Alta (CVSS 7.5)",
            "VULN-04": "Alta (CVSS 7.5)",
            "VULN-05": "Alta (CVSS 8.6)",
            "VULN-06": "Média (CVSS 6.5)"
        }

        for vid, name, status, _ in results:
            sev = severities.get(vid, "N/A")
            f.write(f"| `{vid}` | {name} | **{status}** | {sev} |\n")

        f.write("\n---\n\n## 2. Detalhamento e Logs da Execução de Re-teste\n\n")
        for vid, name, status, output in results:
            f.write(f"### {vid}: {name}\n")
            f.write(f"- **Resultado:** `{status}`\n")
            f.write("```text\n")
            f.write(output.strip() + "\n")
            f.write("```\n\n")

    print(f"\n[+] Relatório de re-teste consolidado gerado com sucesso em: {REPORT_FILE}")

if __name__ == "__main__":
    main()
