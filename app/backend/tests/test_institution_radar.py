import pytest
from api.stats import calculate_wilson_ci, get_sample_status
from api.db import get_db


def test_calculate_wilson_ci_math():
    # n = 0
    lower, upper = calculate_wilson_ci(0, 0)
    assert lower is None
    assert upper is None

    # n = 10, k = 8 (80% acurácia, amostra pequena com incerteza ampla)
    lower, upper = calculate_wilson_ci(8, 10)
    assert lower is not None and upper is not None
    assert 0.45 < lower < 0.55
    assert 0.90 < upper < 0.98
    assert lower < 0.8 < upper

    # n = 100, k = 80 (80% acurácia, amostra maior e intervalo mais estreito)
    lower_100, upper_100 = calculate_wilson_ci(80, 100)
    assert lower_100 is not None and upper_100 is not None
    assert 0.70 < lower_100 < 0.75
    assert 0.85 < upper_100 < 0.90
    assert (upper_100 - lower_100) < (upper - lower)

    # Edge cases (k = 0 e k = n)
    lower_0, upper_0 = calculate_wilson_ci(0, 20)
    assert lower_0 == 0.0
    assert 0.0 < upper_0 < 0.20

    lower_n, upper_n = calculate_wilson_ci(20, 20)
    assert 0.80 < lower_n < 1.0
    assert upper_n == 1.0


def test_get_sample_status():
    assert get_sample_status(0) == "insufficient"
    assert get_sample_status(19) == "insufficient"
    assert get_sample_status(20) == "forming"
    assert get_sample_status(49) == "forming"
    assert get_sample_status(50) == "reliable"
    assert get_sample_status(150) == "reliable"


def test_institution_radar_endpoint_user_isolation(app, client):
    with app.app_context():
        db = get_db()
        # Setup test questions
        db.execute("""
            INSERT OR IGNORE INTO questions (id, source_file, source_number, year, institution_code, institution_label, topic, area, subtema, missing_alts)
            VALUES 
            (7001, 'test.pdf', 1, 2026, 'USP-SP', 'USP São Paulo', 'Cardio', 'Clínica Médica', 'Cardiologia', 0),
            (7002, 'test.pdf', 2, 2026, 'USP-SP', 'USP São Paulo', 'Trauma', 'Cirurgia', 'Trauma Abdominal', 0),
            (7003, 'test.pdf', 3, 2026, 'UNICAMP', 'Unicamp', 'Parto', 'Ginecologia e Obstetrícia', 'Trabalho de Parto', 0)
        """)
        # User A answers 7001 correctly and 7002 incorrectly
        db.execute("""
            INSERT INTO attempts (user_id, question_id, is_correct, selected_letter, answered_at)
            VALUES 
            ('user_alpha', 7001, 1, 'A', '2026-09-01T12:00:00Z'),
            ('user_alpha', 7002, 0, 'B', '2026-09-01T12:01:00Z')
        """)
        db.commit()

    # Request for user_alpha
    headers_alpha = {"X-Guest-ID": "user_alpha"}
    res_alpha = client.get("/api/stats/institution-radar?institution=USP-SP", headers=headers_alpha)
    assert res_alpha.status_code == 200
    data_alpha = res_alpha.get_json()

    assert data_alpha["institution"]["code"] == "USP-SP"
    assert data_alpha["institution"]["total_attempts"] == 2
    assert data_alpha["institution"]["total_correct"] == 1
    assert data_alpha["institution"]["accuracy"] == 0.5
    assert data_alpha["institution"]["sample_status"] == "insufficient"

    # Request for user_beta (must have 0 attempts, perfectly isolated)
    headers_beta = {"X-Guest-ID": "user_beta"}
    res_beta = client.get("/api/stats/institution-radar?institution=USP-SP", headers=headers_beta)
    assert res_beta.status_code == 200
    data_beta = res_beta.get_json()

    assert data_beta["institution"]["total_attempts"] == 0
    assert data_beta["institution"]["total_correct"] == 0
    assert data_beta["institution"]["accuracy"] is None
    assert data_beta["institution"]["sample_status"] == "insufficient"


