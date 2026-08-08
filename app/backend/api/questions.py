"""Blueprint: metadados, listagem/fila de estudo, detalhe, tentativa e favoritos."""
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request, g

from .db import get_db
from .filters import question_filter_clauses
from .schemas import AttemptIn, BatchAttemptIn, ValidationError
from . import srs
import random

bp = Blueprint("questions", __name__)


@bp.route("/simulado/usp")
def simulado_usp():
    db = get_db()
    areas = ["Cirurgia", "Clínica Médica", "Pediatria", "Ginecologia e Obstetrícia", "Medicina Preventiva e Social"]
    rows = []
    for area in areas:
        q = db.execute("""
            SELECT q.id, q.source_file, q.source_number, q.year, q.institution_code,
                   q.institution_label, q.topic, q.area, q.subtema
            FROM questions q 
            WHERE q.institution_code IN ('USP-SP', 'USP-RP') AND q.area = ? AND q.missing_alts = 0
            ORDER BY RANDOM() LIMIT 24
        """, (area,)).fetchall()
        rows.extend(q)
    
    out = [dict(r) for r in rows]
    random.shuffle(out)
    return jsonify(out)


@bp.route("/search")
def search_questions():
    db = get_db()
    q = request.args.get("q", "").strip()
    semantic = request.args.get("semantic", "false").lower() == "true"
    
    if semantic:
        from .ai import expand_search_query
        expanded_terms = expand_search_query(q)
        fts_query = " OR ".join([f'"{term.replace(chr(34), "")}"' for term in expanded_terms])
    else:
        # Padrão: adiciona asterisco para pegar inícios de palavras (ex: press -> pressao)
        terms = [f'"{t.replace(chr(34), "")}"*' for t in q.split()]
        fts_query = " AND ".join(terms)
    
    rows = db.execute("""
        SELECT q.id, q.institution_code, q.year, q.area, q.subtema,
               snippet(questions_fts, 0, '<mark>', '</mark>', '...', 20) as stem_snippet,
               snippet(questions_fts, 1, '<mark>', '</mark>', '...', 20) as exp_snippet
        FROM questions_fts fts
        JOIN questions q ON q.id = fts.rowid
        WHERE questions_fts MATCH ?
        ORDER BY rank
        LIMIT 50
    """, (fts_query,)).fetchall()
    
    return jsonify([dict(r) for r in rows])


