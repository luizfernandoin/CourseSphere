#!/usr/bin/env python3
"""
Teste de Verificação e Demonstração - VULN-03: SQL Injection em Consultas de Cursos
Verifica a mitigação através de consultas parametrizadas na rota de cursos.
"""

import sys
import requests
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_URL = "http://localhost:5000"

def run_test():
    print("=" * 60)
    print("[TESTE VULN-03] Verificação de SQL Injection (blueprints/courses.py)")
    print("=" * 60)

    # 1. Consulta ao endpoint /courses
    print("\n[1] Verificando listagem geral em /courses...")
    try:
        r_list = requests.get(f"{BACKEND_URL}/courses", timeout=5)
        print(f"    Status: {r_list.status_code}")
        total_courses = len(r_list.json()) if r_list.status_code == 200 and isinstance(r_list.json(), list) else 0
        print(f"    Total de cursos cadastrados: {total_courses}")
    except Exception as e:
        print(f"    [-] Falha ao acessar /courses: {e}")
        return False

    # 2. Teste de Injeção SQL na rota /courses/semester/<payload>
    payload = "' OR '1'='1"
    print(f"\n[2] Testando payload malicioso em {BACKEND_URL}/courses/semester/{payload}...")
    try:
        r_sqli = requests.get(f"{BACKEND_URL}/courses/semester/{payload}", timeout=5)
        print(f"    Status HTTP: {r_sqli.status_code}")
        print(f"    Resposta:    {r_sqli.text.strip()}")

        # Se for vulnerável a concatenação, a query retornaria 200 com TODOS os cursos
        # Se estiver parametrizado, busca literalmente pelo semestre "' OR '1'='1", retornando 404
        if r_sqli.status_code == 200 and len(r_sqli.json()) > 1:
            print("\n[ALERTA DE VULNERABILIDADE DETECTADO] VULN-03 CONFIRMADA!")
            print(f"[!] A aplicação retornou todos os {len(r_sqli.json())} cursos, comprovando SQL Injection.")
            return True
        elif r_sqli.status_code == 404:
            print("\n[RESULTADO] VULN-03 MITIGADA COM SUCESSO!")
            print("[+] O payload foi tratado como parâmetro literal pelo SQLite (nenhum curso encontrado).")
            return False
        else:
            print(f"[*] Resposta: {r_sqli.status_code}")
            return False
    except Exception as e:
        print(f"    [-] Erro ao testar rota: {e}")
        return False

if __name__ == "__main__":
    is_vuln = run_test()
    sys.exit(0 if not is_vuln else 1)
