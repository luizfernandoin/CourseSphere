import re

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

ALLOWED_PROFILE_FIELDS = {"majors", "minors", "courses", "college", "year", "about"}


def validate_user_create_input(data: dict):
    """
    Validates input schema and credentials strength for user creation.
    Returns (True, None) if valid, or (False, error_message) if invalid.
    """
    if not isinstance(data, dict):
        return False, "Request body must be a JSON object"

    email = data.get("email")
    password = data.get("password")

    if not email or not isinstance(email, str) or not EMAIL_REGEX.match(email.strip()):
        return False, "A valid email address is required"

    if not password or not isinstance(password, str) or len(password) < 8:
        return False, "Password must be a string with at least 8 characters"

    return True, None


def sanitize_profile_payload(data: dict):
    """
    Sanitizes profile payload by retaining strictly allowed fields,
    preventing mass-assignment and arbitrary property injection.
    """
    if not isinstance(data, dict):
        return {}

    sanitized = {}
    for field in ALLOWED_PROFILE_FIELDS:
        if field in data:
            val = data[field]
            # Ensure strings and lists are within bounded sizes
            if isinstance(val, str):
                sanitized[field] = val[:1000].strip()
            elif isinstance(val, list):
                sanitized[field] = [str(item)[:100].strip() for item in val[:50]]
            elif isinstance(val, (int, float, bool)):
                sanitized[field] = val
            elif val is None:
                sanitized[field] = None
    return sanitized


def validate_chat_messages_payload(messages):
    """
    Validates that messages is a list of well-structured dictionary objects
    with bounded text length.
    """
    if not isinstance(messages, list) or len(messages) == 0:
        return False, "Field 'messages' must be a non-empty array"

    if len(messages) > 100:
        return False, "Cannot submit more than 100 messages at once"

    for idx, msg in enumerate(messages):
        if not isinstance(msg, dict):
            return False, f"Message at index {idx} must be a JSON object"
        sender = msg.get("sender")
        text = msg.get("text")
        if not sender or not isinstance(sender, str):
            return False, f"Message at index {idx} must contain a valid string 'sender'"
        if not text or not isinstance(text, str):
            return False, f"Message at index {idx} must contain a valid string 'text'"
        if len(text) > 4000:
            return False, f"Message at index {idx} text exceeds maximum length of 4000 characters"

    return True, None

