import pytest
from api.edital_profiles import (
    get_edital_profile,
    normalize_weights,
    EditalProfile,
    CANONICAL_AREAS,
)
from api.stats import calculate_bayesian_readiness, beta_credible_interval
from api.db import get_db


def test_normalize_weights_valid_and_invalid():
    # 1. Pesos válidos com soma 1.0
    valid_w = {a: 0.20 for a in CANONICAL_AREAS}
    norm_w = normalize_weights(valid_w)
    assert sum(norm_w.values()) == pytest.approx(1.0, 0.001)
    assert all(norm_w[a] == 0.20 for a in CANONICAL_AREAS)

    # 2. Pesos desnormalizados (soma = 10)
    unnorm_w = {a: 2.0 for a in CANONICAL_AREAS}
    norm_w2 = normalize_weights(unnorm_w)
    assert sum(norm_w2.values()) == pytest.approx(1.0, 0.001)
    assert all(norm_w2[a] == 0.20 for a in CANONICAL_AREAS)

    # 3. Pesos vazios ou inválidos (deve fazer fallback equitativo)
    fallback_w = normalize_weights({})
    assert sum(fallback_w.values()) == pytest.approx(1.0, 0.001)
    assert all(fallback_w[a] == 0.20 for a in CANONICAL_AREAS)


def test_edital_profiles_registry_and_fallback():
    # Perfis locais permanecem experimentais até haver fonte documental validada.
    usp = get_edital_profile("USP-SP")
    assert usp.status == "experimental"
    assert usp.version == "2025.1"
    assert len(usp.weights) == 5

    unicamp = get_edital_profile("UNICAMP")
    assert unicamp.status == "experimental"
    assert unicamp.institution_code == "UNICAMP"

    # Experimental fallback for unknown institution
    custom = get_edital_profile("HOSPITAL_UNKNOWN")
    assert custom.status == "experimental"
    assert custom.institution_code == "HOSPITAL_UNKNOWN"
    assert sum(custom.weights.values()) == pytest.approx(1.0, 0.001)


def test_beta_credible_interval_is_exact_at_small_and_extreme_posteriors():
    # Beta(1, 1) é uniforme; seu intervalo central de 95% é exatamente [2,5%, 97,5%].
    assert beta_credible_interval(1, 1) == pytest.approx((0.025, 0.975), abs=0.0001)

    # A posterior para 20/20 não pode usar uma normal simétrica que extrapola 100%.
    lower, upper = beta_credible_interval(21, 1)
    assert 0.80 < lower < 0.99
    assert 0.99 < upper < 1.0


def test_bayesian_readiness_math_edge_cases():
    profile = get_edital_profile("USP-SP")

    # 1. Zero tentativas em todas as áreas
    empty_records = []
    res_empty = calculate_bayesian_readiness(empty_records, profile)
    # Com prior Beta(1,1), média de cada área é (0+1)/(0+2) = 0.5
    assert res_empty["readiness_score"] == pytest.approx(0.5, 0.01)
    assert res_empty["evidence_status"] == "insufficient"
    assert res_empty["ci_lower"] < 0.5 < res_empty["ci_upper"]
    assert 0.0 <= res_empty["ci_lower"] <= 1.0
    assert 0.0 <= res_empty["ci_upper"] <= 1.0

    # 2. 0% de acerto em amostra de 20 tentativas por área
    records_0_pct = [
        {"area": a, "attempts": 20, "correct": 0, "available": 50, "answered": 20}
        for a in CANONICAL_AREAS
    ]
    res_0 = calculate_bayesian_readiness(records_0_pct, profile)
    # Posterior individual: (0 + 1) / (20 + 2) = 1/22 ≈ 0.0455
    assert res_0["readiness_score"] == pytest.approx(1 / 22, 0.01)
    assert res_0["ci_lower"] >= 0.0
    assert res_0["evidence_status"] == "reliable"

    # 3. 100% de acerto em amostra de 20 tentativas por área
    records_100_pct = [
        {"area": a, "attempts": 20, "correct": 20, "available": 50, "answered": 20}
        for a in CANONICAL_AREAS
    ]
    res_100 = calculate_bayesian_readiness(records_100_pct, profile)
    # Posterior individual: (20 + 1) / (20 + 2) = 21/22 ≈ 0.9545
    assert res_100["readiness_score"] == pytest.approx(21 / 22, 0.01)
    assert res_100["ci_upper"] <= 1.0
    assert res_100["evidence_status"] == "reliable"


