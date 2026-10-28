#!/usr/bin/env python3
"""
Authentication helper for CourseSphere PoCs and Tests.
Retrieves fresh ID tokens for Alice and Bob from the Firebase Auth Emulator.
"""

import urllib.request
import json
import os

AUTH_EMULATOR_HOST = os.environ.get("FIREBASE_AUTH_EMULATOR_HOST", "localhost:9099")
SIGNIN_URL = f"http://{AUTH_EMULATOR_HOST}/identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=fake-api-key"

CREDENTIALS = {
    "alice": {
        "email": "alice@test.local",
        "password": "AlicePassword123!"
    },
    "bob": {
        "email": "bob@test.local",
        "password": "BobPassword123!"
    }
}

def get_auth_token(user="alice"):
    """
    Signs in as the specified user ('alice' or 'bob') and returns (uid, id_token).
    """
    if user not in CREDENTIALS:
        raise ValueError(f"Unknown user '{user}'. Available: alice, bob")
        
    creds = CREDENTIALS[user]
    data = json.dumps({
        "email": creds["email"],
        "password": creds["password"],
        "returnSecureToken": True
    }).encode("utf-8")
    
    req = urllib.request.Request(SIGNIN_URL, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return body["localId"], body["idToken"]
    except Exception as e:
        raise RuntimeError(f"Failed to authenticate {user} against Auth Emulator: {e}")

if __name__ == "__main__":
    print("[*] Testing Auth Helper...")
    try:
        alice_uid, alice_token = get_auth_token("alice")
        print(f"[+] Alice UID: {alice_uid}")
        print(f"[+] Alice Token: {alice_token[:30]}...")
        bob_uid, bob_token = get_auth_token("bob")
        print(f"[+] Bob UID: {bob_uid}")
        print(f"[+] Bob Token: {bob_token[:30]}...")
    except Exception as e:
        print(f"[-] Emulator offline or error: {e}")

