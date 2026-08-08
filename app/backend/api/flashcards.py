from datetime import datetime, timezone
from flask import Blueprint, jsonify, request, g
from .db import get_db
from . import srs
from .ai import generate_cloze_flashcard

bp = Blueprint("flashcards", __name__)

@bp.route("/flashcards/generate", methods=["POST"])
def generate():
    data = request.get_json() or {}
    question_id = data.get("question_id")
    wrong_letter = data.get("wrong_letter", "").upper()

    if not question_id or not wrong_letter:
        return jsonify({"error": "question_id e wrong_letter são obrigatórios."}), 400

    db = get_db()
    
    # Busca a questão, a alternativa correta e a explicação
    q = db.execute("SELECT stem, correct_letter FROM questions WHERE id = ?", (question_id,)).fetchone()
    if not q:
        return jsonify({"error": "Questão não encontrada."}), 404
        
    correct_alt = db.execute("SELECT text FROM alternatives WHERE question_id = ? AND letter = ?", (question_id, q["correct_letter"])).fetchone()
    wrong_alt = db.execute("SELECT text FROM alternatives WHERE question_id = ? AND letter = ?", (question_id, wrong_letter)).fetchone()
    exp = db.execute("SELECT explanation_text FROM explanations WHERE question_id = ?", (question_id,)).fetchone()
    
    if not correct_alt or not wrong_alt:
        return jsonify({"error": "Alternativas não encontradas."}), 404

    # Chama a IA
    card_data = generate_cloze_flashcard(
        stem=q["stem"], 
        correct_text=f"{q['correct_letter']}) {correct_alt['text']}", 
        wrong_text=f"{wrong_letter}) {wrong_alt['text']}", 
        explanation=exp["explanation_text"] if exp else ""
    )

    now = datetime.now(timezone.utc).isoformat()
    # Initial FSRS parameters for a new card: just set next_review_date to now
    cursor = db.execute("""
        INSERT INTO flashcards (question_id, front, back, created_at, next_review_date, fsrs_card, user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (question_id, card_data.get("front", ""), card_data.get("back", ""), now, now, None, g.user_id))
    
    db.commit()

    return jsonify({
        "id": cursor.lastrowid,
        "question_id": question_id,
        "front": card_data.get("front", ""),
        "back": card_data.get("back", "")
    })


@bp.route("/flashcards/review", methods=["GET"])
def get_due_flashcards():
    db = get_db()
    now = datetime.now(timezone.utc).isoformat()
    # Pega até 50 cards vencidos
    rows = db.execute("""
        SELECT f.id, f.question_id, f.front, f.back, f.next_review_date, q.stem
        FROM flashcards f
        JOIN questions q ON f.question_id = q.id
        WHERE f.next_review_date <= ? AND f.user_id = ?
        ORDER BY f.next_review_date ASC LIMIT 50
    """, (now, g.user_id)).fetchall()
    
    return jsonify([dict(r) for r in rows])


@bp.route("/flashcards/<int:fid>/review", methods=["POST"])
def review_flashcard(fid):
    data = request.get_json() or {}
    confidence = data.get("confidence") # "errei", "duvida", "certeza"
    
    if confidence not in ["errei", "duvida", "certeza"]:
        return jsonify({"error": "confidence deve ser 'errei', 'duvida' ou 'certeza'."}), 400
        
    # Translate confidence to FSRS rating (is_correct)
    # se for errei -> is_correct=0
    # se for duvida -> is_correct=1, confidence="duvida"
    # se for certeza -> is_correct=1, confidence="certeza"
    is_correct = 0 if confidence == "errei" else 1

    db = get_db()
    card = db.execute("SELECT fsrs_card FROM flashcards WHERE id = ? AND user_id = ?", (fid, g.user_id)).fetchone()
    if not card:
        return jsonify({"error": "Flashcard não encontrado."}), 404

    card_json, next_review = srs.review(card["fsrs_card"], is_correct, confidence if is_correct else "chutei")
    
    db.execute("""
        UPDATE flashcards 
        SET next_review_date = ?, fsrs_card = ? 
        WHERE id = ? AND user_id = ?
    """, (next_review, card_json, fid, g.user_id))
    db.commit()

    return jsonify({
        "id": fid,
        "next_review_date": next_review
    })
