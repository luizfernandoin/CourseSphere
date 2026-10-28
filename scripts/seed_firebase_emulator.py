#!/usr/bin/env python3
"""
Seed script for Firebase Emulator Suite (CourseSphere)
Populates Auth Emulator and Realtime Database Emulator with test users:
- Alice (alice@test.local): Regular legitimate user
- Bob (bob@test.local): Second user / Attacker persona for access control tests

Requires NO external dependencies (uses standard library urllib).
"""

import urllib.request
import urllib.error
import json
import sys
import os

AUTH_EMULATOR_HOST = os.environ.get("FIREBASE_AUTH_EMULATOR_HOST", "localhost:9099")
RTDB_EMULATOR_HOST = os.environ.get("FIREBASE_DATABASE_EMULATOR_HOST", "localhost:9000")
PROJECT_ID = os.environ.get("FIREBASE_PROJECT", "coursesphere-8bd9a")

AUTH_BASE_URL = f"http://{AUTH_EMULATOR_HOST}/identitytoolkit.googleapis.com/v1"
RTDB_BASE_URL = f"http://{RTDB_EMULATOR_HOST}"

USERS_SEED = [
    {
        "email": "alice@test.local",
        "password": "AlicePassword123!",
        "displayName": "Alice Smith",
        "info": {
            "majors": "Computer Science",
            "minors": "Mathematics",
            "year": "Senior",
            "college": "Engineering",
            "courses": "CS 4820, CS 4410, CS 5412",
            "about": "Estudante de graduação focada em Segurança e Sistemas Distribuídos."
        },
        "chats": {
            "chat_alice_algorithms": {
                "title": "Algoritmos Avançados",
                "messages": {
                    "msg_01": {"sender": "alice", "text": "Como funciona o algoritmo de Dijkstra com heap binária?"},
                    "msg_02": {"sender": "assistant", "text": "Com min-heap, a complexidade passa para O((V + E) log V)."}
                }
            },
            "chat_alice_private": {
                "title": "Anotações Pessoais de Segurança",
                "messages": {
                    "msg_01": {"sender": "alice", "text": "Lembrete: nunca expor o Werkzeug debug em produção!"}
                }
            }
        }
    },
    {
        "email": "bob@test.local",
        "password": "BobPassword123!",
        "displayName": "Bob Walker",
        "info": {
            "majors": "Information Science",
            "minors": "Design",
            "year": "Sophomore",
            "college": "Arts and Sciences",
            "courses": "INFO 2950, INFO 1300",
            "about": "Estudante explorando segurança ofensiva e testes de autorização."
        },
        "chats": {
            "chat_bob_project": {
                "title": "Projeto Semestral",
                "messages": {
                    "msg_01": {"sender": "bob", "text": "Iniciando a pesquisa de vulnerabilidades OWASP Top 10."}
                }
            }
        }
    }
]

def make_request(url, method="GET", data=None, headers=None):
    if headers is None:
        headers = {}
    if data is not None and isinstance(data, (dict, list)):
        data = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
        
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_body = response.read().decode("utf-8")
            if not res_body or res_body.strip() == "null":
                return {}
            return json.loads(res_body)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            return {"error_status": e.code, "error_body": json.loads(err_body)}
        except Exception:
            return {"error_status": e.code, "error_body": err_body}
    except Exception as e:
        return {"error_status": 0, "error_body": str(e)}

def check_emulators_healthy():
    print(f"[*] Verificando emulador de autenticação em {AUTH_EMULATOR_HOST}...")
    auth_check = make_request(f"http://{AUTH_EMULATOR_HOST}/", method="GET")
    if isinstance(auth_check, dict) and auth_check.get("error_status") == 0:
        print(f"[-] Erro: Não foi possível conectar ao Auth Emulator em {AUTH_EMULATOR_HOST}")
        return False
    
    print(f"[*] Verificando emulador do Realtime Database em {RTDB_EMULATOR_HOST}...")
    rtdb_check = make_request(f"{RTDB_BASE_URL}/.json?ns={PROJECT_ID}", method="GET")
    if isinstance(rtdb_check, dict) and rtdb_check.get("error_status") == 0:
        print(f"[-] Erro: Não foi possível conectar ao Realtime Database Emulator em {RTDB_EMULATOR_HOST}")
        return False

    print("[+] Emuladores acessíveis e operacionais!")
    return True

