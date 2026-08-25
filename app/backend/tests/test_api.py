"""Testes de integração da API (blueprints + validação + stats)."""


def test_meta(client):
    r = client.get("/api/meta")
    assert r.status_code == 200
    assert r.get_json()["total_questions"] == 3


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
    assert ov["total_questions"] == 3
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
    assert len(r.get_json()) == 3


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
    # Inicialmente as 3 questões não foram respondidas
    r_unanswered = client.get("/api/questions?status=unanswered")
    r_new = client.get("/api/questions?status=new")
    assert len(r_unanswered.get_json()) == 3
    assert len(r_new.get_json()) == 3

    # Responde à questão 1
    client.post("/api/questions/1/attempt", json={"selected_letter": "B"})

    # Ambas as queries agora devem retornar as questões restantes (2 e 3)
    r_unanswered_after = client.get("/api/questions?status=unanswered")
    r_new_after = client.get("/api/questions?status=new")
    assert len(r_unanswered_after.get_json()) == 2
    assert len(r_new_after.get_json()) == 2


def test_discursive_question_detail_and_self_assessment(client):
    # 1. Verifica flag is_discursive
    res_q1 = client.get("/api/questions/1")
    assert res_q1.status_code == 200
    assert res_q1.get_json()["is_discursive"] is False

    res_q3 = client.get("/api/questions/3")
    assert res_q3.status_code == 200
    assert res_q3.get_json()["is_discursive"] is True

    # 2. Revela resposta discursiva com defer -> is_correct deve vir None para autoavaliação
    attempt = client.post(
        "/api/questions/3/attempt",
        json={"selected_letter": "A", "confidence": "defer", "user_answer_text": "Raquitismo por falta de vit D"}
    )
    assert attempt.status_code == 200
    data = attempt.get_json()
    assert data["is_discursive"] is True
    assert data["is_correct"] is None
    assert data["explanation"] is not None

    # 3. Autoavaliação de erro (Errei)
    review = client.post(
        "/api/questions/3/review",
        json={"confidence": "duvida", "is_correct": False}
    )
    assert review.status_code == 200
    review_data = review.get_json()
    assert review_data["success"] is True
    assert review_data["is_correct"] is False
    assert review_data["next_review_date"] is not None

    # 4. Autoavaliação de acerto explícito em novo attempt
    attempt2 = client.post(
        "/api/questions/3/attempt",
        json={"selected_letter": "A", "confidence": "certeza", "is_correct": True}
    )
    assert attempt2.status_code == 200
    assert attempt2.get_json()["is_correct"] is True
