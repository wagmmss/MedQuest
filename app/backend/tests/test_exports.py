"""Testes de exportações externas (Anki e iCalendar .ics)."""
import pytest


def test_export_anki_header_and_format(client):
    res = client.get("/api/flashcards/export/anki")
    assert res.status_code == 200
    assert "text/plain" in res.headers.get("Content-Type", "")
    text = res.get_data(as_text=True)
    assert "#separator:tab" in text
    assert "#deck:MedQuest::Revisão_Ativa" in text
    assert "#notetype:Cloze" in text


def test_export_anki_with_generated_card(client):
    # Gera um flashcard para teste
    gen_res = client.post("/api/flashcards/generate", json={"question_id": 1, "wrong_letter": "A"})
    assert gen_res.status_code == 200

    res = client.get("/api/flashcards/export/anki")
    assert res.status_code == 200
    text = res.get_data(as_text=True)
    assert "{{c1::" in text
    assert "MedQuest" in text
    assert "Area::" in text or "Subtema::" in text


def test_export_ics_calendar(client):
    # Salva configuração de teste
    client.post("/api/planner/config", json={
        "start_date": "2026-08-24T12:00:00Z",
        "exam_date": "2026-11-15T12:00:00Z",
        "days_per_week": 6,
        "hours_per_day": 4,
        "target_score": 78
    })

    res = client.get("/api/planner/export/ics")
    assert res.status_code == 200
    assert "text/calendar" in res.headers.get("Content-Type", "")
    text = res.get_data(as_text=True)
    assert "BEGIN:VCALENDAR" in text
    assert "VERSION:2.0" in text
    assert "BEGIN:VEVENT" in text
    assert "📖" in text or "Aula:" in text or "Semana" in text
    assert "Revisão 24h" in text
    assert "Revisão 7d" in text
    assert "Revisão 30d" in text
    assert "END:VCALENDAR" in text


def test_calendar_feed_endpoint(client):
    res = client.get("/api/planner/calendar/feed")
    assert res.status_code == 200
    assert "text/calendar" in res.headers.get("Content-Type", "")
    text = res.get_data(as_text=True)
    assert "BEGIN:VCALENDAR" in text
    assert "END:VCALENDAR" in text


def test_calendar_feed_ignores_user_id_query_parameter(client, monkeypatch):
    from api import plan

    captured = {}

    def fake_calendar_content(_db, user_id):
        captured["user_id"] = user_id
        return "BEGIN:VCALENDAR\r\nEND:VCALENDAR"

    monkeypatch.setattr(plan, "_generate_calendar_ics_content", fake_calendar_content)
    res = client.get("/api/planner/calendar/feed?user_id=another-user")

    assert res.status_code == 200
    assert captured["user_id"] == "1"
