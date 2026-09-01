import json
import logging
import uuid


def test_request_correlation_and_security_headers(client):
    request_id = str(uuid.uuid4())
    response = client.get("/api/meta", headers={"X-Request-ID": request_id})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id
    assert response.headers["Server-Timing"].startswith("app;dur=")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"

    secure_response = client.get("/api/meta", base_url="https://medquest.test")
    assert secure_response.headers["Strict-Transport-Security"].startswith("max-age=31536000")


def test_wildcard_cors_configuration_is_rejected(client, monkeypatch):
    from api import create_app

    monkeypatch.setenv("FRONTEND_URL", "*")
    try:
        create_app(testing=True)
    except ValueError as exc:
        assert "wildcard CORS" in str(exc)
    else:
        raise AssertionError("wildcard CORS must fail closed")


def test_invalid_request_id_is_replaced(client):
    response = client.get("/api/meta", headers={"X-Request-ID": "spoofed"})
    assert str(uuid.UUID(response.headers["X-Request-ID"])) == response.headers["X-Request-ID"]


def test_web_vital_validation_and_snapshot(client):
    assert client.post("/api/logs/web-vital", json={"name": "LCP", "value": 1234, "rating": "good", "path": "/"}).status_code == 202
    assert client.post("/api/logs/web-vital", json={"name": "made-up", "value": 1}).status_code == 400
    snapshot = client.get("/api/metrics/performance").get_json()
    assert snapshot["routes"]
    assert any(route["route"] == "/api/logs/web-vital" for route in snapshot["routes"])


def test_frontend_error_ignores_client_user_and_query_string(client, caplog):
    with caplog.at_level(logging.ERROR, logger="medquest.telemetry"):
        response = client.post("/api/logs/error", json={
            "error": "boom",
            "url": "https://medquest.test/estudar?token=secret",
            "user_id": "attacker-controlled",
            "info": {"digest": "safe", "stack": "must not be logged"},
        })
    assert response.status_code == 200
    record = next(json.loads(item.message) for item in caplog.records if '"event":"frontend_error"' in item.message)
    assert record["path"] == "/estudar"
    serialized = json.dumps(record)
    assert "secret" not in serialized
    assert "attacker-controlled" not in serialized
    assert "must not be logged" not in serialized


def test_meta_cache_is_invalidated_after_attempt(client):
    assert client.get("/api/meta").get_json()["answered_questions"] == 0
    client.post("/api/questions/1/attempt", json={"selected_letter": "B"})
    assert client.get("/api/meta").get_json()["answered_questions"] == 1


def test_performance_indexes_cover_user_timeline_and_latest_attempt(client):
    with client.application.app_context():
        from api.db import get_db
        indexes = {row["name"] for row in get_db().execute("PRAGMA index_list(attempts)").fetchall()}
    assert "idx_attempts_user_question_latest" in indexes
    assert "idx_attempts_user_answered_at" in indexes


def test_domain_event_emission_and_p99_metric(client, caplog):
    from api.observability import record_domain_event

    with caplog.at_level(logging.INFO, logger="medquest.telemetry"):
        record_domain_event("study_attempt_completed", user_id="test_user", question_id=10, is_correct=True)
    
    record = next(json.loads(item.message) for item in caplog.records if '"event":"domain_event"' in item.message)
    assert record["event_name"] == "study_attempt_completed"
    assert record["user_id"] == "test_user"
    assert record["question_id"] == 10

    # Ensure performance snapshot has p99_ms and error_rate_pct
    snapshot = client.get("/api/metrics/performance").get_json()
    assert "routes" in snapshot
    for route in snapshot["routes"]:
        assert "p99_ms" in route
        assert "error_rate_pct" in route

