"""Blueprint: metadados, listagem/fila de estudo, detalhe, tentativa e favoritos."""
from datetime import datetime, timezone
from html import escape
import re

from flask import Blueprint, jsonify, request, g

from .db import get_db
from .filters import question_filter_clauses
from .schemas import AttemptIn, BatchAttemptIn, ReviewIn, ValidationError
from . import srs
import random

bp = Blueprint("questions", __name__)


def _sample_ids(db, where_clause, params, limit):
    """Amostragem rápida por faixa de IDs, evitando ORDER BY RANDOM().

    Obtém min/max ID, gera candidatos aleatórios em Python e filtra.
    Fallback para ORDER BY RANDOM() se a faixa for muito esparsa.
    """
    bounds = db.execute(
        f"SELECT MIN(q.id) AS lo, MAX(q.id) AS hi, COUNT(*) AS n FROM questions q WHERE {where_clause}",
        params,
    ).fetchone()
    lo, hi, n = bounds["lo"], bounds["hi"], bounds["n"]
    if not lo or n == 0:
        return []
    effective_limit = min(limit, n)
    # Se a tabela é densa o suficiente, amostragem por faixa é eficiente
    if n > 0 and (hi - lo + 1) / n < 5:
        candidates = random.sample(range(lo, hi + 1), min(effective_limit * 3, hi - lo + 1))
        placeholders = ",".join("?" * len(candidates))
        rows = db.execute(
            f"SELECT q.id FROM questions q WHERE q.id IN ({placeholders}) AND {where_clause} LIMIT ?",
            (*candidates, *params, effective_limit),
        ).fetchall()
        ids = [r["id"] for r in rows]
        if len(ids) >= effective_limit:
            return ids[:effective_limit]
    # Fallback para RANDOM() quando a faixa é muito esparsa
    rows = db.execute(
        f"SELECT q.id FROM questions q WHERE {where_clause} ORDER BY RANDOM() LIMIT ?",
        (*params, effective_limit),
    ).fetchall()
    return [r["id"] for r in rows]


def _bounded_int(value, default, minimum, maximum):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(parsed, maximum))


def _fts_phrase(value):
    """Converte texto livre em uma expressão FTS5 segura e limitada."""
    words = re.findall(r"\w+", value or "", flags=re.UNICODE)[:12]
    return " ".join(words)


def _safe_snippet(value):
    """Escapa o conteúdo original e preserva somente as tags de destaque."""
    return (escape(value or "")
            .replace("⟦MQH⟧", "<mark>")
            .replace("⟦/MQH⟧", "</mark>"))


@bp.route("/simulado/usp")
def simulado_usp():
    db = get_db()
    areas = ["Cirurgia", "Clínica Médica", "Pediatria", "Ginecologia e Obstetrícia", "Medicina Preventiva e Social"]
    all_ids = []
    for area in areas:
        where = "q.institution_code IN ('USP-SP', 'USP-RP') AND q.area = ? AND q.missing_alts = 0"
        ids = _sample_ids(db, where, (area,), 24)
        all_ids.extend(ids)

    if not all_ids:
        return jsonify([])
    placeholders = ",".join("?" * len(all_ids))
    rows = db.execute(
        f"""SELECT q.id, q.source_file, q.source_number, q.year, q.institution_code,
                   q.institution_label, q.topic, q.area, q.subtema
            FROM questions q WHERE q.id IN ({placeholders})""",
        all_ids,
    ).fetchall()
    out = [dict(r) for r in rows]
    random.shuffle(out)
    return jsonify(out)


