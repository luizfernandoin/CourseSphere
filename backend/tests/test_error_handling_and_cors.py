import pytest
from backend.endpoints import app


def test_debug_mode_disabled():
    """
    Regression Test for VULN-02:
    Verifies that Flask debug mode is disabled by default to prevent Werkzeug debugger exposure.
    """
    assert app.debug is False


def test_error_handlers_prevent_stack_trace_leakage(client):
    """
    Regression Test for VULN-02:
    Ensures that unexpected or malformed requests do not expose python stack traces
    or sensitive internal paths in the response body.
    """
    # Test nonexistent route
    res_404 = client.get("/nonexistent-endpoint-404")
    assert res_404.status_code == 404
    assert "error" in res_404.get_json()
    assert "Traceback" not in res_404.text

    # Test malformed payload on POST
    res_malformed = client.post(
        "/users/create",
        data="invalid-not-json-{{{",
        content_type="application/json"
    )
    assert res_malformed.status_code in [400, 500]
    assert "Traceback" not in res_malformed.text


def test_token_in_query_string_rejected(client):
    """
    Regression Test for VULN-06:
    Ensures that passing authentication tokens via URL query parameters
    (e.g. GET /users/info?id_token=...) is no longer accepted, enforcing Authorization header.
    """
    res = client.get("/users/info?id_token=some_token_in_url")
    assert res.status_code == 401
    assert "Authorization header is required" in res.get_json()["error"]


def test_cors_policy_rejects_untrusted_origins(client):
    """
    Regression Test for VULN-06:
    Verifies that untrusted origins (e.g. https://evil-attacker.site)
    do not receive an Access-Control-Allow-Origin response from the API.
    """
    headers = {
        "Origin": "https://evil-attacker.site",
        "Access-Control-Request-Method": "GET"
    }
    res = client.options("/courses", headers=headers)
    allow_origin = res.headers.get("Access-Control-Allow-Origin")
    # Untrusted origin should NOT be reflected in Access-Control-Allow-Origin
    assert allow_origin != "*"
    assert allow_origin != "https://evil-attacker.site"