def test_bayesian_readiness_evidence_status_thresholds():
    profile = get_edital_profile("USP-SP")

    # Insuficiente por total < 20
    rec_insuf = [
        {"area": "Clínica Médica", "attempts": 10, "correct": 8, "available": 50, "answered": 10},
    ]
    assert calculate_bayesian_readiness(rec_insuf, profile)["evidence_status"] == "insufficient"

    # Insuficiente por área ponderada com < 5 tentativas
    rec_uneven = [
        {"area": "Clínica Médica", "attempts": 50, "correct": 40, "available": 50, "answered": 50},
        {"area": "Cirurgia", "attempts": 2, "correct": 1, "available": 50, "answered": 2},
    ]
    assert calculate_bayesian_readiness(rec_uneven, profile)["evidence_status"] == "insufficient"

    # Em formação: total >= 20 e todas as áreas com >= 5 tentativas
    rec_forming = [
        {"area": a, "attempts": 6, "correct": 4, "available": 50, "answered": 6}
        for a in CANONICAL_AREAS
    ]
    assert calculate_bayesian_readiness(rec_forming, profile)["evidence_status"] == "forming"

    # Confiável: total >= 50 e todas as áreas com >= 10 tentativas
    rec_reliable = [
        {"area": a, "attempts": 12, "correct": 9, "available": 50, "answered": 12}
        for a in CANONICAL_AREAS
    ]
    assert calculate_bayesian_readiness(rec_reliable, profile)["evidence_status"] == "reliable"


def test_exam_readiness_endpoint_integration_and_isolation(app, client):
    with app.app_context():
        db = get_db()
        # Setup questions
        db.execute("""
            INSERT OR IGNORE INTO questions (id, source_file, source_number, year, institution_code, institution_label, topic, area, subtema, missing_alts)
            VALUES 
            (9001, 'test.pdf', 1, 2026, 'USP-SP', 'USP São Paulo', 'Cardio', 'Clínica Médica', 'Cardiologia', 0),
            (9002, 'test.pdf', 2, 2026, 'USP-SP', 'USP São Paulo', 'Trauma', 'Cirurgia', 'Trauma Abdominal', 0)
        """)
        # User Alpha attempts
        db.execute("""
            INSERT INTO attempts (user_id, question_id, is_correct, selected_letter, answered_at)
            VALUES 
            ('user_bayes_a', 9001, 1, 'A', '2026-09-01T12:00:00Z'),
            ('user_bayes_a', 9002, 1, 'A', '2026-09-01T12:01:00Z')
        """)
        db.commit()

    # Request for user_bayes_a
    headers_a = {"X-Guest-ID": "user_bayes_a"}
    res_a = client.get("/api/stats/exam-readiness?institution=USP-SP", headers=headers_a)
    assert res_a.status_code == 200
    data_a = res_a.get_json()

    assert data_a["institution"] == "USP-SP"
    assert data_a["answered"] == 2
    assert data_a["evidence_status"] == "insufficient"
    assert "readiness_score" in data_a
    assert "ci_lower" in data_a and "ci_upper" in data_a
    assert data_a["edital_profile"]["version"] == "2025.1"
    assert len(data_a["key_factors"]) > 0
    assert len(data_a["limitations"]) > 0

    # Request for user_bayes_b (isolated)
    headers_b = {"X-Guest-ID": "user_bayes_b"}
    res_b = client.get("/api/stats/exam-readiness?institution=USP-SP", headers=headers_b)
    assert res_b.status_code == 200
    data_b = res_b.get_json()

    assert data_b["answered"] == 0
    assert sum(a["attempts"] for a in data_b["areas"]) == 0
    assert data_b["evidence_status"] == "insufficient"


def test_exam_readiness_viewed_telemetry_is_private(app, client, monkeypatch):
    emitted_events = []

    def mock_emit(event, **fields):
        emitted_events.append((event, fields))

    monkeypatch.setattr("api.stats.emit", mock_emit)

    headers = {"X-Guest-ID": "user_telemetry_bayes"}
    res = client.get("/api/stats/exam-readiness?institution=USP-SP", headers=headers)
    assert res.status_code == 200

    readiness_events = [e for e in emitted_events if e[0] == "exam_readiness_viewed"]
    assert len(readiness_events) == 1

    event_name, payload = readiness_events[0]
    assert payload["profile_status"] in {"validated", "experimental"}
    assert payload["evidence_status"] in {"insufficient", "forming", "reliable"}

    # Garante estritamente que nenhum dado sensível foi logado
    forbidden_keys = {
        "institution", "institution_code", "institution_label", "topic", "subtema",
        "accuracy", "readiness_score", "score", "question", "question_id", "url"
    }
    for k in payload:
        assert k not in forbidden_keys, f"Chave sensível encontrada no payload de telemetria: {k}"
