"""Testes de curadoria e reclassificação de questões restritas por permissão."""
from flask import g


def test_get_taxonomy(client):
    r = client.get("/api/taxonomy")
    assert r.status_code == 200
    data = r.get_json()
    assert isinstance(data, dict)
    assert len(data) >= 5
    assert "Cirurgia" in data
    assert "Clínica Médica" in data


def test_curator_reclassification_success(client):
    payload = {
        "area": "Clínica Médica",
        "subtema": "Geriatria: Avaliação Ampla do Idoso, Síndromes Demenciais e Quedas",
        "topic": "Quedas no Idoso"
    }
    r = client.patch("/api/questions/1/classification", json=payload)
    assert r.status_code == 200
    res = r.get_json()
    assert res["success"] is True
    assert res["question"]["subtema"] == "Geriatria: Avaliação Ampla do Idoso, Síndromes Demenciais e Quedas"
    assert res["question"]["area"] == "Clínica Médica"


def test_curator_reclassification_validation(client):
    r = client.patch("/api/questions/1/classification", json={"area": ""})
    assert r.status_code == 400

    r = client.patch("/api/questions/999999/classification", json={
        "area": "Cirurgia",
        "subtema": "Trauma Torácico: Pneumotórax, Hemotórax e Tamponamento Cardíaco"
    })
    assert r.status_code == 404


def test_non_curator_forbidden(client):
    # Simulate a request from a non-curator user
    from flask import g
    from api.auth import require_curator

    @require_curator
    def dummy():
        return "ok"

    from flask import Flask
    app = Flask("test_auth_check")
    app.config["TESTING"] = False  # Disable testing bypass
    with app.test_request_context(headers={"X-User-Email": "other@user.com"}):
        g.user_email = "other@user.com"
        res = dummy()
        assert res[1] == 403

