def register_security_headers(app):
    """
    Registers an after_request hook that injects baseline OWASP recommended security headers
    into every HTTP response dispatched by the application.
    """
    @app.after_request
    def set_security_headers(response):
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking by disallowing framing
        response.headers["X-Frame-Options"] = "DENY"

        # Modern replacement for obsolete X-XSS-Protection header
        response.headers["X-XSS-Protection"] = "0"

        # Enforce strict referrer information leakage policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Enforce strict Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "connect-src 'self' http://localhost:* ws://localhost:*; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )

        # Restrict browser APIs and hardware features
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        return response