@bp.route("/meta")
def meta():
    db = get_db()
    clauses, params = question_filter_clauses(request.args)
    
    # We must replace q. with empty or alias questions as q
    # Because question_filter_clauses assumes "q.institution_code" etc
    where = " AND ".join(clauses)

    institutions = db.execute(
        f"""SELECT q.institution_code, q.institution_label, COUNT(*) n
           FROM questions q WHERE {where} GROUP BY q.institution_code ORDER BY n DESC""", params
    ).fetchall()
    
    years = db.execute(f"SELECT DISTINCT q.year FROM questions q WHERE q.year IS NOT NULL AND {where} ORDER BY q.year", params).fetchall()
    
    sources = db.execute(
        f"SELECT q.source_file, COUNT(*) n FROM questions q WHERE {where} GROUP BY q.source_file ORDER BY q.source_file", params
    ).fetchall()
    
    areas = db.execute(
        f"""SELECT q.area, COUNT(*) n FROM questions q
           WHERE q.area IS NOT NULL AND q.area != '' AND {where} GROUP BY q.area ORDER BY n DESC""", params
    ).fetchall()
    
    subtemas = db.execute(
        f"""SELECT q.subtema, COUNT(*) n FROM questions q
           WHERE q.subtema IS NOT NULL AND q.subtema != '' AND {where} GROUP BY q.subtema ORDER BY n DESC LIMIT 300""", params
    ).fetchall()
    
    total = db.execute(f"SELECT COUNT(*) n FROM questions q WHERE {where}", params).fetchone()["n"]
    answered_params = list(params)
    answered_params.append(g.user_id)
    answered = db.execute(f"SELECT COUNT(DISTINCT q.id) n FROM questions q WHERE {where} AND q.id IN (SELECT question_id FROM attempts WHERE user_id = ?)", answered_params).fetchone()["n"]
    
    return jsonify({
        "institutions": [dict(r) for r in institutions],
        "years": [r["year"] for r in years],
        "sources": [dict(r) for r in sources],
        "areas": [dict(r) for r in areas],
        "subtemas": [dict(r) for r in subtemas],
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
        "SELECT selected_letter, is_correct FROM attempts WHERE question_id = ? AND user_id = ? ORDER BY id DESC LIMIT 1",
        (qid, g.user_id),
    ).fetchone()
    times_wrong = db.execute(
        "SELECT COUNT(*) as n FROM attempts WHERE question_id = ? AND is_correct = 0 AND user_id = ?", 
        (qid, g.user_id)
    ).fetchone()["n"]
    is_favorite = db.execute("SELECT 1 FROM favorites WHERE question_id = ? AND user_id = ?", (qid, g.user_id)).fetchone()
    return jsonify({
        "id": q["id"], "source_file": q["source_file"], "source_number": q["source_number"],
        "year": q["year"], "institution_code": q["institution_code"],
        "institution_label": q["institution_label"], "topic": q["topic"],
        "area": q["area"], "subtema": q["subtema"], "stem": q["stem"],
        "alternatives": [dict(a) for a in alts],
        "images": [i["file_path"] for i in imgs],
        "already_answered": dict(last_attempt) if last_attempt else None,
        "is_favorite": bool(is_favorite),
        "times_wrong": times_wrong,
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
        """INSERT INTO attempts (question_id, selected_letter, is_correct, answered_at, time_spent_ms, confidence, user_id)
           VALUES (?,?,?,?,?,?,?)""",
        (qid, selected, is_correct, datetime.now(timezone.utc).isoformat(),
         payload.time_spent_ms, payload.confidence, g.user_id),
    )

    # Repetição espaçada (FSRS)
    sr = db.execute("SELECT fsrs_card FROM spaced_repetition WHERE question_id = ? AND user_id = ?", (qid, g.user_id)).fetchone()
    card_json, next_review = srs.review(sr["fsrs_card"] if sr else None, is_correct, payload.confidence)
    db.execute("""
        INSERT INTO spaced_repetition (question_id, next_review_date, fsrs_card, user_id)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(question_id, user_id) DO UPDATE SET
            next_review_date = excluded.next_review_date, fsrs_card = excluded.fsrs_card
    """, (qid, next_review, card_json, g.user_id))
    db.commit()

    exp = db.execute("SELECT explanation_text FROM explanations WHERE question_id = ?", (qid,)).fetchone()
    return jsonify({
        "is_correct": bool(is_correct),
        "correct_letter": q["correct_letter"],
        "explanation": exp["explanation_text"] if exp else None,
        "next_review_date": next_review,
    })


@bp.route("/attempt/batch", methods=["POST"])
def submit_attempt_batch():
    db = get_db()
    try:
        payload = BatchAttemptIn.model_validate(request.get_json(force=True) or {})
    except ValidationError as e:
        return jsonify({"error": "invalid input", "details": e.errors()}), 400

    results = []
    answered_at = datetime.now(timezone.utc).isoformat()

    # To avoid many SELECTs, get all correct_letters and explanations at once
    q_ids = [item.question_id for item in payload.attempts]
    if not q_ids:
        return jsonify({"results": []})

    CHUNK_SIZE = 500
    q_map = {}
    exp_map = {}
    srs_map = {}

    for i in range(0, len(q_ids), CHUNK_SIZE):
        chunk = q_ids[i:i + CHUNK_SIZE]
        placeholders = ",".join("?" * len(chunk))
        
        qs = db.execute(f"SELECT id, correct_letter FROM questions WHERE id IN ({placeholders})", chunk).fetchall()
        for q in qs:
            q_map[q["id"]] = q["correct_letter"]
            
        exps = db.execute(f"SELECT question_id, explanation_text FROM explanations WHERE question_id IN ({placeholders})", chunk).fetchall()
        for e in exps:
            exp_map[e["question_id"]] = e["explanation_text"]
            
        chunk_args = list(chunk)
        chunk_args.append(g.user_id)
        srs_data = db.execute(f"SELECT question_id, fsrs_card FROM spaced_repetition WHERE question_id IN ({placeholders}) AND user_id = ?", chunk_args).fetchall()
        for s in srs_data:
            srs_map[s["question_id"]] = s["fsrs_card"]

    for item in payload.attempts:
        correct_letter = q_map.get(item.question_id)
        if not correct_letter:
            continue
        
        selected = item.selected_letter.upper()
        is_correct = 1 if selected == correct_letter else 0
        conf = item.confidence or "certeza"

        db.execute(
            """INSERT INTO attempts (question_id, selected_letter, is_correct, answered_at, time_spent_ms, confidence, user_id)
               VALUES (?,?,?,?,?,?,?)""",
            (item.question_id, selected, is_correct, answered_at, item.time_spent_ms, conf, g.user_id),
        )

        old_card = srs_map.get(item.question_id)
        card_json, next_review = srs.review(old_card, is_correct, conf)
        db.execute("""
            INSERT INTO spaced_repetition (question_id, next_review_date, fsrs_card, user_id)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(question_id, user_id) DO UPDATE SET
                next_review_date = excluded.next_review_date, fsrs_card = excluded.fsrs_card
        """, (item.question_id, next_review, card_json, g.user_id))

        results.append({
            "question_id": item.question_id,
            "is_correct": bool(is_correct),
            "correct_letter": correct_letter,
            "explanation": exp_map.get(item.question_id),
            "next_review_date": next_review
        })

    db.commit()
    return jsonify({"results": results})


@bp.route("/questions/<int:qid>/favorite", methods=["POST"])
def toggle_favorite(qid):
    db = get_db()
    fav = db.execute("SELECT 1 FROM favorites WHERE question_id = ? AND user_id = ?", (qid, g.user_id)).fetchone()
    if fav:
        db.execute("DELETE FROM favorites WHERE question_id = ? AND user_id = ?", (qid, g.user_id))
        is_fav = False
    else:
        db.execute("INSERT INTO favorites (question_id, user_id) VALUES (?, ?)", (qid, g.user_id))
        is_fav = True
    db.commit()
    return jsonify({"success": True, "is_favorite": is_fav})
