import pytest


def test_stats_benchmark(client):
    # Antes de tentativas
    r = client.get("/api/stats/benchmark")
    assert r.status_code == 200
    data = r.get_json()
    assert "accuracy_overall" in data
    assert "target_score_pct" in data
    assert "status_label" in data
    assert "weekly_progress_pct" in data

    # Registrar tentativa
    client.post("/api/questions/1/attempt", json={"selected_letter": "B"})
    r2 = client.get("/api/stats/benchmark")
    assert r2.status_code == 200
    data2 = r2.get_json()
    assert data2["accuracy_overall"] is not None
    assert data2["last7_attempts"] >= 1


def test_stats_bottlenecks(client):
    # Responder 2 erradas na mesma questao ou subtema
    client.post("/api/questions/1/attempt", json={"selected_letter": "A"})
    client.post("/api/questions/1/attempt", json={"selected_letter": "C"})

    r = client.get("/api/stats/bottlenecks")
    assert r.status_code == 200
    data = r.get_json()
    assert isinstance(data, list)


def test_stats_domain_summary(client):
    r = client.get("/api/stats/domain-summary")
    assert r.status_code == 200
    data = r.get_json()
    assert "overall_domain_pct" in data
    assert "areas" in data
    assert len(data["areas"]) >= 5


def test_stats_error_notebook_summary(client):
    # Registrar um erro
    client.post("/api/questions/1/attempt", json={"selected_letter": "A"})
    r = client.get("/api/stats/error-notebook-summary")
    assert r.status_code == 200
    data = r.get_json()
    assert "ever_wrong_count" in data
    assert "currently_unresolved_count" in data
    assert "practice_url" in data
