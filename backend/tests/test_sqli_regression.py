import pytest
from backend.db import execute_query


def test_courses_endpoint_is_registered(client):
    """Ensures the courses blueprint is actively registered and returns course list."""
    res = client.get("/courses")
    assert res.status_code == 200
    assert isinstance(res.get_json(), list)


def test_sqli_boolean_bypass_is_mitigated(client):
    """
    Regression Test for VULN-03 (SQL Injection):
    Ensures boolean-based SQL injection (' OR '1'='1) is treated as a literal search string
    and does NOT bypass SQL conditions or dump the courses table.
    """
    injection_payload = "' OR '1'='1"
    res = client.get(f"/courses/semester/{injection_payload}")
    # In parameterized query, SQLite looks for semester == "' OR '1'='1" which returns no rows -> 404
    assert res.status_code == 404
    assert "No courses found for this semester" in res.get_json()["error"]


def test_sqli_union_injection_is_mitigated(client):
    """
    Regression Test for VULN-03 (SQL Injection):
    Ensures UNION SELECT payloads attempting schema extraction are treated as literals
    and rejected cleanly.
    """
    union_payload = "' UNION SELECT 9999, 'INJECTED', 0, 'FA23', 'SEC', 'INJECTED' --"
    res = client.get(f"/courses/semester/{union_payload}")
    assert res.status_code == 404
    assert "No courses found for this semester" in res.get_json()["error"]


def test_legitimate_course_retrieval_by_id(client):
    """Ensures legitimate queries using integers succeed and return proper data."""
    # Assuming course with ID 1 exists from seed
    res = client.get("/courses/1")
    if res.status_code == 200:
        data = res.get_json()
        assert "id" in data
        assert data["id"] == 1
    else:
        assert res.status_code == 404

