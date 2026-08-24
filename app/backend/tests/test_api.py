"""Testes de integração da API (blueprints + validação + stats)."""


def test_meta(client):
    r = client.get("/api/meta")
    assert r.status_code == 200
    assert r.get_json()["total_questions"] == 2


def test_meta_cache_preserva_filtros_repetidos(client):
    usp = client.get("/api/meta?institution=USP-SP")
    ambas = client.get("/api/meta?institution=USP-SP&institution=USP-RP")
    assert usp.get_json()["total_questions"] == 1
    assert ambas.get_json()["total_questions"] == 2


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
    # Coverage is catalog-driven and must expose the five canonical study areas,
    # including areas for which the current database has no questions yet.
    assert len(cov["areas"]) == 5
    assert {area["area"] for area in cov["areas"]} >= {"Clínica Médica", "Cirurgia", "Pediatria"}


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


def test_simulado_custom_rejeita_quantidade_invalida(client):
    r = client.post("/api/simulado/custom", json={"questions_per_area": "abc"})
    assert r.status_code == 400


def test_request_bodies_reject_unknown_fields(client):
    attempt = client.post(
        "/api/questions/1/attempt",
        json={"selected_letter": "B", "user_id": "another-user"},
    )
    assert attempt.status_code == 400

    simulado = client.post(
        "/api/simulado/custom",
        json={"questions_per_area": 10, "unexpected": True},
    )
    assert simulado.status_code == 400


def test_question_batch_validates_and_deduplicates_ids(client):
    invalid = client.post("/api/questions/batch", json={"ids": [1, -2]})
    assert invalid.status_code == 400

    response = client.post("/api/questions/batch", json={"ids": [1, 1]})
    assert response.status_code == 200
    assert [question["id"] for question in response.get_json()["questions"]] == [1]


def test_filters_status_new_e_unanswered(client):
    # Inicialmente ambas as 2 questões não foram respondidas
    r_unanswered = client.get("/api/questions?status=unanswered")
    r_new = client.get("/api/questions?status=new")
    assert len(r_unanswered.get_json()) == 2
    assert len(r_new.get_json()) == 2

    # Responde à questão 1
    client.post("/api/questions/1/attempt", json={"selected_letter": "B"})

    # Ambas as queries agora devem retornar apenas a questão 2 restante
    r_unanswered_after = client.get("/api/questions?status=unanswered")
    r_new_after = client.get("/api/questions?status=new")
    assert len(r_unanswered_after.get_json()) == 1
    assert r_unanswered_after.get_json()[0]["id"] == 2
    assert len(r_new_after.get_json()) == 1
    assert r_new_after.get_json()[0]["id"] == 2
