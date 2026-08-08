"""Blueprint: metadados, listagem/fila de estudo, detalhe, tentativa e favoritos."""
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from .db import get_db
from .filters import question_filter_clauses
from .schemas import AttemptIn, ValidationError
from . import srs

bp = Blueprint("questions", __name__)


@bp.route("/meta")
def meta():
    db = get_db()
    institutions = db.execute(
        """SELECT institution_code, institution_label, COUNT(*) n
           FROM questions GROUP BY institution_code ORDER BY n DESC"""
    ).fetchall()
    years = db.execute("SELECT DISTINCT year FROM questions WHERE year IS NOT NULL ORDER BY year").fetchall()
    sources = db.execute(
        "SELECT source_file, COUNT(*) n FROM questions GROUP BY source_file ORDER BY source_file"
    ).fetchall()
    areas = db.execute(
        """SELECT area, COUNT(*) n FROM questions
           WHERE area IS NOT NULL AND area != '' GROUP BY area ORDER BY n DESC"""
    ).fetchall()
    total = db.execute("SELECT COUNT(*) n FROM questions").fetchone()["n"]
    answered = db.execute("SELECT COUNT(DISTINCT question_id) n FROM attempts").fetchone()["n"]
    return jsonify({
        "institutions": [dict(r) for r in institutions],
        "years": [r["year"] for r in years],
        "sources": [dict(r) for r in sources],
        "areas": [dict(r) for r in areas],
        "total_questions": total,
        "answered_questions": answered,
    })


@bp.route("/subtemas")
def subtemas():
    db = get_db()
    area = request.args.get("area")
    q = request.args.get("q", "").strip()
    clauses = ["subtema IS NOT NULL", "subtema != ''"]
    params = []
    if area:
        clauses.append("area = ?")
        params.append(area)
    if q:
        clauses.append("subtema LIKE ?")
        params.append(f"%{q}%")
    where = " AND ".join(clauses)
    rows = db.execute(
        f"SELECT subtema, COUNT(*) n FROM questions WHERE {where} GROUP BY subtema ORDER BY n DESC LIMIT 50",
        params,
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@bp.route("/questions")
def questions():
    db = get_db()
    clauses, params = question_filter_clauses(request.args)
    where = " AND ".join(clauses)
    limit = min(int(request.args.get("limit", 500)), 2000)
    rows = db.execute(
        f"""SELECT q.id, q.source_file, q.source_number, q.year, q.institution_code,
                   q.institution_label, q.topic, q.area, q.subtema
            FROM questions q WHERE {where} ORDER BY RANDOM() LIMIT ?""",
        (*params, limit),
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@bp.route("/questions/count")
def questions_count():
    db = get_db()
    clauses, params = question_filter_clauses(request.args)
    where = " AND ".join(clauses)
    n = db.execute(f"SELECT COUNT(*) n FROM questions q WHERE {where}", params).fetchone()["n"]
    return jsonify({"count": n})


@bp.route("/questions/<int:qid>")
def question_detail(qid):
    db = get_db()
    q = db.execute("SELECT * FROM questions WHERE id = ?", (qid,)).fetchone()
    if not q:
        return jsonify({"error": "not found"}), 404
    alts = db.execute(
        "SELECT letter, text FROM alternatives WHERE question_id = ? ORDER BY letter", (qid,)
    ).fetchall()
    imgs = db.execute(
        "SELECT file_path FROM question_images WHERE question_id = ? ORDER BY order_index", (qid,)
    ).fetchall()
    last_attempt = db.execute(
        "SELECT selected_letter, is_correct FROM attempts WHERE question_id = ? ORDER BY id DESC LIMIT 1",
        (qid,),
    ).fetchone()
    is_favorite = db.execute("SELECT 1 FROM favorites WHERE question_id = ?", (qid,)).fetchone()
    return jsonify({
        "id": q["id"], "source_file": q["source_file"], "source_number": q["source_number"],
        "year": q["year"], "institution_code": q["institution_code"],
        "institution_label": q["institution_label"], "topic": q["topic"],
        "area": q["area"], "subtema": q["subtema"], "stem": q["stem"],
        "alternatives": [dict(a) for a in alts],
        "images": [i["file_path"] for i in imgs],
        "already_answered": dict(last_attempt) if last_attempt else None,
        "is_favorite": bool(is_favorite),
    })


@bp.route("/questions/<int:qid>/attempt", methods=["POST"])
def submit_attempt(qid):
    db = get_db()
    try:
        payload = AttemptIn.model_validate(request.get_json(force=True) or {})
    except ValidationError as e:
        return jsonify({"error": "invalid input", "details": e.errors()}), 400

    q = db.execute("SELECT correct_letter FROM questions WHERE id = ?", (qid,)).fetchone()
    if not q:
        return jsonify({"error": "not found"}), 404

    selected = payload.selected_letter.upper()
    is_correct = 1 if selected == q["correct_letter"] else 0

    db.execute(
        """INSERT INTO attempts (question_id, selected_letter, is_correct, answered_at, time_spent_ms, confidence)
           VALUES (?,?,?,?,?,?)""",
        (qid, selected, is_correct, datetime.now(timezone.utc).isoformat(),
         payload.time_spent_ms, payload.confidence),
    )

    # Repetição espaçada (FSRS)
    sr = db.execute("SELECT fsrs_card FROM spaced_repetition WHERE question_id = ?", (qid,)).fetchone()
    card_json, next_review = srs.review(sr["fsrs_card"] if sr else None, is_correct, payload.confidence)
    db.execute("""
        INSERT INTO spaced_repetition (question_id, next_review_date, fsrs_card)
        VALUES (?, ?, ?)
        ON CONFLICT(question_id) DO UPDATE SET
            next_review_date = excluded.next_review_date, fsrs_card = excluded.fsrs_card
    """, (qid, next_review, card_json))
    db.commit()

    exp = db.execute("SELECT explanation_text FROM explanations WHERE question_id = ?", (qid,)).fetchone()
    return jsonify({
        "is_correct": bool(is_correct),
        "correct_letter": q["correct_letter"],
        "explanation": exp["explanation_text"] if exp else None,
        "next_review_date": next_review,
    })


@bp.route("/questions/<int:qid>/favorite", methods=["POST"])
def toggle_favorite(qid):
    db = get_db()
    fav = db.execute("SELECT 1 FROM favorites WHERE question_id = ?", (qid,)).fetchone()
    if fav:
        db.execute("DELETE FROM favorites WHERE question_id = ?", (qid,))
        is_fav = False
    else:
        db.execute("INSERT INTO favorites (question_id) VALUES (?)", (qid,))
        is_fav = True
    db.commit()
    return jsonify({"is_favorite": is_fav})
