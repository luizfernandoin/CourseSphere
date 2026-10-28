import functools
from flask import request, jsonify, g

try:
    from backend.firebase import Firebase
except ImportError:
    from firebase import Firebase


def require_auth(f):
    """
    Decorator that enforces JWT authentication on protected endpoints.
    Extracts Bearer token from Authorization header and verifies it via Firebase Admin SDK.
    Injects authenticated user payload into Flask request context (g.current_user, g.uid).
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header:
            return jsonify({"error": "Authorization header is required"}), 401

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({"error": "Invalid Authorization header format. Expected 'Bearer <token>'"}), 401

        token = parts[1]
        try:
            decoded_token = Firebase.verify_id_token(token)
            g.current_user = decoded_token
            g.uid = decoded_token.get("uid")
        except Exception:
            return jsonify({"error": "Invalid or expired token"}), 401

        return f(*args, **kwargs)

    return decorated_function


def get_current_user():
    """Returns the decoded token dictionary of the authenticated user in the current context."""
    return getattr(g, "current_user", None)


def get_current_uid():
    """Returns the UID string of the authenticated user in the current context."""
    return getattr(g, "uid", None)
