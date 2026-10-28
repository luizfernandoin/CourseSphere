import pytest
from backend.endpoints import app


def test_http_security_headers_injected(client):
    """
    Verifies that baseline OWASP security headers are injected into every HTTP response.
    """
    res = client.get("/courses")
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert res.headers.get("X-XSS-Protection") == "0"
    assert res.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "Content-Security-Policy" in res.headers
    assert "Permissions-Policy" in res.headers


def test_max_content_length_enforced(client):
    """
    Verifies that payloads exceeding MAX_CONTENT_LENGTH (1MB) are rejected with HTTP 413.
    """
    oversized_data = "A" * (1024 * 1024 + 100)  # > 1MB
    res = client.post(
        "/users/create",
        data=oversized_data,
        content_type="application/json"
    )
    assert res.status_code == 413
    assert "Payload exceeds maximum permitted size" in res.get_json()["error"]


def test_user_creation_input_validation(client):
    """
    Verifies schema validation on /users/create: invalid email or weak password must be rejected.
    """
    # 1. Invalid email
    res_bad_email = client.post("/users/create", json={"email": "not-an-email", "password": "validPassword123"})
    assert res_bad_email.status_code == 400
    assert "A valid email address is required" in res_bad_email.get_json()["error"]

    # 2. Short password
    res_short_pwd = client.post("/users/create", json={"email": "user@test.local", "password": "123"})
    assert res_short_pwd.status_code == 400
    assert "at least 8 characters" in res_short_pwd.get_json()["error"]


def test_chat_messages_schema_validation(client, mock_auth, auth_tokens):
    """
    Verifies schema and length validation on /chats/<chat_id>/messages.
    """
    alice_token = auth_tokens["alice"]["token"]
    headers = {"Authorization": f"Bearer {alice_token}"}

    # 1. Empty messages array
    res_empty = client.post("/chats/chat_test/messages", json={"messages": []}, headers=headers)
    assert res_empty.status_code == 400
    assert "non-empty array" in res_empty.get_json()["error"]

    # 2. Oversized message text
    oversized_msg = [{"sender": "Alice", "text": "X" * 4001}]
    res_oversized = client.post("/chats/chat_test/messages", json={"messages": oversized_msg}, headers=headers)
    assert res_oversized.status_code == 400
    assert "exceeds maximum length" in res_oversized.get_json()["error"]


def test_rate_limiting_enforcement(client):
    """
    Verifies that rapid successive requests trigger the rate limiter (HTTP 429 Too Many Requests).
    """
    # The /users/create endpoint has a limit of 10 per minute
    # Trigger requests until limit is hit or loop finishes
    status_codes = []
    for _ in range(15):
        res = client.post("/users/create", json={"email": "bad", "password": "bad"})
        status_codes.append(res.status_code)

    assert 429 in status_codes