@bp.route("/search")
def search_questions():
    db = get_db()
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])
    semantic = request.args.get("semantic", "false").lower() == "true"
    
    if semantic:
        from .ai import expand_search_query
        expanded_terms = expand_search_query(q)
        phrases = [_fts_phrase(term) for term in expanded_terms]
        fts_query = " OR ".join(f'"{phrase}"' for phrase in phrases if phrase)
    else:
        # Padrão: adiciona asterisco para pegar inícios de palavras (ex: press -> pressao)
        terms = [f'"{term}"*' for term in _fts_phrase(q).split()]
        fts_query = " AND ".join(terms)

    if not fts_query:
        return jsonify([])
    
    rows = db.execute("""
        SELECT q.id, q.institution_code, q.year, q.area, q.subtema,
               snippet(questions_fts, 0, '⟦MQH⟧', '⟦/MQH⟧', '...', 20) as stem_snippet,
               snippet(questions_fts, 1, '⟦MQH⟧', '⟦/MQH⟧', '...', 20) as exp_snippet
        FROM questions_fts fts
        JOIN questions q ON q.id = fts.rowid
        WHERE questions_fts MATCH ?
        ORDER BY rank
        LIMIT 50
    """, (fts_query,)).fetchall()
    
    out = []
    for row in rows:
        item = dict(row)
        item["stem_snippet"] = _safe_snippet(item.get("stem_snippet"))
        item["exp_snippet"] = _safe_snippet(item.get("exp_snippet"))
        out.append(item)
    return jsonify(out)


