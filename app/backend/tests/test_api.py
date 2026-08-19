"""Testes de integração da API (blueprints + validação + stats)."""


def test_meta(client):
    r = client.get("/api/meta")
    assert r.status_code == 200
    assert r.get_json()["total_questions"] == 2


def test_v1_alias(client):
    assert client.get("/api/v1/meta").status_code == 200


def test_attempt_correto(client):
    r = client.post("/api/questions/1/attempt",
                    json={"selected_letter": "B", "confidence": "certeza", "time_spent_ms": 12000})
    assert r.status_code == 200
    body = r.get_json()
    assert body["is_correct"] is True
    assert body["next_review_date"]
    assert body["explanation"] == "explicação da 1"


def test_attempt_errado(client):
    r = client.post("/api/questions/2/attempt", json={"selected_letter": "B"})  # correto é A
    assert r.get_json()["is_correct"] is False


def test_validacao_letra_invalida(client):
    r = client.post("/api/questions/1/attempt", json={"selected_letter": "Z"})
    assert r.status_code == 400


def test_overview_conta_tentativa(client):
    client.post("/api/questions/1/attempt", json={"selected_letter": "B"})
    ov = client.get("/api/stats/overview").get_json()
    assert ov["total_questions"] == 2
    assert ov["distinct_answered"] == 1
    assert ov["accuracy_latest_attempt"] == 1.0


def test_coverage(client):
    cov = client.get("/api/coverage").get_json()
    assert len(cov["areas"]) == 2


def test_planner_config_roundtrip(client):
    assert client.post("/api/planner/config",
                       json={"exam_date": "2026-11-15", "days_per_week": 6, "hours_per_day": 5}).status_code == 200
    cfg = client.get("/api/planner/config").get_json()
    assert cfg["hours_per_day"] == 5


def test_planner_config_validacao(client):
    r = client.post("/api/planner/config", json={"days_per_week": 99})  # > 7
    assert r.status_code == 400


def test_questions_limit_invalido_usa_padrao(client):
    r = client.get("/api/questions?limit=nao-e-numero")
    assert r.status_code == 200
    assert len(r.get_json()) == 2


def test_questions_limit_negativo_nao_fura_limite(client):
    r = client.get("/api/questions?limit=-1")
    assert r.status_code == 200
    assert len(r.get_json()) == 1


def test_review_rejeita_confianca_invalida(client):
    client.post("/api/questions/1/attempt", json={"selected_letter": "B"})
    r = client.post("/api/questions/1/review", json={"confidence": "qualquer-coisa"})
    assert r.status_code == 400


def test_weak_topics_aceita_min_attempts_invalido(client):
    r = client.get("/api/stats/weak-topics?min_attempts=abc")
    assert r.status_code == 200
