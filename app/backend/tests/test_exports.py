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
    assert "SUMMARY:[MedQuest]" in text
    assert "END:VCALENDAR" in text
