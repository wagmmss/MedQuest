"""Blueprint: metadados, listagem/fila de estudo, detalhe, tentativa e favoritos."""
import json
import random
import re
import time
from datetime import datetime, timezone
from threading import Lock

from flask import Blueprint, g, jsonify, request

from . import srs
from .adaptive import rank_adaptive_candidates
from .db import db_transaction, get_db
from .filters import question_filter_clauses
from .idempotency import complete_idempotency, fail_idempotency, reserve_idempotency
from .schemas import (
    AttemptIn,
    BatchAttemptIn,
    FavoriteIn,
    PrescribeStudyIn,
    QuestionBatchIn,
    ReviewIn,
    SimuladoCustomIn,
    SynthesizeExplanationIn,
    ValidationError,
    validation_errors,
)


class SimpleTTLCache:
    def __init__(self, ttl_seconds, max_size=500):
        self.ttl = ttl_seconds
        self.max_size = max_size
        self.cache = {}
        self.lock = Lock()
        
    def get(self, key):
        with self.lock:
            if key in self.cache:
                value, expiry = self.cache[key]
                if time.time() < expiry:
                    return value
                else:
                    del self.cache[key]
            return None
            
    def set(self, key, value):
        with self.lock:
            now = time.time()
            stale = [k for k, (v, exp) in self.cache.items() if now >= exp]
            for k in stale:
                del self.cache[k]
            if len(self.cache) >= self.max_size:
                oldest = min(self.cache.keys(), key=lambda k: self.cache[k][1])
                del self.cache[oldest]
            self.cache[key] = (value, now + self.ttl)

    def clear_user(self, user_id):
        with self.lock:
            keys = [key for key in self.cache if isinstance(key, tuple) and key[0] == user_id]
            for key in keys:
                del self.cache[key]

meta_cache = SimpleTTLCache(60)

bp = Blueprint("questions", __name__)


