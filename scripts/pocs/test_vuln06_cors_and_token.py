#!/usr/bin/env python3
"""
Teste de Verificação e Demonstração - VULN-06: CORS Permissivo e Exposição de Token na URL
Verifica o cabeçalho Access-Control-Allow-Origin: * e a passagem de tokens sensíveis via query string.
"""

import sys
import json
import requests
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
TOKENS_FILE = BASE_DIR / "scripts" / "pocs" / "test_tokens.json"
BACKEND_URL = "http://localhost:5000"

def run_test():
    print("=" * 60)
    print("[TESTE VULN-06] Verificação de CORS Permissivo e Token na Query String")
    print("=" * 60)

    is_vuln = False

    # 1. Testar CORS Wildcard / Permissivo
    print(f"\n[1] Testando política CORS com Origin malicioso (https://evil-attacker.site)...")
    try:
        cors_headers = {
            "Origin": "https://evil-attacker.site",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Authorization,Content-Type"
        }
        r_cors = requests.options(f"{BACKEND_URL}/users/info", headers=cors_headers, timeout=5)
        allow_origin = r_cors.headers.get("Access-Control-Allow-Origin")
        print(f"    Código de resposta Preflight: {r_cors.status_code}")
        print(f"    Access-Control-Allow-Origin:  {allow_origin}")

        if allow_origin == "*" or allow_origin == "https://evil-attacker.site":
            print("    [!] CORS Permissivo detectado! Qualquer origem externa pode fazer requisições.")
            is_vuln = True
        else:
            print("    [*] CORS restrito ou não retornado.")
    except Exception as e:
        print(f"    [-] Erro ao testar CORS: {e}")

    # 2. Testar exposição de token via query string em /users/info
    print(f"\n[2] Testando passagem de token via query parameter em GET /users/info...")
    if TOKENS_FILE.exists():
        with open(TOKENS_FILE, "r") as f:
            tokens = json.load(f)
        alice_token = tokens["alice"].get("idToken") or tokens["alice"].get("id_token")

        try:
            # Chama com id_token na query string
            url = f"{BACKEND_URL}/users/info?id_token={alice_token}"
            print(f"    URL enviada (exposta em access logs, proxies e histórico):")
            print(f"    -> {url[:60]}...[TRUNCATED TOKEN]")
            
            r_info = requests.get(url, timeout=5)
            print(f"    Código de resposta: {r_info.status_code}")
            if r_info.status_code == 200:
                print("    [!] A aplicação aceitou com sucesso o JWT via URL query parameter.")
                print(f"    Dados retornados: {r_info.json()}")
                is_vuln = True
            else:
                print(f"    Resposta: {r_info.status_code} - {r_info.text}")
        except Exception as e:
            print(f"    [-] Erro ao testar rota /users/info: {e}")

    if is_vuln:
        print("\n[ALERTA DE VULNERABILIDADE DETECTADO] VULN-06 CONFIRMADA!")
        print("[!] Foram comprovadas falhas de exposição de token em URL e/ou CORS permissivo.")
        return True
    return False

if __name__ == "__main__":
    vuln = run_test()
    sys.exit(1 if vuln else 0)
