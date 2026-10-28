from flask import jsonify

def success_response(data, code=200):
    """Formats a standardized JSON success response."""
    return jsonify(data), code

def error_response(message, code=400):
    """Formats a standardized JSON error response."""
    return jsonify({"error": message}), code

