"""Testes de integração herméticos para o blueprint de flashcards."""
import pytest


def test_flashcards_generate_and_review(client):
    # Gera flashcard a partir do erro na questão 1 (resposta certa B, marcou A)
    r = client.post("/api/flashcards/generate", json={
        "question_id": 1,
        "wrong_letter": "A"
    })
    assert r.status_code == 200
    data = r.get_json()
    assert "id" in data
    assert data["question_id"] == 1
    assert "front" in data
    assert "back" in data
    fid = data["id"]

    # Consulta flashcards vencidos
    r_due = client.get("/api/flashcards/review")
    assert r_due.status_code == 200
    due_list = r_due.get_json()
    assert len(due_list) >= 1
    assert any(card["id"] == fid for card in due_list)

    # Executa revisão do flashcard com 'certeza'
    r_rev = client.post(f"/api/flashcards/{fid}/review", json={
        "confidence": "certeza"
    })
    assert r_rev.status_code == 200
    rev_data = r_rev.get_json()
    assert rev_data["id"] == fid
    assert "next_review_date" in rev_data

    # Reporta flashcard
    r_rep = client.post(f"/api/flashcards/{fid}/report", json={
        "reason": "Erro de digitação no enunciado"
    })
    assert r_rep.status_code == 200
    assert r_rep.get_json()["success"] is True


def test_flashcards_validation_errors(client):
    # Campos obrigatórios ausentes
    r = client.post("/api/flashcards/generate", json={})
    assert r.status_code == 400

    # Questão inexistente
    r = client.post("/api/flashcards/generate", json={
        "question_id": 9999,
        "wrong_letter": "A"
    })
    assert r.status_code == 404

    # Confiança inválida no review
    r = client.post("/api/flashcards/1/review", json={
        "confidence": "invalido"
    })
    assert r.status_code == 400

    # Flashcard inexistente
    r = client.post("/api/flashcards/9999/review", json={
        "confidence": "certeza"
    })
    assert r.status_code == 404

    # Report sem motivo
    r = client.post("/api/flashcards/1/report", json={})
    assert r.status_code == 400