def invalidate_user_caches(user_id):
    """Invalidate every derived per-user view after a successful mutation."""
    meta_cache.clear_user(user_id)
    from .stats import overview_cache
    overview_cache.clear_user(user_id)


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
        sample_size = min(effective_limit * 3, hi - lo + 1, 900)
        candidates = random.sample(range(lo, hi + 1), sample_size)
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
                   q.institution_label, q.topic, q.area, q.subtema, q.editorial_status
            FROM questions q WHERE q.id IN ({placeholders})""",
        all_ids,
    ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["is_autoral"] = bool(d.get("editorial_status") == "autoral" or (d.get("source_file") and "AUTORAL" in d.get("source_file").upper()))
        out.append(d)
    random.shuffle(out)
    return jsonify(out)


@bp.route("/simulado/custom", methods=["POST"])
def simulado_custom():
    db = get_db()
    try:
        data = SimuladoCustomIn.model_validate(request.get_json(force=True) or {})
    except ValidationError as e:
        return jsonify({"error": "invalid input", "details": validation_errors(e)}), 400
    institutions = [value[:64] for value in data.institutions]
    years = [value[:4] for value in data.years]
    q_per_area = data.questions_per_area
    
    areas = ["Cirurgia", "Clínica Médica", "Pediatria", "Ginecologia e Obstetrícia", "Medicina Preventiva e Social"]
    all_ids = []
    
    # Montar restrições
    base_clauses = ["q.missing_alts = 0"]
    base_params = []
    
    if institutions:
        placeholders = ",".join("?" * len(institutions))
        base_clauses.append(f"q.institution_code IN ({placeholders})")
        base_params.extend(institutions)
        
    if years:
        placeholders = ",".join("?" * len(years))
        base_clauses.append(f"q.year IN ({placeholders})")
        base_params.extend(years)
        
    for area in areas:
        clauses = base_clauses + ["q.area = ?"]
        params = base_params + [area]
        where = " AND ".join(clauses)
        ids = _sample_ids(db, where, tuple(params), q_per_area)
        all_ids.extend(ids)
        
    if not all_ids:
        return jsonify([])
        
    placeholders = ",".join("?" * len(all_ids))
    rows = db.execute(
        f"""SELECT q.id, q.source_file, q.source_number, q.year, q.institution_code,
                   q.institution_label, q.topic, q.area, q.subtema, q.editorial_status
            FROM questions q WHERE q.id IN ({placeholders})""",
        all_ids,
    ).fetchall()
    
    out = []
    for r in rows:
        d = dict(r)
        d["is_autoral"] = bool(d.get("editorial_status") == "autoral" or (d.get("source_file") and "AUTORAL" in d.get("source_file").upper()))
        out.append(d)
    random.shuffle(out)
    return jsonify(out)


@bp.route("/search")
def search_questions():
    db = get_db()
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])
    semantic = request.args.get("semantic", "false").lower() == "true"
    
    def make_like_clauses(term_list, joiner="AND"):
        clauses = []
        params = []
        for term in term_list:
            if not term: continue
            term_clean = term.replace("%", "").replace("_", "")
            if len(term_clean) < 2: continue
            clauses.append("(q.stem LIKE ? OR e.explanation_text LIKE ? OR q.area LIKE ? OR q.subtema LIKE ?)")
            like_val = f"%{term_clean}%"
            params.extend([like_val, like_val, like_val, like_val])
        if not clauses:
            return "", []
        return f"({f' {joiner} '.join(clauses)})", params

    if semantic:
        from .ai import expand_search_query
        expanded_terms = expand_search_query(q)
        where_sql, params = make_like_clauses(expanded_terms, "OR")
    else:
        terms = re.findall(r"\w+", q, flags=re.UNICODE)[:12]
        where_sql, params = make_like_clauses(terms, "AND")

    if not where_sql:
        return jsonify([])
    
    rows = db.execute(f"""
        SELECT q.id, q.institution_code, q.year, q.area, q.subtema, q.source_file, q.editorial_status,
               SUBSTR(q.stem, 1, 150) as stem_snippet,
               SUBSTR(e.explanation_text, 1, 150) as exp_snippet
        FROM questions q
        LEFT JOIN explanations e ON q.id = e.question_id
        WHERE {where_sql}
        LIMIT 50
    """, params).fetchall()
    
    out = []
    for row in rows:
        item = dict(row)
        item["is_autoral"] = bool(item.get("editorial_status") == "autoral" or (item.get("source_file") and "AUTORAL" in str(item.get("source_file")).upper()))
        item["stem_snippet"] = (item.get("stem_snippet") or "") + "..."
        item["exp_snippet"] = (item.get("exp_snippet") or "") + "..."
        out.append(item)
    return jsonify(out)


@bp.route("/meta")
def meta():
    # Preserva valores repetidos (ex.: institution=A&institution=B) e faz
    # consultas equivalentes compartilharem a mesma entrada de cache.
    normalized_args = tuple(sorted(
        (key, tuple(sorted(values)))
        for key, values in request.args.lists()
    ))
    cache_key = (g.user_id, normalized_args)
    cached = meta_cache.get(cache_key)
    if cached:
        return jsonify(cached)

    db = get_db()
    clauses, params = question_filter_clauses(request.args)
    
    # We must replace q. with empty or alias questions as q
    # Because question_filter_clauses assumes "q.institution_code" etc
    where = " AND ".join(clauses)

    from werkzeug.datastructures import MultiDict
    args_no_subtema = MultiDict((k, v) for k, v in request.args.items(multi=True) if k != 'subtema')
    clauses_no_subtema, params_no_subtema = question_filter_clauses(args_no_subtema)
    where_no_subtema = " AND ".join(clauses_no_subtema)

    answered_params = list(params)
    answered_params.append(g.user_id)

    queries = [
        (f"SELECT q.institution_code, q.institution_label, COUNT(*) n FROM questions q WHERE {where} GROUP BY q.institution_code ORDER BY n DESC", params),
        (f"SELECT DISTINCT q.year FROM questions q WHERE q.year IS NOT NULL AND {where} ORDER BY q.year", params),
        (f"SELECT q.area, COUNT(*) n FROM questions q WHERE q.area IS NOT NULL AND q.area != '' AND {where} GROUP BY q.area ORDER BY n DESC", params),
        (f"SELECT q.subtema, COUNT(*) n FROM questions q WHERE q.subtema IS NOT NULL AND q.subtema != '' AND {where_no_subtema} GROUP BY q.subtema ORDER BY n DESC LIMIT 300", params_no_subtema),
        (f"SELECT q.topic, COUNT(*) n FROM questions q WHERE q.topic IS NOT NULL AND q.topic != '' AND {where_no_subtema} GROUP BY q.topic ORDER BY n DESC LIMIT 500", params_no_subtema),
        (f"SELECT COUNT(*) n FROM questions q WHERE {where}", params),
        (f"SELECT COUNT(DISTINCT q.id) n FROM questions q WHERE {where} AND q.id IN (SELECT question_id FROM attempts WHERE user_id = ?)", answered_params)
    ]

    if hasattr(db, "batch"):
        results = db.batch(queries)
        institutions = results[0].fetchall()
        years = results[1].fetchall()
        areas = results[2].fetchall()
        subtemas = results[3].fetchall()
        topics = results[4].fetchall()
        total = results[5].fetchone()["n"]
        answered = results[6].fetchone()["n"]
    else:
        institutions = db.execute(queries[0][0], queries[0][1]).fetchall()
        years = db.execute(queries[1][0], queries[1][1]).fetchall()
        areas = db.execute(queries[2][0], queries[2][1]).fetchall()
        subtemas = db.execute(queries[3][0], queries[3][1]).fetchall()
        topics = db.execute(queries[4][0], queries[4][1]).fetchall()
        total = db.execute(queries[5][0], queries[5][1]).fetchone()["n"]
        answered = db.execute(queries[6][0], queries[6][1]).fetchone()["n"]
    
    result = {
        "institutions": [dict(r) for r in institutions],
        "years": [r["year"] for r in years],
        "sources": [],
        "areas": [dict(r) for r in areas],
        "specialties": [],
        "subtemas": [dict(r) for r in subtemas],
        "topics": [dict(r) for r in topics],
        "total_questions": total,
        "answered_questions": answered,
    }
    
    meta_cache.set(cache_key, result)
    return jsonify(result)


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
    if request.args.get("mode") == "adaptive":
        return jsonify(rank_adaptive_candidates(db, g.user_id, where, params, limit))
    ids = _sample_ids(db, where, params, limit)
    if not ids:
        return jsonify([])
    placeholders = ",".join("?" * len(ids))
    rows = db.execute(
        f"""SELECT q.id, q.source_file, q.source_number, q.year, q.institution_code,
                   q.institution_label, q.topic, q.area, q.subtema, q.editorial_status
            FROM questions q WHERE q.id IN ({placeholders})""",
        ids,
    ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["is_autoral"] = bool(d.get("editorial_status") == "autoral" or (d.get("source_file") and "AUTORAL" in d.get("source_file").upper()))
        out.append(d)
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
    queries = [
        ("SELECT * FROM questions WHERE id = ?", (qid,)),
        ("SELECT letter, text FROM alternatives WHERE question_id = ? ORDER BY letter", (qid,)),
        ("SELECT file_path FROM question_images WHERE question_id = ? ORDER BY order_index", (qid,)),
        ("SELECT selected_letter, is_correct FROM attempts WHERE question_id = ? AND user_id = ? ORDER BY id DESC LIMIT 1", (qid, g.user_id)),
        ("SELECT COUNT(*) as n FROM attempts WHERE question_id = ? AND is_correct = 0 AND user_id = ?", (qid, g.user_id)),
        ("SELECT 1 FROM favorites WHERE question_id = ? AND user_id = ?", (qid, g.user_id))
    ]
    
    if hasattr(db, "batch"):
        res = db.batch(queries)
        q = res[0].fetchone()
        alts = res[1].fetchall()
        imgs = res[2].fetchall()
        last_attempt = res[3].fetchone()
        times_wrong = res[4].fetchone()["n"]
        is_favorite = res[5].fetchone()
    else:
        q = db.execute(queries[0][0], queries[0][1]).fetchone()
        alts = db.execute(queries[1][0], queries[1][1]).fetchall()
        imgs = db.execute(queries[2][0], queries[2][1]).fetchall()
        last_attempt = db.execute(queries[3][0], queries[3][1]).fetchone()
        times_wrong = db.execute(queries[4][0], queries[4][1]).fetchone()["n"]
        is_favorite = db.execute(queries[5][0], queries[5][1]).fetchone()
        
    if not q:
        return jsonify({"error": "not found"}), 404
    q = dict(q)
        
    cc = None
    if q.get("clinical_case_id"):
        cc_row = db.execute("SELECT stem, images FROM clinical_cases WHERE id = ?", (q["clinical_case_id"],)).fetchone()
        if cc_row:
            cc = {
                "stem": cc_row["stem"],
                "images": json.loads(cc_row["images"]) if cc_row["images"] else []
            }

    return jsonify({
        "id": q["id"], "source_file": q["source_file"], "source_number": q["source_number"],
        "year": q["year"], "institution_code": q["institution_code"],
        "institution_label": q["institution_label"], "topic": q["topic"],
        "area": q["area"], "subtema": q["subtema"], "stem": q["stem"],
        "is_autoral": bool(q.get("editorial_status") == "autoral" or (q.get("source_file") and "AUTORAL" in str(q.get("source_file")).upper())),
        "is_verified": bool(q.get("is_verified", 0)),
        "last_updated_at": q.get("last_updated_at"),
        "technical_note": q.get("technical_note"),
        "medical_references": q.get("medical_references"),
        "clinical_case": cc,
        "usp_macro": q.get("usp_macro"),
        "usp_micro": q.get("usp_micro"),
        "alternatives": [dict(a) for a in alts],
        "images": [i["file_path"] for i in imgs],
        "already_answered": dict(last_attempt) if last_attempt else None,
        "is_favorite": bool(is_favorite),
        "times_wrong": times_wrong,
    })


@bp.route("/questions/<int:qid>/attempt", methods=["POST"])
def submit_attempt(qid):
    db = get_db()
    raw_payload = request.get_data()

    cached_resp, err_resp, lease_token = reserve_idempotency(db, g.user_id, request.path, request.method, raw_payload)
    if cached_resp is not None:
        return cached_resp
    if err_resp is not None:
        return err_resp

    try:
        try:
            payload = AttemptIn.model_validate(request.get_json(force=True) or {})
        except ValidationError as e:
            if lease_token:
                fail_idempotency(db, g.user_id, lease_token)
            return jsonify({"error": "invalid input", "details": validation_errors(e)}), 400

        q = db.execute("SELECT correct_letter FROM questions WHERE id = ?", (qid,)).fetchone()
        if not q:
            if lease_token:
                fail_idempotency(db, g.user_id, lease_token)
            return jsonify({"error": "not found"}), 404

        with db_transaction(db, immediate=True):
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

            exp = db.execute("SELECT explanation_text FROM explanations WHERE question_id = ?", (qid,)).fetchone()
            resp_data = {
                "is_correct": bool(is_correct),
                "correct_letter": q["correct_letter"],
                "explanation": exp["explanation_text"] if exp else None,
                "next_review_date": next_review,
            }

            if lease_token:
                complete_idempotency(db, g.user_id, 200, resp_data, lease_token)

        invalidate_user_caches(g.user_id)
        return jsonify(resp_data)
    except Exception:
        if lease_token:
            fail_idempotency(db, g.user_id, lease_token)
        raise


@bp.route("/questions/<int:qid>/review", methods=["POST"])
def review_fsrs(qid):
    db = get_db()
    raw_payload = request.get_data()

    cached_resp, err_resp, lease_token = reserve_idempotency(db, g.user_id, request.path, request.method, raw_payload)
    if cached_resp is not None:
        return cached_resp
    if err_resp is not None:
        return err_resp

    try:
        try:
            data = ReviewIn.model_validate(request.get_json(force=True) or {})
        except ValidationError as e:
            if lease_token:
                fail_idempotency(db, g.user_id, lease_token)
            return jsonify({"error": "invalid input", "details": validation_errors(e)}), 400
        confidence = data.confidence

        with db_transaction(db, immediate=True):
            last_attempt = db.execute(
                "SELECT id, is_correct, confidence FROM attempts WHERE question_id = ? AND user_id = ? ORDER BY id DESC LIMIT 1",
                (qid, g.user_id)
            ).fetchone()
            if not last_attempt:
                resp_data = {"error": "No attempt found"}
                if lease_token:
                    complete_idempotency(db, g.user_id, 400, resp_data, lease_token)
                return jsonify(resp_data), 400

            db.execute(
                "UPDATE attempts SET confidence = ? WHERE id = ?",
                (confidence, last_attempt["id"])
            )

            # Evita avanço duplo no FSRS se o cartão já havia sido classificado antes nesta tentativa
            if last_attempt["confidence"] != "defer" and last_attempt["confidence"] is not None:
                resp_data = {"success": True, "warning": "Confiança atualizada, mas FSRS retido na primeira impressão para evitar avanço duplo."}
                if lease_token:
                    complete_idempotency(db, g.user_id, 200, resp_data, lease_token)
                return jsonify(resp_data)

            sr = db.execute("SELECT fsrs_card FROM spaced_repetition WHERE question_id = ? AND user_id = ?", (qid, g.user_id)).fetchone()
            card_json, next_review = srs.review(sr["fsrs_card"] if sr else None, last_attempt["is_correct"], confidence)
            db.execute("""
                INSERT INTO spaced_repetition (question_id, next_review_date, fsrs_card, user_id)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(question_id, user_id) DO UPDATE SET
                    next_review_date = excluded.next_review_date, fsrs_card = excluded.fsrs_card
            """, (qid, next_review, card_json, g.user_id))

            resp_data = {"success": True, "next_review_date": next_review}
            if lease_token:
                complete_idempotency(db, g.user_id, 200, resp_data, lease_token)

        invalidate_user_caches(g.user_id)
        return jsonify(resp_data)
    except Exception:
        if lease_token:
            fail_idempotency(db, g.user_id, lease_token)
        raise

@bp.route("/attempt/batch", methods=["POST"])
def submit_attempt_batch():
    db = get_db()
    raw_payload = request.get_data()

    cached_resp, err_resp, lease_token = reserve_idempotency(db, g.user_id, request.path, request.method, raw_payload)
    if cached_resp is not None:
        return cached_resp
    if err_resp is not None:
        return err_resp

    try:
        try:
            payload = BatchAttemptIn.model_validate(request.get_json(force=True) or {})
        except ValidationError as e:
            if lease_token:
                fail_idempotency(db, g.user_id, lease_token)
            return jsonify({"error": "invalid input", "details": validation_errors(e)}), 400

        results = []
        answered_at = datetime.now(timezone.utc).isoformat()

        # To avoid many SELECTs, get all correct_letters and explanations at once
        q_ids = [item.question_id for item in payload.attempts]
        if not q_ids:
            resp_data = {"results": []}
            with db_transaction(db, immediate=True):
                if lease_token:
                    complete_idempotency(db, g.user_id, 200, resp_data, lease_token)
            return jsonify(resp_data)

        CHUNK_SIZE = 500
        q_map = {}
        exp_map = {}

        for i in range(0, len(q_ids), CHUNK_SIZE):
            chunk = q_ids[i:i + CHUNK_SIZE]
            placeholders = ",".join("?" * len(chunk))
            
            qs = db.execute(f"SELECT id, correct_letter FROM questions WHERE id IN ({placeholders})", chunk).fetchall()
            for q in qs:
                q_map[q["id"]] = q["correct_letter"]
                
            exps = db.execute(f"SELECT question_id, explanation_text FROM explanations WHERE question_id IN ({placeholders})", chunk).fetchall()
            for e in exps:
                exp_map[e["question_id"]] = e["explanation_text"]
                
        with db_transaction(db, immediate=True):
            # Read FSRS cards after acquiring the write transaction. Otherwise
            # a concurrent batch can advance a card between this read and UPSERT.
            srs_map = {}
            for i in range(0, len(q_ids), CHUNK_SIZE):
                chunk = q_ids[i:i + CHUNK_SIZE]
                placeholders = ",".join("?" * len(chunk))
                chunk_args = [*chunk, g.user_id]
                srs_data = db.execute(
                    f"SELECT question_id, fsrs_card FROM spaced_repetition WHERE question_id IN ({placeholders}) AND user_id = ?",
                    chunk_args
                ).fetchall()
                for card in srs_data:
                    srs_map[card["question_id"]] = card["fsrs_card"]

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

            resp_data = {"results": results}
            if lease_token:
                complete_idempotency(db, g.user_id, 200, resp_data, lease_token)

        invalidate_user_caches(g.user_id)
        return jsonify(resp_data)
    except Exception:
        if lease_token:
            fail_idempotency(db, g.user_id, lease_token)
        raise


@bp.route("/questions/<int:qid>/favorite", methods=["POST"])
def toggle_favorite(qid):
    db = get_db()
    raw_payload = request.get_data()

    cached_resp, err_resp, lease_token = reserve_idempotency(db, g.user_id, request.path, request.method, raw_payload)
    if cached_resp is not None:
        return cached_resp
    if err_resp is not None:
        return err_resp

    try:
        try:
            data = FavoriteIn.model_validate(request.get_json(silent=True) or {})
        except ValidationError as e:
            if lease_token:
                fail_idempotency(db, g.user_id, lease_token)
            return jsonify({"error": "invalid input", "details": validation_errors(e)}), 400
        target_fav = data.is_favorite

        with db_transaction(db, immediate=True):
            if target_fav is not None:
                if target_fav:
                    db.execute("INSERT OR IGNORE INTO favorites (question_id, user_id) VALUES (?, ?)", (qid, g.user_id))
                    is_fav = True
                else:
                    db.execute("DELETE FROM favorites WHERE question_id = ? AND user_id = ?", (qid, g.user_id))
                    is_fav = False
            else:
                fav = db.execute("SELECT 1 FROM favorites WHERE question_id = ? AND user_id = ?", (qid, g.user_id)).fetchone()
                if fav:
                    db.execute("DELETE FROM favorites WHERE question_id = ? AND user_id = ?", (qid, g.user_id))
                    is_fav = False
                else:
                    db.execute("INSERT OR IGNORE INTO favorites (question_id, user_id) VALUES (?, ?)", (qid, g.user_id))
                    is_fav = True

            resp_data = {"success": True, "is_favorite": is_fav}
            if lease_token:
                complete_idempotency(db, g.user_id, 200, resp_data, lease_token)

        invalidate_user_caches(g.user_id)
        return jsonify(resp_data)
    except Exception:
        if lease_token:
            fail_idempotency(db, g.user_id, lease_token)
        raise


@bp.route("/questions/batch", methods=["POST"])
def question_batch_detail():
    """Retorna detalhes completos de múltiplas questões em uma única requisição.
    
    Aceita {"ids": [1, 2, ...]} com no máximo 200 IDs.
    Substitui até 120 chamadas individuais GET /questions/:id no simulado.
    """
    try:
        data = QuestionBatchIn.model_validate(request.get_json(force=True) or {})
    except ValidationError as e:
        return jsonify({"error": "invalid input", "details": validation_errors(e)}), 400
    ids = data.ids
    force_4_options = data.force_4_options

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

    cc_map = {}
    cc_ids = list({q["clinical_case_id"] for q in q_map.values() if q.get("clinical_case_id")})
    if cc_ids:
        ph_cc = ",".join("?" * len(cc_ids))
        for r in db.execute(f"SELECT id, stem, images FROM clinical_cases WHERE id IN ({ph_cc})", cc_ids).fetchall():
            cc_map[r["id"]] = {
                "stem": r["stem"],
                "images": json.loads(r["images"]) if r["images"] else []
            }

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
            "is_autoral": bool(q.get("editorial_status") == "autoral" or (q.get("source_file") and "AUTORAL" in str(q.get("source_file")).upper())),
            "is_verified": bool(q.get("is_verified", 0)),
            "last_updated_at": q.get("last_updated_at"),
            "technical_note": q.get("technical_note"),
            "medical_references": q.get("medical_references"),
            "clinical_case": cc_map.get(q.get("clinical_case_id")),
            "usp_macro": q.get("usp_macro"),
            "usp_micro": q.get("usp_micro"),
            "alternatives": alts,
            "images": img_map.get(qid, []),
            "already_answered": attempt_map.get(qid),
            "is_favorite": qid in fav_set,
            "times_wrong": wrong_map.get(qid, 0),
        })

    return jsonify({"questions": out})


@bp.route("/questions/<int:question_id>/ask_ai", methods=["POST"])
def ask_question_ai(question_id):
    db = get_db()
    q = db.execute("""
        SELECT q.id, q.stem, q.area, q.subtema, q.topic,
               e.explanation_text
        FROM questions q
        LEFT JOIN explanations e ON q.id = e.question_id
        WHERE q.id = ?
    """, (question_id,)).fetchone()
    
    if not q:
        return jsonify({"error": "Questão não encontrada"}), 404
        
    alts = db.execute("""
        SELECT letter, text, is_correct
        FROM alternatives
        WHERE question_id = ?
        ORDER BY letter
    """, (question_id,)).fetchall()
    
    alts_list = [{"letter": a["letter"], "text": a["text"], "is_correct": bool(a["is_correct"])} for a in alts]
    correct_alt = next((a for a in alts_list if a["is_correct"]), None)
    correct_letter = correct_alt["letter"] if correct_alt else ""
    correct_text = correct_alt["text"] if correct_alt else ""
    
    body = request.get_json(silent=True) or {}
    user_question = body.get("user_question", "")
    user_letter = body.get("user_letter", "")
    
    from .ai import ask_preceptor_ai
    result = ask_preceptor_ai(
        stem=q["stem"],
        alternatives=alts_list,
        correct_letter=correct_letter,
        correct_text=correct_text,
        user_letter=user_letter,
        user_question=user_question,
        explanation=q["explanation_text"] or "",
        area=q["area"] or "",
        subtema=q["subtema"] or q["topic"] or ""
    )
    
    return jsonify(result)


@bp.route("/ai/health", methods=["GET"])
def ai_health():
    from .gemini_pool import gemini_pool
    return jsonify(gemini_pool.health_check())


@bp.route("/ai/prescribe_study", methods=["POST"])
def prescribe_study():
    try:
        data = PrescribeStudyIn.model_validate(request.get_json(force=True) or {})
    except ValidationError as e:
        return jsonify({"error": "invalid input", "details": validation_errors(e)}), 400

    from .ai import generate_study_prescription
    result = generate_study_prescription(
        weak_topics=data.weak_topics,
        distractors=data.distractors,
        at_risk_topics=data.at_risk_topics,
        target_institution=data.target_institution
    )
    return jsonify(result)


@bp.route("/questions/<int:question_id>/synthesize_explanation", methods=["POST"])
def synthesize_explanation(question_id):
    try:
        data = SynthesizeExplanationIn.model_validate(request.get_json(force=True) or {})
    except ValidationError as e:
        return jsonify({"error": "invalid input", "details": validation_errors(e)}), 400

    db = get_db()
    q = db.execute("""
        SELECT q.id, q.stem, q.area, q.subtema, q.topic,
               e.explanation_text
        FROM questions q
        LEFT JOIN explanations e ON q.id = e.question_id
        WHERE q.id = ?
    """, (question_id,)).fetchone()

    if not q:
        return jsonify({"error": "Questão não encontrada"}), 404

    # Se já possui explicação e não é para forçar regeneração, retorna a existente
    if q["explanation_text"] and not data.force_regenerate:
        return jsonify({
            "question_id": question_id,
            "explanation_text": q["explanation_text"],
            "source": "cached_db"
        })

    alts = db.execute("""
        SELECT letter, text, is_correct
        FROM alternatives
        WHERE question_id = ?
        ORDER BY letter
    """, (question_id,)).fetchall()

    alts_list = [{"letter": a["letter"], "text": a["text"], "is_correct": bool(a["is_correct"])} for a in alts]
    correct_alt = next((a for a in alts_list if a["is_correct"]), None)
    correct_letter = correct_alt["letter"] if correct_alt else ""
    correct_text = correct_alt["text"] if correct_alt else ""

    from .ai import synthesize_question_explanation
    result = synthesize_question_explanation(
        stem=q["stem"],
        alternatives=alts_list,
        correct_letter=correct_letter,
        correct_text=correct_text,
        area=q["area"] or "",
        subtema=q["subtema"] or q["topic"] or ""
    )

    # Persiste na tabela explanations se sintetizado com sucesso
    with db_transaction(db, immediate=True):
        existing_exp = db.execute("SELECT question_id FROM explanations WHERE question_id = ?", (question_id,)).fetchone()
        if existing_exp:
            db.execute("""
                UPDATE explanations
                SET explanation_text = ?
                WHERE question_id = ?
            """, (result.get("explanation_text", ""), question_id))
        else:
            db.execute("""
                INSERT INTO explanations (question_id, explanation_text)
                VALUES (?, ?)
            """, (question_id, result.get("explanation_text", "")))

    invalidate_user_caches(g.user_id)

    return jsonify({
        "question_id": question_id,
        "explanation_text": result.get("explanation_text"),
        "medical_references": result.get("medical_references"),
        "source": result.get("source"),
        "model": result.get("model")
    })


@bp.route("/images/<path:filename>")
def serve_image(filename):
    import os

    from flask import send_from_directory
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    static_dir = os.path.join(backend_dir, "static")
    
    # Check if direct file exists
    if os.path.exists(os.path.join(static_dir, filename)):
        return send_from_directory(static_dir, filename)
    # Check if inside static/images/
    if os.path.exists(os.path.join(static_dir, "images", filename)):
        return send_from_directory(os.path.join(static_dir, "images"), filename)
    return send_from_directory(static_dir, filename)
