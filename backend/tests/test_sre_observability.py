import pytest
from backend.endpoints import app


def test_liveness_probe_returns_200(client):
    """
    Verifies that GET /health responds with HTTP 200 and valid JSON health payload.
    """
    res = client.get("/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "UP"
    assert "timestamp" in data
    assert "instance_id" in data
    assert "uptime_seconds" in data


def test_readiness_probe_returns_200(client):
    """
    Verifies that GET /ready validates dependencies (SQLite, Firebase, Redis).
    """
    res = client.get("/ready")
    assert res.status_code in [200, 503]
    data = res.get_json()
    assert "checks" in data
    assert "sqlite" in data["checks"]
    assert "firebase" in data["checks"]
    assert "redis" in data["checks"]


def test_prometheus_metrics_endpoint(client):
    """
    Verifies that GET /metrics exposes Prometheus formatted metrics.
    """
    # Trigger a request to ensure counters are populated
    client.get("/courses")

    res = client.get("/metrics")
    assert res.status_code == 200
    assert "text/plain" in res.content_type
    body = res.data.decode("utf-8")
    assert "http_requests_total" in body
    assert "http_request_duration_seconds" in body
    assert "http_requests_in_flight" in body
    assert "dependency_up" in body


def test_request_tracing_x_request_id_header(client):
    """
    Verifies that X-Request-ID correlation headers are propagated or generated on all responses.
    """
    # 1. Custom incoming request ID is propagated
    res_custom = client.get("/courses", headers={"X-Request-ID": "trace-custom-999"})
    assert res_custom.headers.get("X-Request-ID") == "trace-custom-999"

    # 2. When omitted, an ID is dynamically generated
    res_generated = client.get("/courses")
    assert res_generated.headers.get("X-Request-ID") is not None
    assert len(res_generated.headers.get("X-Request-ID")) > 10

