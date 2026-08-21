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
