import os
import time
from datetime import datetime, timezone
from flask import Blueprint, Response, jsonify, request
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
    REGISTRY
)

try:
    from backend.db import execute_query
    from backend.firebase import firebase_app
except ImportError:
    from db import execute_query
    from firebase import firebase_app

monitoring_bp = Blueprint("monitoring", __name__)

INSTANCE_ID = os.environ.get("INSTANCE_ID", "backend-standalone")
START_TIME = time.time()

# Prometheus Metrics Definitions
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total number of HTTP requests processed",
    ["method", "endpoint", "status"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request execution latency in seconds",
    ["method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

HTTP_REQUESTS_IN_FLIGHT = Gauge(
    "http_requests_in_flight",
    "Current number of HTTP requests being processed concurrently"
)

DEPENDENCY_HEALTH = Gauge(
    "dependency_up",
    "Operational status of external and storage dependencies (1 = UP, 0 = DOWN)",
    ["dependency"]
)


def track_metrics(app):
    """Hooks into request lifecycle to collect Prometheus metrics."""
    @app.before_request
    def before_request_metrics():
        HTTP_REQUESTS_IN_FLIGHT.inc()
        request._prom_start_time = time.time()

    @app.after_request
    def after_request_metrics(response):
        HTTP_REQUESTS_IN_FLIGHT.dec()
        start = getattr(request, "_prom_start_time", None)
        if start:
            duration = time.time() - start
            endpoint = request.url_rule.rule if request.url_rule else request.path
            HTTP_REQUESTS_TOTAL.labels(
                method=request.method,
                endpoint=endpoint,
                status=str(response.status_code)
            ).inc()
            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=request.method,
                endpoint=endpoint
            ).observe(duration)
        return response


@monitoring_bp.route("/health", methods=["GET"])
def liveness_probe():
    """
    Liveness probe: verifies that the web server process is alive and responding.
    Used by orchestrators (Docker/K8s) to determine container health.
    """
    return jsonify({
        "status": "UP",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "instance_id": INSTANCE_ID,
        "uptime_seconds": round(time.time() - START_TIME, 2)
    }), 200


@monitoring_bp.route("/ready", methods=["GET"])
def readiness_probe():
    """
    Readiness probe: validates connectivity to required dependencies
    (SQLite database, Firebase Admin SDK, and Redis).
    Returns HTTP 200 when ready to accept traffic, or HTTP 503 if any dependency fails.
    """
    checks = {}
    is_ready = True

    # 1. SQLite connectivity check
    try:
        execute_query("SELECT 1")
        checks["sqlite"] = "UP"
        DEPENDENCY_HEALTH.labels(dependency="sqlite").set(1)
    except Exception as e:
        checks["sqlite"] = f"DOWN: {str(e)}"
        DEPENDENCY_HEALTH.labels(dependency="sqlite").set(0)
        is_ready = False

    # 2. Firebase Admin SDK initialized check
    try:
        if firebase_app is not None:
            checks["firebase"] = "UP"
            DEPENDENCY_HEALTH.labels(dependency="firebase").set(1)
        else:
            checks["firebase"] = "DOWN: App uninitialized"
            DEPENDENCY_HEALTH.labels(dependency="firebase").set(0)
            is_ready = False
    except Exception as e:
        checks["firebase"] = f"DOWN: {str(e)}"
        DEPENDENCY_HEALTH.labels(dependency="firebase").set(0)
        is_ready = False

    # 3. Redis connectivity check
    try:
        redis_url = os.environ.get("REDIS_URL")
        if redis_url and redis_url != "memory://":
            import redis
            r = redis.from_url(redis_url, socket_timeout=1)
            r.ping()
            checks["redis"] = "UP"
            DEPENDENCY_HEALTH.labels(dependency="redis").set(1)
        else:
            checks["redis"] = "SKIPPED: in-memory mode"
            DEPENDENCY_HEALTH.labels(dependency="redis").set(1)
    except Exception as e:
        checks["redis"] = f"DOWN: {str(e)}"
        DEPENDENCY_HEALTH.labels(dependency="redis").set(0)
        is_ready = False

    status_code = 200 if is_ready else 503
    return jsonify({
        "status": "READY" if is_ready else "NOT_READY",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "instance_id": INSTANCE_ID,
        "checks": checks
    }), status_code


@monitoring_bp.route("/metrics", methods=["GET"])
def prometheus_metrics():
    """
    Prometheus metrics exposition endpoint.
    Returns plain text metrics following the OpenMetrics / Prometheus standard format.
    """
    return Response(generate_latest(REGISTRY), mimetype=CONTENT_TYPE_LATEST)

