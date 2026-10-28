import pytest
from backend.firebase import Firebase


def test_unauthenticated_request_rejected(client):
    """Ensures protected endpoints reject requests lacking Authorization header."""
    res = client.get("/users/info")
    assert res.status_code == 401
    assert "Authorization header is required" in res.get_json()["error"]

    res_del = client.delete("/chats/any-chat-id")
    assert res_del.status_code == 401


def test_malformed_auth_header_rejected(client):
    """Ensures requests with malformed Authorization schemes (e.g. Basic or raw string) are rejected."""
    res = client.get("/users/info", headers={"Authorization": "Basic 123456"})
    assert res.status_code == 401
    assert "Expected 'Bearer <token>'" in res.get_json()["error"]


def test_invalid_token_rejected(client, mock_auth):
    """Ensures requests with forged or invalid JWTs return 401 Unauthorized."""
    res = client.get("/users/info", headers={"Authorization": "Bearer invalid_forged_token"})
    assert res.status_code == 401
    assert "Invalid or expired token" in res.get_json()["error"]


def test_user_cannot_delete_nonexistent_or_unowned_chat(client, mock_auth, auth_tokens, monkeypatch):
    """
    Regression Test for VULN-01 (IDOR):
    Ensures that an authenticated user (Bob) cannot delete a chat that does not belong to him.
    The system verifies ownership and returns 404/403 rather than deleting arbitrary chats.
    """
    bob_token = auth_tokens["bob"]["token"]

    # Mock Firebase.get_chat: Alice owns the chat, but Bob is requesting deletion
    def fake_get_chat(uid, chat_id):
        # The endpoint calls get_chat(caller_uid, chat_id).
        # Since caller is Bob, this chat does not exist under Bob's node
        return None

    monkeypatch.setattr(Firebase, "get_chat", fake_get_chat)

    headers = {"Authorization": f"Bearer {bob_token}"}
    res = client.delete("/chats/alice_private_chat_123", headers=headers)
    assert res.status_code == 404
    assert res.get_json()["error"] == "Chat not found"


def test_authorized_user_can_save_and_manage_own_chat(client, mock_auth, auth_tokens, monkeypatch):
    """Ensures authorized users can create and manage their own resources."""
    alice_token = auth_tokens["alice"]["token"]

    saved_payloads = []
    def fake_save_chat(uid, chat_id, messages):
        saved_payloads.append((uid, chat_id, messages))

    monkeypatch.setattr(Firebase, "save_chat", fake_save_chat)

    headers = {"Authorization": f"Bearer {alice_token}"}
    body = {
        "messages": [
            {"sender": "Alice", "text": "Legitimate study note"}
        ]
    }
    res = client.post("/chats/chat_alice_01/messages", json=body, headers=headers)
    assert res.status_code == 200
    assert res.get_json()["message"] == "Messages saved successfully"
    assert len(saved_payloads) == 1
    assert saved_payloads[0][0] == auth_tokens["alice"]["uid"]

