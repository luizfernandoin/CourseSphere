import os
from flask import request, jsonify, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

def get_client_identifier():
    """
    Determines client identity for rate limiting purposes.
    Prefers authenticated user UID (g.uid) if present,
    otherwise falls back to client IP address (considering reverse proxy X-Forwarded-For).
    """
    uid = getattr(g, "uid", None)
    if uid:
        return f"uid:{uid}"

    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
        return f"ip:{client_ip}"

    return f"ip:{request.remote_addr or 'unknown'}"


def init_rate_limiter(app):
    """
    Initializes and attaches Flask-Limiter to the Flask application.
    Uses Redis backend if configured, falling back to in-memory storage for test/offline environments.
    """
    redis_url = os.environ.get("REDIS_URL", "memory://")
    storage_uri = redis_url if not app.config.get("TESTING") else "memory://"

    limiter = Limiter(
        key_func=get_client_identifier,
        app=app,
        storage_uri=storage_uri,
        storage_options={"socket_connect_timeout": 2},
        default_limits=["200 per day", "60 per minute"],
        strategy="moving-window"
    )

    @app.errorhandler(429)
    def handle_rate_limit_exceeded(e):
        return jsonify({
            "error": "Rate limit exceeded. Please slow down and try again later.",
            "retry_after": getattr(e, "description", None)
        }), 429

    return limiter

