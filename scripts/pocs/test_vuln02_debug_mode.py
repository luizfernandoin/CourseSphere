#!/usr/bin/env python3
"""
Teste de Verificação e Demonstração - VULN-02: Debug Mode Ativo e Exposição de Stack Trace
Verifica a exposição de informações sensíveis quando o Flask opera com debug=True.
"""

import sys
import requests

BACKEND_URL = "http://localhost:5000"

def run_test():
    print("=" * 60)
    print("[TESTE VULN-02] Verificação de Debug Mode e Stack Trace Exposure")
    print("=" * 60)

    # 1. Testar endpoint inexistente ou que force erro
    print(f"[*] Enviando requisição para rota propositalmente inválida em {BACKEND_URL}/nonexistent-route...")
    try:
        r_404 = requests.get(f"{BACKEND_URL}/nonexistent-route", timeout=5)
        print(f"[*] Código retornado: {r_404.status_code}")
    except Exception as e:
        print(f"[-] Erro ao conectar ao backend: {e}")
        return False

    # 2. Testar chamada com payload corrompido para acionar exceção não tratada
    print(f"\n[*] Enviando requisição malformada para /chats/trigger_error/messages sem JSON body...")
    try:
        r_err = requests.post(
            f"{BACKEND_URL}/chats/invalid_chat_id/messages",
            headers={"Content-Type": "application/json"},
            data="invalid-not-json-{{{",
            timeout=5
        )
        print(f"[*] Código retornado: {r_err.status_code}")
        print(f"[*] Headers da resposta: {dict(r_err.headers)}")

        # Verificar se expõe detalhes internos de depuração ou biblioteca
        body = r_err.text
        server_header = r_err.headers.get("Server", "")
        print(f"[*] Server Header: {server_header}")

        # In endpoints.py:
        # app.run(debug=True, host="0.0.0.0", port=5000)
        # When run under Gunicorn or Flask, debug mode or exception handler may leak traceback
        # Let's check /users/info without required parameter or invalid token
        r_token = requests.get(f"{BACKEND_URL}/users/info?id_token=malformed_token_123", timeout=5)
        print(f"\n[*] Testando /users/info com token malformado...")
        print(f"[*] Código retornado: {r_token.status_code}")
        print(f"[*] Corpo da resposta (vazamento de erro interno): {r_token.text}")

        has_trace_or_debug = (
            "Traceback" in r_err.text or
            "Traceback" in r_token.text or
            "Firebase" in r_token.text or
            "Error verifying ID token" in r_token.text or
            "Wrong number of segments" in r_token.text or
            "Exception" in r_token.text
        )

        # 3. Verificar configuração estática em backend/endpoints.py
        with open("backend/endpoints.py", "r", encoding="utf-8") as f:
            code = f.read()
        debug_in_code = "debug=True" in code

        if has_trace_or_debug or debug_in_code:
            print("\n[ALERTA DE VULNERABILIDADE DETECTADO] VULN-02 CONFIRMADA!")
            if debug_in_code:
                print("[!] Configuração 'app.run(debug=True)' ativa no código de produção.")
            if has_trace_or_debug:
                print("[!] Exposição de mensagens internas de erro/exceção da SDK no corpo da resposta HTTP.")
            return True
        else:
            print("[*] Resposta sanitizada ou tratada.")
            return False

    except Exception as e:
        print(f"[-] Erro ao executar teste: {e}")
        return False

if __name__ == "__main__":
    is_vuln = run_test()
    sys.exit(0 if is_vuln else 1)
