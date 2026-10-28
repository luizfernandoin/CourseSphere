import os
import sys
import json
import pytest
from pathlib import Path

# Add backend directory and project root to Python path
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Ensure dummy credentials exist so Firebase Admin SDK initializes without cloud dependency
dummy_creds = BACKEND_DIR / "credentials.dummy.json"
target_creds = BACKEND_DIR / "credentials.json"
if dummy_creds.exists() and not target_creds.exists():
    import shutil
    shutil.copy(str(dummy_creds), str(target_creds))

from backend.endpoints import app
from backend.firebase import Firebase

TOKENS_FILE = PROJECT_ROOT / "scripts" / "pocs" / "test_tokens.json"


@pytest.fixture
def client():
    """Provides a Flask test client configured for testing."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def auth_tokens():
    """Returns test tokens for Alice and Bob if present, otherwise returns mock tokens."""
    if TOKENS_FILE.exists():
        try:
            with open(TOKENS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {
                    "alice": {
                        "uid": data["alice"]["uid"],
                        "token": data["alice"].get("idToken") or data["alice"].get("id_token")
                    },
                    "bob": {
                        "uid": data["bob"]["uid"],
                        "token": data["bob"].get("idToken") or data["bob"].get("id_token")
                    }
                }
        except Exception:
            pass

    return {
        "alice": {"uid": "mock_alice_uid_101", "token": "mock_token_alice"},
        "bob": {"uid": "mock_bob_uid_202", "token": "mock_token_bob"}
    }


@pytest.fixture
def mock_auth(monkeypatch, auth_tokens):
    """Mocks Firebase token verification for standalone unit testing."""
    def fake_verify_id_token(token, check_revoked=False):
        if token == auth_tokens["alice"]["token"]:
            return {"uid": auth_tokens["alice"]["uid"], "email": "alice@test.local"}
        elif token == auth_tokens["bob"]["token"]:
            return {"uid": auth_tokens["bob"]["uid"], "email": "bob@test.local"}
        raise ValueError("Invalid ID token")

    monkeypatch.setattr(Firebase, "verify_id_token", fake_verify_id_token)
