import os
import time
import json
import uuid
import logging
from datetime import datetime, timezone
from flask import request, g

INSTANCE_ID = os.environ.get("INSTANCE_ID", "backend-standalone")


def get_request_id():
    """Returns the current request's unique correlation ID."""
    return getattr(g, "request_id", None)


def register_structured_logging(app):
    """
    Registers request hooks to inject unique correlation IDs (X-Request-ID)
    and emit structured JSON access logs with performance metrics.
    """
    # Configure root logger with custom JSON format
    logger = logging.getLogger("coursesphere")
    logger.setLevel(logging.INFO)

    @app.before_request
    def before_request_logging():
        # Correlation ID from upstream proxy or generated locally
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        g.request_id = req_id
        g.request_start_time = time.time()

    @app.after_request
    def after_request_logging(response):
        # Attach correlation ID and instance ID to response headers
        req_id = getattr(g, "request_id", None)
        if req_id:
            response.headers["X-Request-ID"] = req_id
        response.headers["X-Instance-ID"] = INSTANCE_ID

        # Calculate response latency in milliseconds
        start_time = getattr(g, "request_start_time", None)
        latency_ms = round((time.time() - start_time) * 1000, 2) if start_time else 0.0

        # Avoid polluting logs with repetitive internal health probes if requested
        if request.path in ["/health", "/ready"] and response.status_code == 200:
            level = "DEBUG"
        elif response.status_code >= 500:
            level = "ERROR"
        elif response.status_code >= 400:
            level = "WARNING"
        else:
            level = "INFO"

        client_ip = (
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            or request.remote_addr
            or "unknown"
        )

        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "request_id": req_id,
            "instance_id": INSTANCE_ID,
            "method": request.method,
            "path": request.path,
            "status_code": response.status_code,
            "latency_ms": latency_ms,
            "client_ip": client_ip,
            "uid": getattr(g, "uid", None),
            "user_agent": request.headers.get("User-Agent", "unknown")[:200]
        }

        print(json.dumps(log_record), flush=True)
        return response

