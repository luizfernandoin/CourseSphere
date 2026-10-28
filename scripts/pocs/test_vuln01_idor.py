#!/usr/bin/env python3
"""
Teste de Verificação e Demonstração - VULN-01: Broken Access Control & IDOR
Verifica os controles de autorização no Backend e no Firebase Realtime Database.
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
RTDB_NS = "coursesphere-8bd9a-default-rtdb"

def run_test():
    print("=" * 60)
    print("[TESTE VULN-01] Broken Access Control & IDOR Verification")
    print("=" * 60)

    if not TOKENS_FILE.exists():
        print(f"[-] Arquivo de tokens não encontrado em {TOKENS_FILE}.")
        return False

    with open(TOKENS_FILE, "r") as f:
        tokens = json.load(f)

    alice_uid = tokens["alice"]["uid"]
    alice_token = tokens["alice"].get("idToken") or tokens["alice"].get("id_token")
    bob_uid = tokens["bob"]["uid"]
    bob_token = tokens["bob"].get("idToken") or tokens["bob"].get("id_token")

    print(f"[+] Alice UID: {alice_uid}")
    print(f"[+] Bob UID:   {bob_uid}")

    chat_id = "chat_alice_secret_123"
    alice_chat_data = {
        "title": "Aconselhamento Academico Privado",
        "created_at": "2026-10-28T10:00:00Z",
        "messages": {
            "msg-01": {"sender": "Alice", "text": "Mensagem confidencial com notas e histórico."}
        }
    }

    # 1. Criação do chat privado da Alice
    print("\n[Passo 1] Alice cria conversa confidencial no Realtime Database...")
    r_put = requests.put(
        f"{RTDB_URL}/users/{alice_uid}/chats/{chat_id}.json?ns={RTDB_NS}&auth={alice_token}",
        json=alice_chat_data,
        timeout=5
    )
    if r_put.status_code == 200:
        print("[+] Conversa da Alice criada com sucesso (HTTP 200).")
    else:
        print(f"[-] Falha ao criar conversa: {r_put.status_code} - {r_put.text}")

    # 2. Teste de Leitura Não Autorizada (IDOR) no Realtime Database
    print("\n[Passo 2] Bob tenta ler diretamente os dados de Alice no Realtime Database...")
    r_idor_read = requests.get(
        f"{RTDB_URL}/users/{alice_uid}/chats/{chat_id}.json?ns={RTDB_NS}&auth={bob_token}",
        timeout=5
    )
    print(f"[*] Código retornado para Bob: {r_idor_read.status_code}")
    print(f"[*] Resposta: {r_idor_read.text.strip()}")

    rtdb_blocked = r_idor_read.status_code in [401, 403]

    # 3. Teste de Exclusão Não Autorizada (IDOR) no Backend
    print("\n[Passo 3] Bob tenta deletar a conversa de Alice via DELETE /chats/<chat_id> no Backend...")
    try:
        r_del = requests.delete(
            f"{BACKEND_URL}/chats/{chat_id}",
            headers={"Authorization": f"Bearer {bob_token}"},
            timeout=5
        )
        print(f"[*] Resposta do Backend: {r_del.status_code} - {r_del.text.strip()}")
        backend_blocked = r_del.status_code in [403, 404]
    except Exception as e:
        print(f"[-] Erro ao conectar ao Backend: {e}")
        backend_blocked = False

    # 4. Avaliação
    if rtdb_blocked and backend_blocked:
        print("\n[RESULTADO] VULN-01 MITIGADA COM SUCESSO!")
        print("[+] Tentativa de leitura não autorizada bloqueada pelo Realtime Database (Permission denied).")
        print("[+] Tentativa de deleção não autorizada bloqueada pelo Backend (Recurso não encontrado/pertencente).")
        return False  # False = Não vulnerável (corrigida)
    else:
        print("\n[ALERTA DE VULNERABILIDADE DETECTADO] VULN-01 AINDA VULNERÁVEL!")
        return True

if __name__ == "__main__":
    is_vuln = run_test()
    # Exit code 0 if mitigated/secure for automated re-tests, or flag accordingly
    sys.exit(0 if not is_vuln else 1)
