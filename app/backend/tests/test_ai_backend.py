"""Testes para a suite de Inteligência Artificial Google Gemini 3.7 Flash no Backend."""
from api import ai


def test_ai_health(client):
    res = client.get("/api/ai/health")
    assert res.status_code == 200
    data = res.get_json()
    assert "model" in data
    assert "total_keys" in data


def test_ask_ai_endpoint(client):
    res = client.post(
        "/api/questions/1/ask_ai",
        json={"user_question": "Qual a conduta padrão ouro?", "user_letter": "A"}
    )
    assert res.status_code == 200
    data = res.get_json()
    assert "answer" in data
    assert "model" in data
    assert len(data["answer"]) > 10


def test_ask_ai_endpoint_reports_provider_unavailability(client, monkeypatch):
    """A fallback nunca deve ser apresentado como resposta gerada pela IA."""
    monkeypatch.setattr(
        ai,
        "ask_preceptor_ai",
        lambda **_: {"answer": "fallback", "model": "deterministic_fallback", "source": "fallback"},
    )

    res = client.post("/api/questions/1/ask_ai", json={"user_question": "Explique"})

    assert res.status_code == 503
    assert "temporariamente indisponível" in res.get_json()["error"]


def test_prescribe_study_endpoint(client):
    res = client.post(
        "/api/ai/prescribe_study",
        json={
            "target_institution": "USP",
            "weak_topics": [
                {"topic": "Hipertensão Arterial", "accuracy": 0.4, "correct": 2, "attempts": 5}
            ],
            "distractors": [
                {"subtema": "Hipertensão Arterial", "wrong_choices": [{"letter": "A", "count": 3}]}
            ],
            "at_risk_topics": [
                {"subtema": "Imunização", "items_count": 2, "retrievability": 0.55}
            ]
        }
    )
    assert res.status_code == 200
    data = res.get_json()
    assert "prescription_markdown" in data
    assert len(data["prescription_markdown"]) > 20


def test_synthesize_explanation_endpoint(client):
    res = client.post(
        "/api/questions/2/synthesize_explanation",
        json={"force_regenerate": True}
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["question_id"] == 2
    assert "explanation_text" in data
    assert "Pulo do Gato" in data["explanation_text"] or "Gabarito" in data["explanation_text"]


def test_flashcard_generate_without_wrong_letter(client):
    res = client.post(
        "/api/flashcards/generate",
        json={"question_id": 1, "wrong_letter": ""}
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["question_id"] == 1
    assert "front" in data
    assert "{{c1::" in data["front"]


def test_flashcard_generate_with_wrong_letter(client):
    res = client.post(
        "/api/flashcards/generate",
        json={"question_id": 1, "wrong_letter": "A"}
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["question_id"] == 1
    assert "front" in data
    assert "{{c1::" in data["front"]


def test_flashcard_fallback_normalizes_options_without_ai(monkeypatch):
    """The deterministic path must work when every AI provider is unavailable."""
    monkeypatch.setattr(ai.gemini_pool, "_keys", [])
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    card = ai.generate_cloze_flashcard(
        stem="Paciente com hipertensão. Qual a conduta?",
        correct_text="B) Iniciar tratamento adequado",
        wrong_text="A) Não tratar",
    )

    assert "{{c1::Iniciar tratamento adequado}}" in card["front"]
    assert "Não tratar" in card["back"]


def test_semantic_search_expansion(client):
    res = client.get("/api/search?q=hipertensao&semantic=true")
    assert res.status_code == 200
    data = res.get_json()
    assert isinstance(data, list)