@bp.route("/meta")
def meta():
    db = get_db()
    clauses, params = question_filter_clauses(request.args)
    
    # We must replace q. with empty or alias questions as q
    # Because question_filter_clauses assumes "q.institution_code" etc
    where = " AND ".join(clauses)

    from werkzeug.datastructures import MultiDict
    args_no_subtema = MultiDict((k, v) for k, v in request.args.items(multi=True) if k != 'subtema')
    clauses_no_subtema, params_no_subtema = question_filter_clauses(args_no_subtema)
    where_no_subtema = " AND ".join(clauses_no_subtema)

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
           WHERE q.subtema IS NOT NULL AND q.subtema != '' AND {where_no_subtema} GROUP BY q.subtema ORDER BY n DESC LIMIT 300""", params_no_subtema
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
    limit = _bounded_int(request.args.get("limit"), default=500, minimum=1, maximum=2000)
    ids = _sample_ids(db, where, params, limit)
    if not ids:
        return jsonify([])
    placeholders = ",".join("?" * len(ids))
    rows = db.execute(
        f"""SELECT q.id, q.source_file, q.source_number, q.year, q.institution_code,
                   q.institution_label, q.topic, q.area, q.subtema
            FROM questions q WHERE q.id IN ({placeholders})""",
        ids,
    ).fetchall()
    out = [dict(r) for r in rows]
    random.shuffle(out)
    return jsonify(out)


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
        "is_verified": bool(q.get("is_verified", 0)),
        "last_updated_at": q.get("last_updated_at"),
        "technical_note": q.get("technical_note"),
        "medical_references": q.get("medical_references"),
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
    next_review = None
    if payload.confidence != "defer":
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


@bp.route("/questions/<int:qid>/review", methods=["POST"])
def review_fsrs(qid):
    db = get_db()
    try:
        data = ReviewIn.model_validate(request.get_json(force=True) or {})
    except ValidationError as e:
        return jsonify({"error": "invalid input", "details": e.errors()}), 400
    confidence = data.confidence
    
    last_attempt = db.execute(
        "SELECT id, is_correct FROM attempts WHERE question_id = ? AND user_id = ? ORDER BY id DESC LIMIT 1", 
        (qid, g.user_id)
    ).fetchone()
    
    if not last_attempt:
        return jsonify({"error": "No attempt found"}), 400
        
    db.execute(
        "UPDATE attempts SET confidence = ? WHERE id = ?",
        (confidence, last_attempt["id"])
    )
        
    sr = db.execute("SELECT fsrs_card FROM spaced_repetition WHERE question_id = ? AND user_id = ?", (qid, g.user_id)).fetchone()
    card_json, next_review = srs.review(sr["fsrs_card"] if sr else None, last_attempt["is_correct"], confidence)
    db.execute("""
        INSERT INTO spaced_repetition (question_id, next_review_date, fsrs_card, user_id)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(question_id, user_id) DO UPDATE SET
            next_review_date = excluded.next_review_date, fsrs_card = excluded.fsrs_card
    """, (qid, next_review, card_json, g.user_id))
    db.commit()
    return jsonify({"success": True, "next_review_date": next_review})

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


@bp.route("/questions/batch", methods=["POST"])
def question_batch_detail():
    """Retorna detalhes completos de múltiplas questões em uma única requisição.
    
    Aceita {"ids": [1, 2, ...]} com no máximo 200 IDs.
    Substitui até 120 chamadas individuais GET /questions/:id no simulado.
    """
    data = request.get_json(force=True) or {}
    ids = data.get("ids", [])
    force_4_options = data.get("force_4_options", False)
    if not ids or not isinstance(ids, list):
        return jsonify({"error": "ids is required and must be a list"}), 400
    ids = ids[:200]  # Cap at 200

    db = get_db()
    CHUNK = 500
    q_map = {}
    alt_map = {}
    img_map = {}
    attempt_map = {}
    wrong_map = {}
    fav_set = set()

    for i in range(0, len(ids), CHUNK):
        chunk = ids[i:i + CHUNK]
        ph = ",".join("?" * len(chunk))

        for r in db.execute(f"SELECT * FROM questions WHERE id IN ({ph})", chunk).fetchall():
            q_map[r["id"]] = dict(r)

        for r in db.execute(f"SELECT question_id, letter, text FROM alternatives WHERE question_id IN ({ph}) ORDER BY letter", chunk).fetchall():
            alt_map.setdefault(r["question_id"], []).append({"letter": r["letter"], "text": r["text"]})

        for r in db.execute(f"SELECT question_id, file_path FROM question_images WHERE question_id IN ({ph}) ORDER BY order_index", chunk).fetchall():
            img_map.setdefault(r["question_id"], []).append(r["file_path"])

        chunk_user = list(chunk) + [g.user_id]
        for r in db.execute(
            f"SELECT question_id, selected_letter, is_correct FROM attempts WHERE question_id IN ({ph}) AND user_id = ? ORDER BY id DESC",
            chunk_user,
        ).fetchall():
            if r["question_id"] not in attempt_map:
                attempt_map[r["question_id"]] = {"selected_letter": r["selected_letter"], "is_correct": bool(r["is_correct"])}

        for r in db.execute(
            f"SELECT question_id, COUNT(*) as n FROM attempts WHERE question_id IN ({ph}) AND is_correct = 0 AND user_id = ? GROUP BY question_id",
            chunk_user,
        ).fetchall():
            wrong_map[r["question_id"]] = r["n"]

        for r in db.execute(f"SELECT question_id FROM favorites WHERE question_id IN ({ph}) AND user_id = ?", chunk_user).fetchall():
            fav_set.add(r["question_id"])

    out = []
    for qid in ids:
        q = q_map.get(qid)
        if not q:
            continue
            
        alts = alt_map.get(qid, [])
        if force_4_options and len(alts) > 4:
            correct_letter = q.get("correct_letter")
            incorrects = [a for a in alts if a["letter"] != correct_letter]
            if incorrects:
                # Escolhe um distrator para remover para que sobrem apenas 4 alternativas
                # Se len for 5, remove 1. Se len for N, remove N-4
                remove_count = len(alts) - 4
                to_remove = random.sample(incorrects, remove_count)
                to_remove_letters = {a["letter"] for a in to_remove}
                alts = [a for a in alts if a["letter"] not in to_remove_letters]

        out.append({
            "id": q["id"],
            "source_file": q["source_file"],
            "source_number": q["source_number"],
            "year": q["year"],
            "institution_code": q["institution_code"],
            "institution_label": q["institution_label"],
            "topic": q["topic"],
            "area": q["area"],
            "subtema": q["subtema"],
            "stem": q["stem"],
            "is_verified": bool(q.get("is_verified", 0)),
            "last_updated_at": q.get("last_updated_at"),
            "technical_note": q.get("technical_note"),
            "medical_references": q.get("medical_references"),
            "alternatives": alts,
            "images": img_map.get(qid, []),
            "already_answered": attempt_map.get(qid),
            "is_favorite": qid in fav_set,
            "times_wrong": wrong_map.get(qid, 0),
        })

    return jsonify({"questions": out})


@bp.route("/images/<path:filename>")
def serve_image(filename):
    import os
    from flask import send_from_directory
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    static_dir = os.path.join(backend_dir, "static")
    return send_from_directory(static_dir, filename)

