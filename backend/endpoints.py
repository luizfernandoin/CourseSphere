import os
from flask import Flask, request, jsonify
from flask_cors import CORS

try:
    from backend.query_manager import QueryManager
    from backend.firebase import Firebase
    from backend.main import hashFunction
    from backend.blueprints.courses import courses_bp
    from backend.security.auth import require_auth, get_current_uid
    from backend.security.rate_limit import init_rate_limiter
    from backend.security.validation import (
        validate_user_create_input,
        sanitize_profile_payload,
        validate_chat_messages_payload,
    )
    from backend.middleware.security_headers import register_security_headers
    from backend.utils.responses import success_response, error_response
except ImportError:
    from query_manager import QueryManager
    from firebase import Firebase
    from main import hashFunction
    from blueprints.courses import courses_bp
    from security.auth import require_auth, get_current_uid
    from security.rate_limit import init_rate_limiter
    from security.validation import (
        validate_user_create_input,
        sanitize_profile_payload,
        validate_chat_messages_payload,
    )
    from middleware.security_headers import register_security_headers
    from utils.responses import success_response, error_response

app = Flask(__name__)

# Enforce maximum body payload size (1MB) to protect against memory exhaustion / payload bombs
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024

# Register security headers middleware
register_security_headers(app)

# Initialize distributed rate limiter
limiter = init_rate_limiter(app)

# Configure restricted CORS policy
allowed_origins = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173"
).split(",")
CORS(app, origins=[origin.strip() for origin in allowed_origins if origin.strip()], supports_credentials=True)

# Register blueprints
app.register_blueprint(courses_bp)


# ============================================================================
# Centralized Error Handlers (Prevents stack trace and internal leakages)
# ============================================================================

@app.errorhandler(400)
def handle_bad_request(e):
    return error_response(getattr(e, "description", "Bad Request"), 400)


@app.errorhandler(401)
def handle_unauthorized(e):
    return error_response(getattr(e, "description", "Unauthorized"), 401)


@app.errorhandler(403)
def handle_forbidden(e):
    return error_response(getattr(e, "description", "Forbidden"), 403)


@app.errorhandler(404)
def handle_not_found(e):
    return error_response(getattr(e, "description", "Resource not found"), 404)


@app.errorhandler(405)
def handle_method_not_allowed(e):
    return error_response("Method not allowed", 405)


@app.errorhandler(413)
def handle_payload_too_large(e):
    return error_response("Payload exceeds maximum permitted size of 1MB", 413)


@app.errorhandler(500)
def handle_internal_error(e):
    return error_response("Internal server error", 500)


@app.errorhandler(Exception)
def handle_unhandled_exception(e):
    app.logger.error(f"Unhandled exception encountered: {type(e).__name__}")
    return error_response("An unexpected internal error occurred", 500)


# ============================================================================
# User Authentication and Profile Endpoints
# ============================================================================

@app.route("/users/create", methods=["POST"])
@limiter.limit("10 per minute")
def create_user():
    data = request.get_json(silent=True) or {}
    is_valid, err_msg = validate_user_create_input(data)
    if not is_valid:
        return error_response(err_msg, 400)

    email = data.get("email").strip()
    password = data.get("password")

    try:
        result = Firebase.create_user(email, password)
        return success_response(result, 201)
    except Exception as e:
        return error_response(f"Error creating user: {str(e)}", 400)


@app.route("/users/info", methods=["POST"])
@require_auth
def set_user_info():
    user_id = get_current_uid()
    data = request.get_json(silent=True) or {}
    sanitized_info = sanitize_profile_payload(data)

    try:
        Firebase.set_user_info(user_id, sanitized_info)
        return success_response({"message": "User info set successfully", "uid": user_id}, 200)
    except Exception:
        return error_response("Failed to update user profile", 500)


@app.route("/users/info", methods=["GET"])
@require_auth
def get_user_info():
    """
    Retrieves profile information for the authenticated user.
    Token must be provided via Authorization: Bearer <token> header.
    """
    user_id = get_current_uid()
    try:
        user_info = Firebase.get_user_info(user_id)
        return success_response(user_info, 200)
    except Exception:
        return error_response("Failed to retrieve user profile", 500)


@app.route("/users/query", methods=["POST"])
@require_auth
@limiter.limit("20 per minute")
def get_user_query():
    data = request.get_json(silent=True) or {}
    query = data.get("query")
    if not query or not isinstance(query, str) or len(query.strip()) == 0:
        return error_response("Query field is required and must be non-empty", 400)
    if len(query) > 2000:
        return error_response("Query exceeds maximum allowed length of 2000 characters", 400)

    user_id = get_current_uid()
    try:
        user_info = Firebase.get_user_info(user_id)
        response_data = QueryManager(query.strip(), user_info).response
        return success_response(response_data, 200)
    except Exception:
        return error_response("Failed to generate response for query", 500)


@app.route("/hash", methods=["POST"])
@require_auth
@limiter.limit("60 per minute")
def generate_message_id():
    data = request.get_json(silent=True)
    if not data:
        return error_response("Request payload is required", 400)
    try:
        message_id = hashFunction(data)
        return success_response({"messageID": message_id}, 200)
    except Exception:
        return error_response("Failed to generate message hash", 500)


# ============================================================================
# Chat Management Endpoints (Protected by Authorization and Resource Ownership)
# ============================================================================

@app.route("/chats/<chat_id>/messages", methods=["POST"])
@require_auth
def save_chat_messages(chat_id):
    user_id = get_current_uid()
    data = request.get_json(silent=True) or {}
    messages = data.get("messages")

    is_valid, err_msg = validate_chat_messages_payload(messages)
    if not is_valid:
        return error_response(err_msg, 400)

    try:
        Firebase.save_chat(user_id, chat_id, messages)
        return success_response({"message": "Messages saved successfully"}, 200)
    except Exception:
        return error_response("Failed to save chat messages", 500)


@app.route("/chats/<chat_id>", methods=["DELETE"])
@require_auth
def delete_chat(chat_id):
    """
    Deletes a chat session belonging to the authenticated user.
    Validates resource ownership and existence before deletion.
    """
    user_id = get_current_uid()
    try:
        chat = Firebase.get_chat(user_id, chat_id)
        if chat is None:
            return error_response("Chat not found", 404)
        Firebase.delete_chat(user_id, chat_id)
        return success_response({"message": "Message deleted successfully"}, 200)
    except Exception:
        return error_response("Failed to delete chat session", 500)


if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug_mode, host="0.0.0.0", port=5000)