def test_institution_radar_comparison_and_actions(app, client):
    with app.app_context():
        db = get_db()
        # Setup questions
        db.execute("""
            INSERT OR IGNORE INTO questions (id, source_file, source_number, year, institution_code, institution_label, topic, area, subtema, missing_alts)
            VALUES 
            (8001, 'test.pdf', 1, 2026, 'USP-SP', 'USP São Paulo', 'Cardio', 'Clínica Médica', 'Cardiologia', 0),
            (8002, 'test.pdf', 2, 2026, 'UNICAMP', 'Unicamp', 'Cardio', 'Clínica Médica', 'Cardiologia', 0)
        """)
        # Insert 25 attempts for user_radar on 8001 (forming sample)
        for i in range(25):
            db.execute("""
                INSERT INTO attempts (user_id, question_id, is_correct, selected_letter, answered_at)
                VALUES ('user_radar', 8001, 1, 'A', '2026-09-01T12:00:00Z')
            """)
        db.commit()

    headers = {"X-Guest-ID": "user_radar"}
    res = client.get("/api/stats/institution-radar?institution=USP-SP&compare_institution=UNICAMP", headers=headers)
    assert res.status_code == 200
    data = res.get_json()

    # Primary institution: USP-SP
    inst = data["institution"]
    assert inst["code"] == "USP-SP"
    assert inst["total_attempts"] == 25
    assert inst["total_correct"] == 25
    assert inst["accuracy"] == 1.0
    assert inst["sample_status"] == "forming"
    assert inst["ci_lower"] is not None and inst["ci_lower"] > 0.80

    # Verification of canonical areas
    areas = {a["area"]: a for a in inst["areas"]}
    assert "Clínica Médica" in areas
    assert "Cirurgia" in areas
    assert "Ginecologia e Obstetrícia" in areas
    assert "Pediatria" in areas
    assert "Medicina Preventiva" in areas

    clinica = areas["Clínica Médica"]
    assert clinica["attempts"] == 25
    assert clinica["accuracy"] == 1.0
    assert clinica["sample_status"] == "forming"
    assert len(clinica["priority_topics"]) > 0

    cardio_topic = next((t for t in clinica["priority_topics"] if t["subtema"] == "Cardiologia"), None)
    assert cardio_topic is not None
    assert "/estudar?" in cardio_topic["study_url"]
    assert "institution=USP-SP" in cardio_topic["study_url"]
    assert "/simulado?" in cardio_topic["simulado_url"]
    assert "institutions=USP-SP" in cardio_topic["simulado_url"]
    assert "/revisao-ativa" == cardio_topic["review_url"]


    # Comparison institution: UNICAMP
    comp = data["comparison"]
    assert comp["type"] == "institution"
    assert comp["code"] == "UNICAMP"
    assert comp["total_attempts"] == 0
    assert comp["sample_status"] == "insufficient"


def test_institution_radar_viewed_telemetry_is_private(app, client, monkeypatch):
    emitted_events = []

    def mock_emit(event, **fields):
        emitted_events.append((event, fields))

    monkeypatch.setattr("api.stats.emit", mock_emit)

    headers = {"X-Guest-ID": "user_telemetry"}
    res = client.get("/api/stats/institution-radar?institution=USP-SP&compare_institution=UNICAMP", headers=headers)
    assert res.status_code == 200

    # Confirma que institution_radar_viewed foi emitido
    radar_events = [e for e in emitted_events if e[0] == "institution_radar_viewed"]
    assert len(radar_events) == 1

    event_name, payload = radar_events[0]
    assert payload["has_comparator"] is True
    assert payload["sample_status"] in {"insufficient", "forming", "reliable"}

    # Garante estritamente que nenhum dado sensível foi logado
    forbidden_keys = {
        "institution", "institution_code", "institution_label", "topic", "subtema",
        "accuracy", "score", "question", "question_id", "url", "study_url", "simulado_url"
    }
    for k in payload:
        assert k not in forbidden_keys, f"Chave sensível encontrada no payload de telemetria: {k}"


def test_institution_radar_action_endpoint(app, client, monkeypatch):
    emitted_events = []

    def mock_emit(event, **fields):
        emitted_events.append((event, fields))

    monkeypatch.setattr("api.stats.emit", mock_emit)

    headers = {"X-Guest-ID": "user_actions"}

    # 1. Ações válidas
    for action in ["study", "simulado", "review"]:
        res = client.post(
            "/api/stats/institution-radar/action",
            json={"action": action},
            headers=headers,
        )
        assert res.status_code == 200
        assert res.get_json() == {"success": True}

    action_events = [e for e in emitted_events if e[0] == "institution_radar_action_clicked"]
    assert len(action_events) == 3
    assert [e[1]["action"] for e in action_events] == ["study", "simulado", "review"]

    # 2. Ação inválida por enum
    res_inv = client.post(
        "/api/stats/institution-radar/action",
        json={"action": "invalid_action"},
        headers=headers,
    )
    assert res_inv.status_code == 400
    assert "Invalid action" in res_inv.get_json()["error"]

    # 3. Payload malformado
    res_empty = client.post(
        "/api/stats/institution-radar/action",
        data="not a json",
        content_type="text/plain",
        headers=headers,
    )
    assert res_empty.status_code == 400