def create_or_signin_user(user_cfg):
    email = user_cfg["email"]
    password = user_cfg["password"]
    
    # Try sign in first
    signin_url = f"{AUTH_BASE_URL}/accounts:signInWithPassword?key=fake-api-key"
    res = make_request(signin_url, method="POST", data={
        "email": email,
        "password": password,
        "returnSecureToken": True
    })
    
    if "idToken" in res:
        print(f"[+] Usuário {email} autenticado com sucesso (UID: {res['localId']})")
        return res
    
    # If user doesn't exist, sign up
    signup_url = f"{AUTH_BASE_URL}/accounts:signUp?key=fake-api-key"
    res = make_request(signup_url, method="POST", data={
        "email": email,
        "password": password,
        "returnSecureToken": True
    })
    
    if "idToken" in res:
        print(f"[+] Usuário {email} criado com sucesso (UID: {res['localId']})")
        return res
    
    print(f"[-] Falha ao autenticar/criar {email}: {res}")
    return None

def seed_database_for_user(uid, id_token, user_cfg):
    print(f"[*] Populando perfil de {user_cfg['email']} no Realtime Database...")
    info_url = f"{RTDB_BASE_URL}/users/{uid}/info.json?ns={PROJECT_ID}"
    res = make_request(info_url, method="PUT", data=user_cfg["info"])
    if "error_status" in res:
        print(f"[-] Erro ao salvar info de {uid}: {res}")
    else:
        print(f"[+] Perfil de {uid} salvo com sucesso.")
        
    for chat_id, chat_data in user_cfg.get("chats", {}).items():
        chat_url = f"{RTDB_BASE_URL}/users/{uid}/chats/{chat_id}.json?ns={PROJECT_ID}"
        c_res = make_request(chat_url, method="PUT", data=chat_data)
        if "error_status" in c_res:
            print(f"[-] Erro ao criar chat {chat_id} para {uid}: {c_res}")
        else:
            print(f"[+] Chat '{chat_id}' criado com sucesso.")

def main():
    print("=" * 60)
    print(" CourseSphere — Seed do Firebase Emulator Suite")
    print(f" Projeto: {PROJECT_ID}")
    print(f" Auth: {AUTH_EMULATOR_HOST} | RTDB: {RTDB_EMULATOR_HOST}")
    print("=" * 60)
    
    if not check_emulators_healthy():
        print("\n[!] DICA: Inicie os emuladores antes de rodar o seed:")
        print("    Docker: docker compose up firebase-emulator")
        print("    Local:  cd infra/firebase-emulator && firebase emulators:start\n")
        sys.exit(1)
        
    tokens_output = {}
    
    for u in USERS_SEED:
        auth_data = create_or_signin_user(u)
        if auth_data:
            uid = auth_data["localId"]
            token = auth_data["idToken"]
            seed_database_for_user(uid, token, u)
            tokens_output[u["email"].split("@")[0]] = {
                "email": u["email"],
                "uid": uid,
                "idToken": token,
                "refreshToken": auth_data.get("refreshToken", "")
            }
            
    # Save tokens to helper file
    os.makedirs("scripts/pocs", exist_ok=True)
    tokens_path = os.path.join("scripts", "pocs", "test_tokens.json")
    with open(tokens_path, "w", encoding="utf-8") as f:
        json.dump(tokens_output, f, indent=2)
    print(f"\n[+] Tokens de autenticação salvos em: {tokens_path}")
    print("[+] Seed do Firebase Emulator concluído com sucesso!\n")

if __name__ == "__main__":
    main()

