import json

from api.adaptive import fsrs_metrics, topic_priority
from api.srs import review


def test_fsrs_metrics_are_real_and_corrupt_state_is_safe():
    card_json, _ = review(None, True, "duvida")
    metrics = fsrs_metrics(card_json)
    assert 0 <= metrics["retrievability"] <= 1
    assert metrics["stability"] > 0
    assert fsrs_metrics("not-json")["retrievability"] is None


def test_topic_priority_uses_evidence_memory_and_coverage():
    weak, confidence = topic_priority(10, 2, retrievability=0.5, coverage=0.1)
    strong, _ = topic_priority(10, 9, retrievability=0.95, coverage=0.8)
    assert confidence > 0.8
    assert weak > strong


def test_learning_profile_exposes_goal_and_transparent_method(client):
    response = client.get("/api/stats/learning-profile")
    assert response.status_code == 200
    body = response.get_json()
    assert body["goal"]["configured_daily_questions"] == 30
    assert body["method"]["deterministic"] is True
    assert body["topics"]
    assert "priority_score" in body["topics"][0]


def test_adaptive_queue_is_deterministic_and_prioritizes_recent_error(client):
    attempt = client.post(
        "/api/questions/1/attempt",
        json={"selected_letter": "A", "confidence": "certeza", "time_spent_ms": 1000},
    )
    assert attempt.status_code == 200
    first = client.get("/api/questions?mode=adaptive&limit=2").get_json()
    second = client.get("/api/questions?mode=adaptive&limit=2").get_json()
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    assert first[0]["id"] == 1
    assert "latest_attempt_wrong" in first[0]["adaptive_reasons"]
