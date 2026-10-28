#!/usr/bin/env python3
"""
Teste de Verificação e Demonstração - VULN-05: Outdated and Vulnerable Components
Analisa os relatórios de auditoria de dependências (npm audit e pip-audit).
"""

import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
NPM_AUDIT_FILE = BASE_DIR / "docs" / "evidencias" / "sca" / "npm-audit.json"
PIP_AUDIT_FILE = BASE_DIR / "docs" / "evidencias" / "sca" / "pip-audit.json"

def run_test():
    print("=" * 60)
    print("[TESTE VULN-05] Verificação de Componentes Desatualizados e Vulneráveis")
    print("=" * 60)

    critical_count = 0
    high_count = 0
    total_vulns = 0

    if NPM_AUDIT_FILE.exists():
        with open(NPM_AUDIT_FILE, "r", encoding="utf-8") as f:
            npm_data = json.load(f)
        metadata = npm_data.get("metadata", {}).get("vulnerabilities", {})
        critical_count += metadata.get("critical", 0)
        high_count += metadata.get("high", 0)
        total_vulns += metadata.get("total", 0)
        print(f"\n[1] Auditoria Frontend (NPM):")
        print(f"    - Críticas: {metadata.get('critical', 0)}")
        print(f"    - Altas:    {metadata.get('high', 0)}")
        print(f"    - Moderadas:{metadata.get('moderate', 0)}")
        print(f"    - Baixas:   {metadata.get('low', 0)}")
        print(f"    - Total:    {metadata.get('total', 0)}")

        # Destacar os pacotes mais graves
        vulnerabilities = npm_data.get("vulnerabilities", {})
        print("\n    Principais pacotes comprometidos identificados:")
        for pkg_name, details in list(vulnerabilities.items())[:5]:
            severity = details.get("severity")
            print(f"      * {pkg_name} ({severity}) - via {details.get('via')}")

    if PIP_AUDIT_FILE.exists():
        try:
            with open(PIP_AUDIT_FILE, "r", encoding="utf-8") as f:
                pip_data = json.load(f)
            print(f"\n[2] Auditoria Backend (PIP):")
            print(f"    - Dependências analisadas: {len(pip_data.get('dependencies', []))}")
        except Exception:
            pass

    if critical_count > 0 or high_count > 0:
        print("\n[ALERTA DE VULNERABILIDADE DETECTADO] VULN-05 CONFIRMADA!")
        print(f"[!] Aplicação depende de {critical_count} pacotes com severidade CRÍTICA e {high_count} com severidade ALTA.")
        return True
    return False

if __name__ == "__main__":
    is_vuln = run_test()
    sys.exit(0 if is_vuln else 1)

