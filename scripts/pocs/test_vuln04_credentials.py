#!/usr/bin/env python3
"""
Teste de Verificação e Demonstração - VULN-04: Credenciais e Chaves Hardcoded
Verifica a presença de credenciais sensíveis no repositório e no histórico Git.
"""

import sys
import json
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
REDDIT_KEY_FILE = BASE_DIR / "backend" / "cornell-course-sphere-data" / "reddit-data" / "reddit_key.json"

def run_test():
    print("=" * 60)
    print("[TESTE VULN-04] Verificação de Credenciais Hardcoded e Histórico Git")
    print("=" * 60)

    found_vulns = []

    # 1. Verificar arquivo reddit_key.json
    print(f"\n[1] Verificando existência de {REDDIT_KEY_FILE}...")
    if REDDIT_KEY_FILE.exists():
        with open(REDDIT_KEY_FILE, "r") as f:
            data = json.load(f)
        client_id = data.get("client_id")
        client_secret = data.get("client_secret")
        print(f"    [!] ARQUIVO PRESENTE NO DIRETÓRIO DE TRABALHO:")
        print(f"        client_id:     {client_id}")
        print(f"        client_secret: {'*' * (len(client_secret)-4) + client_secret[-4:] if client_secret else 'N/A'}")
        if client_id and client_secret:
            found_vulns.append("reddit_key.json no working directory")

    # 2. Verificar histórico Git usando git log
    print("\n[2] Verificando histórico de commits do Git para credenciais vazadas...")
    try:
        git_cmd = ["git", "log", "-S", "client_secret", "--pretty=format:%h %an %ad %s", "--date=short"]
        result = subprocess.run(git_cmd, cwd=str(BASE_DIR), capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            print("    [!] Commits no histórico contendo chaves sensíveis:")
            for line in result.stdout.strip().split("\n"):
                print(f"        -> {line}")
            found_vulns.append("Segredos no histórico do Git")
        else:
            print("    [*] Nenhum commit encontrado via git log.")
    except Exception as e:
        print(f"    [-] Erro ao executar git log: {e}")

    # 3. Verificar presence de git-secrets audit
    audit_file = BASE_DIR / "docs" / "evidencias" / "sast" / "git_secrets_audit.json"
    if audit_file.exists():
        with open(audit_file, "r") as f:
            audit = json.load(f)
        total_findings = len(audit) if isinstance(audit, list) else audit.get("total_findings", 0)
        print(f"\n[3] Evidência automatizada em {audit_file}:")
        print(f"    Total de ocorrências de segredos detectadas: {total_findings}")
        if total_findings > 0:
            found_vulns.append(f"{total_findings} segredos catalogados no SAST")

    if found_vulns:
        print("\n[ALERTA DE VULNERABILIDADE DETECTADO] VULN-04 CONFIRMADA!")
        print(f"[!] Credenciais ativas ou sensíveis expostas:")
        for v in found_vulns:
            print(f"    - {v}")
        return True
    return False

if __name__ == "__main__":
    is_vuln = run_test()
    sys.exit(0 if is_vuln else 1)
