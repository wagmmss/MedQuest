import json
import logging
import re
from datetime import datetime, timedelta, timezone

from flask import Blueprint, Response, g, jsonify, request

from . import srs
from .ai import generate_cloze_flashcard
from .anki import parse_apkg_bytes, parse_anki_text
from .db import db_transaction, get_db
from .observability import record_domain_event
from .questions import invalidate_user_caches
from .schemas import (
    AnkiDeleteDeckIn,
    AnkiImportBatchIn,
    AnkiSyncStateIn,
    FlashcardBatchIn,
    FlashcardGenerateIn,
    FlashcardPreviewIn,
    FlashcardReportIn,
    FlashcardReviewIn,
    FlashcardSaveIn,
    ValidationError,
    validation_errors,
)

bp = Blueprint("flashcards", __name__)
logger = logging.getLogger(__name__)

@bp.route("/flashcards/generate", methods=["POST"])
def generate():
    try:
        data = FlashcardGenerateIn.model_validate(request.get_json(force=True) or {})
    except ValidationError as e:
        return jsonify({"error": "invalid input", "details": validation_errors(e)}), 400
    question_id = data.question_id
    wrong_letter = data.wrong_letter.upper()

    db = get_db()
    
    q = db.execute("SELECT stem, correct_letter, area, subtema, topic FROM questions WHERE id = ?", (question_id,)).fetchone()
    if not q:
        return jsonify({"error": "Questao nao encontrada."}), 404
        
    correct_alt = db.execute("SELECT text FROM alternatives WHERE question_id = ? AND letter = ?", (question_id, q["correct_letter"])).fetchone()
    wrong_alt = None
    if wrong_letter:
        wrong_alt = db.execute("SELECT text FROM alternatives WHERE question_id = ? AND letter = ?", (question_id, wrong_letter)).fetchone()
    exp = db.execute("SELECT explanation_text FROM explanations WHERE question_id = ?", (question_id,)).fetchone()
    
    if not correct_alt:
        return jsonify({"error": "Alternativa correta nao encontrada."}), 404

    card_data = generate_cloze_flashcard(
        stem=q["stem"], 
        correct_text=correct_alt["text"], 
        wrong_text=wrong_alt["text"] if wrong_alt else "", 
        explanation=exp["explanation_text"] if exp else "",
        area=q["area"] or "",
        subtema=q["subtema"] or "",
        topic=q["topic"] or "",
        correct_letter=q["correct_letter"],
        wrong_letter=wrong_letter
    )

    now = datetime.now(timezone.utc).isoformat()
    with db_transaction(db, immediate=True):
        existing = db.execute("SELECT id FROM flashcards WHERE question_id = ? AND user_id = ?", (question_id, g.user_id)).fetchone()
        if existing:
            db.execute("""
                UPDATE flashcards
                SET front = ?, back = ?, source_context = ?, next_review_date = ?
                WHERE id = ? AND user_id = ?
            """, (card_data.get("front", ""), card_data.get("back", ""), card_data.get("context", ""), now, existing["id"], g.user_id))
            card_id = existing["id"]
        else:
            cursor = db.execute("""
                INSERT INTO flashcards (question_id, front, back, created_at, next_review_date, fsrs_card, user_id, source_context, is_ai_generated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (question_id, card_data.get("front", ""), card_data.get("back", ""), now, now, None, g.user_id, card_data.get("context", "")))
            card_id = cursor.lastrowid
        
    invalidate_user_caches(g.user_id)

    return jsonify({
        "id": card_id,
        "question_id": question_id,
        "front": card_data.get("front", ""),
        "back": card_data.get("back", ""),
        "context": card_data.get("context", "")
    })

@bp.route("/flashcards/preview", methods=["POST"])
def preview():
    try:
        data = FlashcardPreviewIn.model_validate(request.get_json(force=True) or {})
    except ValidationError as e:
        return jsonify({"error": "invalid input", "details": validation_errors(e)}), 400
    question_id = data.question_id
    wrong_letter = data.wrong_letter.upper()

    db = get_db()
    
    q = db.execute("SELECT stem, correct_letter, area, subtema, topic FROM questions WHERE id = ?", (question_id,)).fetchone()
    if not q:
        return jsonify({"error": "Questao nao encontrada."}), 404
        
    correct_alt = db.execute("SELECT text FROM alternatives WHERE question_id = ? AND letter = ?", (question_id, q["correct_letter"])).fetchone()
    
    wrong_alt = None
    if wrong_letter:
        wrong_alt = db.execute("SELECT text FROM alternatives WHERE question_id = ? AND letter = ?", (question_id, wrong_letter)).fetchone()
        
    exp = db.execute("SELECT explanation_text FROM explanations WHERE question_id = ?", (question_id,)).fetchone()
    
    if not correct_alt:
        return jsonify({"error": "Alternativa correta nao encontrada."}), 404

    card_data = generate_cloze_flashcard(
        stem=q["stem"], 
        correct_text=correct_alt["text"], 
        wrong_text=wrong_alt["text"] if wrong_alt else "", 
        explanation=exp["explanation_text"] if exp else "",
        area=q["area"] or "",
        subtema=q["subtema"] or "",
        topic=q["topic"] or "",
        correct_letter=q["correct_letter"],
        wrong_letter=wrong_letter
    )

    return jsonify({
        "question_id": question_id,
        "front": card_data.get("front", ""),
        "back": card_data.get("back", ""),
        "context": card_data.get("context", "")
    })


@bp.route("/flashcards/save", methods=["POST"])
def save():
    try:
        data = FlashcardSaveIn.model_validate(request.get_json(force=True) or {})
    except ValidationError as e:
        return jsonify({"error": "invalid input", "details": validation_errors(e)}), 400
    question_id = data.question_id
    front = data.front
    back = data.back
    context = data.context

    db = get_db()
    now = datetime.now(timezone.utc).isoformat()
    
    with db_transaction(db, immediate=True):
        existing = db.execute("SELECT id FROM flashcards WHERE question_id = ? AND user_id = ?", (question_id, g.user_id)).fetchone()
        if existing:
            db.execute("""
                UPDATE flashcards
                SET front = ?, back = ?, source_context = ?, next_review_date = ?
                WHERE id = ? AND user_id = ?
            """, (front, back, context, now, existing["id"], g.user_id))
            card_id = existing["id"]
        else:
            cursor = db.execute("""
                INSERT INTO flashcards (question_id, front, back, created_at, next_review_date, fsrs_card, user_id, source_context, is_ai_generated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (question_id, front, back, now, now, None, g.user_id, context))
            card_id = cursor.lastrowid
        
    invalidate_user_caches(g.user_id)
    record_domain_event(
        "flashcard_created",
        user_id=g.user_id,
        question_id=question_id,
        flashcard_id=card_id,
    )
    return jsonify({
        "id": card_id,
        "question_id": question_id,
        "front": front,
        "back": back,
        "context": context
    })


@bp.route("/flashcards/generate-batch", methods=["POST"])
def generate_batch():
    try:
        payload = FlashcardBatchIn.model_validate(request.get_json(force=True) or {})
    except ValidationError as e:
        return jsonify({"error": "invalid input", "details": validation_errors(e)}), 400

    db = get_db()
    now = datetime.now(timezone.utc).isoformat()
    created_or_updated = []
    question_ids = [item.question_id for item in payload.items]
    placeholders = ",".join("?" * len(question_ids))
    question_rows = db.execute(
        f"""SELECT q.id, q.stem, q.correct_letter, q.area, q.subtema, q.topic,
                   e.explanation_text
            FROM questions q
            LEFT JOIN explanations e ON e.question_id = q.id
            WHERE q.id IN ({placeholders})""",
        question_ids,
    ).fetchall()
    question_map = {row["id"]: row for row in question_rows}
    alternative_rows = db.execute(
        f"SELECT question_id, letter, text FROM alternatives WHERE question_id IN ({placeholders})",
        question_ids,
    ).fetchall()
    alternative_map = {
        (row["question_id"], row["letter"].upper()): row["text"]
        for row in alternative_rows
    }

    # Do not hold a write transaction while waiting for an AI provider.
    prepared = []
    for item in payload.items:
        qid = item.question_id
        wrong_letter = item.wrong_letter.upper()
        q = question_map.get(qid)
        if not q:
            continue
        correct_text = alternative_map.get((qid, q["correct_letter"].upper()))
        wrong_text = alternative_map.get((qid, wrong_letter))
        if not correct_text or not wrong_text:
            continue
        prepared.append((qid, generate_cloze_flashcard(
            stem=q["stem"],
            correct_text=correct_text,
            wrong_text=wrong_text,
            explanation=q["explanation_text"] or "",
            area=q["area"] or "",
            subtema=q["subtema"] or "",
            topic=q["topic"] or "",
            correct_letter=q["correct_letter"],
            wrong_letter=wrong_letter,
        )))

    with db_transaction(db, immediate=True):
        existing_rows = db.execute(
            f"SELECT id, question_id FROM flashcards WHERE question_id IN ({placeholders}) AND user_id = ?",
            [*question_ids, g.user_id],
        ).fetchall()
        existing_map = {row["question_id"]: row["id"] for row in existing_rows}

        for qid, card_data in prepared:
            existing_id = existing_map.get(qid)
            if existing_id is not None:
                db.execute("""
                    UPDATE flashcards
                    SET front = ?, back = ?, source_context = ?, next_review_date = ?
                    WHERE id = ? AND user_id = ?
                """, (card_data.get("front", ""), card_data.get("back", ""), card_data.get("context", ""), now, existing_id, g.user_id))
                created_or_updated.append({
                    "id": existing_id,
                    "question_id": qid,
                    "front": card_data.get("front", ""),
                    "back": card_data.get("back", "")
                })
            else:
                cursor = db.execute("""
                    INSERT INTO flashcards (question_id, front, back, created_at, next_review_date, fsrs_card, user_id, source_context, is_ai_generated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                """, (qid, card_data.get("front", ""), card_data.get("back", ""), now, now, None, g.user_id, card_data.get("context", "")))
                created_or_updated.append({
                    "id": cursor.lastrowid,
                    "question_id": qid,
                    "front": card_data.get("front", ""),
                    "back": card_data.get("back", "")
                })

    invalidate_user_caches(g.user_id)
    for c in created_or_updated:
        record_domain_event(
            "flashcard_created",
            user_id=g.user_id,
            question_id=c["question_id"],
            flashcard_id=c["id"],
        )
    return jsonify({
        "success": True,
        "count": len(created_or_updated),
        "flashcards": created_or_updated
    })


def _bounded_int(value, default, minimum, maximum):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(parsed, maximum))


@bp.route("/flashcards/decks", methods=["GET"])
def get_decks():
    db = get_db()
    now = datetime.now(timezone.utc).isoformat()
    rows = db.execute("""
        SELECT COALESCE(NULLIF(TRIM(f.deck_name), ''), 'Geral') AS deck_name,
               COALESCE(NULLIF(TRIM(f.source_type), ''), 'medquest') AS source_type,
               COUNT(*) AS total_cards,
               SUM(CASE WHEN f.next_review_date <= ? THEN 1 ELSE 0 END) AS due_cards
        FROM flashcards f
        WHERE f.user_id = ? AND (f.report_status IS NULL OR TRIM(f.report_status) = '')
        GROUP BY COALESCE(NULLIF(TRIM(f.deck_name), ''), 'Geral')
        ORDER BY deck_name ASC
    """, (now, g.user_id)).fetchall()

    decks = []
    total_all = 0
    due_all = 0
    for r in rows:
        t = r["total_cards"] or 0
        d = r["due_cards"] or 0
        total_all += t
        due_all += d
        decks.append({
            "name": r["deck_name"],
            "source_type": r["source_type"],
            "total_cards": t,
            "due_cards": d,
        })

    return jsonify({
        "total_cards": total_all,
        "due_cards": due_all,
        "decks": decks,
    })


@bp.route("/flashcards/import/file", methods=["POST"])
def import_anki_file():
    if "file" not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado no formulário ('file')."}), 400
    file = request.files["file"]
    if not file or not file.filename:
        return jsonify({"error": "Nome de arquivo inválido."}), 400

    target_deck = request.form.get("deck_name", "").strip() or "Anki"
    content = file.read()
    if not content:
        return jsonify({"error": "Arquivo enviado está vazio."}), 400

    filename_lower = file.filename.lower()
    try:
        if filename_lower.endswith((".apkg", ".colpkg")):
            cards = parse_apkg_bytes(content, fallback_deck_name=target_deck)
        else:
            text_str = content.decode("utf-8", errors="replace")
            cards = parse_anki_text(text_str, default_deck_name=target_deck)
    except Exception as e:
        logger.exception("Falha ao analisar arquivo Anki %s: %s", file.filename, e)
        return jsonify({"error": f"Falha ao ler arquivo do Anki: {e}"}), 400

    if not cards:
        return jsonify({"error": "Nenhum flashcard válido foi encontrado no arquivo."}), 400

    db = get_db()
    now = datetime.now(timezone.utc).isoformat()
    imported_count = 0
    unique_decks = set()

    with db_transaction(db, immediate=True):
        for c in cards:
            c_deck = (target_deck if target_deck != "Anki" and target_deck else c.get("deck_name") or "Anki").strip()
            unique_decks.add(c_deck)
            c_tags = c.get("tags") or []
            c_tags_json = json.dumps(c_tags)
            anki_nid = c.get("anki_nid")
            source_type = c.get("source_type") or ("anki_apkg" if filename_lower.endswith((".apkg", ".colpkg")) else "anki_txt")
            source_context = c.get("source_context") or f"Anki: {c_deck}"

            existing = None
            if anki_nid is not None:
                existing = db.execute(
                    "SELECT id FROM flashcards WHERE user_id = ? AND anki_nid = ?",
                    (g.user_id, anki_nid),
                ).fetchone()

            if existing:
                db.execute("""
                    UPDATE flashcards
                    SET front = ?, back = ?, deck_name = ?, tags = ?, source_context = ?, source_type = ?
                    WHERE id = ? AND user_id = ?
                """, (c["front"], c["back"], c_deck, c_tags_json, source_context, source_type, existing["id"], g.user_id))
            else:
                db.execute("""
                    INSERT INTO flashcards (question_id, front, back, created_at, next_review_date, fsrs_card, user_id, source_context, is_ai_generated, deck_name, tags, source_type, anki_nid)
                    VALUES (NULL, ?, ?, ?, ?, NULL, ?, ?, 0, ?, ?, ?, ?)
                """, (c["front"], c["back"], now, now, g.user_id, source_context, c_deck, c_tags_json, source_type, anki_nid))
                imported_count += 1

    invalidate_user_caches(g.user_id)
    record_domain_event(
        "anki_cards_imported",
        user_id=g.user_id,
        count=len(cards),
        new_cards=imported_count,
        decks=list(unique_decks),
    )

    return jsonify({
        "success": True,
        "total_imported": len(cards),
        "new_cards": imported_count,
        "decks": sorted(list(unique_decks)),
    })


@bp.route("/flashcards/import/batch", methods=["POST"])
def import_anki_batch():
    try:
        data = AnkiImportBatchIn.model_validate(request.get_json(force=True) or {})
    except ValidationError as e:
        return jsonify({"error": "invalid input", "details": validation_errors(e)}), 400

    db = get_db()
    now = datetime.now(timezone.utc).isoformat()
    imported_count = 0
    unique_decks = set()

    with db_transaction(db, immediate=True):
        for c in data.cards:
            c_deck = (data.deck_name or c.deck_name or "Anki").strip()
            unique_decks.add(c_deck)
            c_tags_json = json.dumps(c.tags or [])
            source_context = c.source_context or f"Anki: {c_deck}"

            existing = None
            if c.anki_nid is not None:
                existing = db.execute(
                    "SELECT id FROM flashcards WHERE user_id = ? AND anki_nid = ?",
                    (g.user_id, c.anki_nid),
                ).fetchone()

            if existing:
                db.execute("""
                    UPDATE flashcards
                    SET front = ?, back = ?, deck_name = ?, tags = ?, source_context = ?, source_type = 'anki_connect', anki_cid = ?
                    WHERE id = ? AND user_id = ?
                """, (c.front, c.back, c_deck, c_tags_json, source_context, c.anki_cid, existing["id"], g.user_id))
            else:
                db.execute("""
                    INSERT INTO flashcards (question_id, front, back, created_at, next_review_date, fsrs_card, user_id, source_context, is_ai_generated, deck_name, tags, source_type, anki_nid, anki_cid)
                    VALUES (NULL, ?, ?, ?, ?, NULL, ?, ?, 0, ?, ?, 'anki_connect', ?, ?)
                """, (c.front, c.back, now, now, g.user_id, source_context, c_deck, c_tags_json, c.anki_nid, c.anki_cid))
                imported_count += 1

    invalidate_user_caches(g.user_id)
    record_domain_event(
        "anki_batch_imported",
        user_id=g.user_id,
        count=len(data.cards),
        new_cards=imported_count,
        decks=list(unique_decks),
    )

    return jsonify({
        "success": True,
        "total_imported": len(data.cards),
        "new_cards": imported_count,
        "decks": sorted(list(unique_decks)),
    })


@bp.route("/flashcards/anki/sync-state", methods=["POST"])
def sync_anki_scheduling_state():
    """Aplica no MedQuest a agenda calculada pelo Anki local."""
    try:
        payload = AnkiSyncStateIn.model_validate(request.get_json(force=True) or {})
    except ValidationError as e:
        return jsonify({"error": "invalid input", "details": validation_errors(e)}), 400

    db = get_db()
    now = datetime.now(timezone.utc)
    updated = 0
    with db_transaction(db, immediate=True):
        for item in payload.cards:
            row = db.execute(
                "SELECT id FROM flashcards WHERE user_id = ? AND anki_cid = ?",
                (g.user_id, item.anki_cid),
            ).fetchone()
            if not row and item.anki_nid is not None:
                row = db.execute(
                    "SELECT id FROM flashcards WHERE user_id = ? AND anki_nid = ?",
                    (g.user_id, item.anki_nid),
                ).fetchone()
            if not row:
                continue

            # Anki usa segundos negativos durante aprendizagem e dias positivos
            # para revisão. Assim a fila do MedQuest passa a refletir a agenda
            # do Anki sem o servidor acessar a máquina local.
            next_due = now + (
                timedelta(seconds=abs(item.interval))
                if item.interval < 0
                else timedelta(days=item.interval)
            )
            db.execute(
                """UPDATE flashcards
                   SET anki_cid = ?, anki_reps = ?, anki_lapses = ?,
                       anki_synced_at = ?, next_review_date = ?
                   WHERE id = ? AND user_id = ?""",
                (item.anki_cid, item.reps, item.lapses, now.isoformat(), next_due.isoformat(), row["id"], g.user_id),
            )
            updated += 1

    invalidate_user_caches(g.user_id)
    return jsonify({"success": True, "updated": updated})


@bp.route("/flashcards/deck", methods=["DELETE"])
def delete_deck():
    try:
        data = AnkiDeleteDeckIn.model_validate(request.get_json(force=True) or {})
    except ValidationError as e:
        return jsonify({"error": "invalid input", "details": validation_errors(e)}), 400

    db = get_db()
    with db_transaction(db, immediate=True):
        cursor = db.execute(
            "DELETE FROM flashcards WHERE user_id = ? AND deck_name = ?",
            (g.user_id, data.deck_name),
        )
        deleted_count = cursor.rowcount

    invalidate_user_caches(g.user_id)
    return jsonify({
        "success": True,
        "deck_name": data.deck_name,
        "deleted_count": deleted_count,
    })


@bp.route("/flashcards/review", methods=["GET"])
def get_due_flashcards():
    db = get_db()
    now = datetime.now(timezone.utc).isoformat()
    include_all = request.args.get("all", "false").lower() == "true"
    scope = request.args.get("scope", "due")
    limit = _bounded_int(request.args.get("limit"), 50, 1, 100)
    deck = request.args.get("deck")

    params = [g.user_id]
    deck_clause = ""
    if deck and deck.lower() != "all":
        deck_clause = " AND f.deck_name = ?"
        params.append(deck)

    if include_all:
        sql = f"""
            SELECT f.id, f.question_id, f.front, f.back, f.next_review_date,
                   f.source_context, f.is_ai_generated, f.deck_name, f.tags, f.source_type, f.anki_nid, f.anki_cid,
                   q.stem, q.area, q.subtema
            FROM flashcards f LEFT JOIN questions q ON f.question_id = q.id
            WHERE f.user_id = ? AND (f.report_status IS NULL OR TRIM(f.report_status) = ''){deck_clause}
            ORDER BY f.next_review_date ASC LIMIT ?
        """
        params.append(limit)
    elif scope == "upcoming":
        sql = f"""
            SELECT f.id, f.question_id, f.front, f.back, f.next_review_date,
                   f.source_context, f.is_ai_generated, f.deck_name, f.tags, f.source_type, f.anki_nid, f.anki_cid,
                   q.stem, q.area, q.subtema
            FROM flashcards f LEFT JOIN questions q ON f.question_id = q.id
            WHERE f.user_id = ? AND f.next_review_date > ?
              AND (f.report_status IS NULL OR TRIM(f.report_status) = ''){deck_clause}
            ORDER BY f.next_review_date ASC LIMIT ?
        """
        params.insert(1, now)
        params.append(limit)
    else:
        sql = f"""
            SELECT f.id, f.question_id, f.front, f.back, f.next_review_date,
                   f.source_context, f.is_ai_generated, f.deck_name, f.tags, f.source_type, f.anki_nid, f.anki_cid,
                   q.stem, q.area, q.subtema
            FROM flashcards f LEFT JOIN questions q ON f.question_id = q.id
            WHERE f.next_review_date <= ? AND f.user_id = ?
              AND (f.report_status IS NULL OR TRIM(f.report_status) = ''){deck_clause}
            ORDER BY f.next_review_date ASC LIMIT ?
        """
        params.insert(0, now)
        params.append(limit)

    rows = db.execute(sql, tuple(params)).fetchall()

    items = []
    for r in rows:
        item = dict(r)
        front = item.get("front", "")
        back = item.get("back", "")
        stem = item.get("stem", "")
        tags_raw = item.get("tags")

        if tags_raw and isinstance(tags_raw, str):
            try:
                item["tags"] = json.loads(tags_raw)
            except Exception:
                item["tags"] = [t.strip() for t in tags_raw.split() if t.strip()]
        else:
            item["tags"] = tags_raw or []

        if not item.get("deck_name"):
            item["deck_name"] = "Geral"

        if (
            "A alternativa correta era" in front
            or front.startswith(("Neste caso clínico, em vez de", "Para este quadro clínico,"))
        ):
            cloze_match = re.search(r'{{c1::(.*?)}}', front)
            term = cloze_match.group(1) if cloze_match else ""
            term = re.sub(r'^[A-Ea-e][\)\.\:\-]\s*', '', term).strip()

            wrong_match = re.search(r"Você marcou\s*['\"](.*?)['\"]", back, re.IGNORECASE) or re.search(r"em vez de\s*[\"'](.*?)[\"']", back, re.IGNORECASE)
            wrong_term = re.sub(r'^[A-Ea-e][\)\.\:\-]\s*', '', wrong_match.group(1)).strip() if wrong_match else ""

            scenario = ""
            if stem:
                scenario = re.sub(r'\s+', ' ', stem.strip())
                end_match = re.search(
                    r'(?:Diante disso|Diante do exposto|Diante desse quadro|Nesse momento|Nesse caso|Considerando o caso|Em relação ao caso|Sobre o caso descrito|Qual a conduta|Qual o diagnóstico|Qual é o diagnóstico|A melhor conduta|A conduta mais adequada|O diagnóstico mais provável).*$',
                    scenario,
                    re.IGNORECASE
                )
                if end_match and end_match.start() > 30:
                    scenario = scenario[:end_match.start()].strip()
                scenario = re.sub(r'[\s,;:]+$', '', scenario).strip()
                if scenario and not scenario.endswith('.'):
                    scenario += '.'

            tag = "[Caso Clínico / Conduta]"
            item["front"] = (
                f"{tag} {scenario}\n\n👉 Diagnóstico / Conduta indicada: {{{{c1::{term}}}}}"
                if scenario and len(scenario) > 20
                else f"{tag}\n\n👉 Diagnóstico / Conduta indicada: {{{{c1::{term}}}}}"
            )
            if back.startswith(("Você marcou", "Alternativa correta:")):
                item["back"] = (
                    f"💡 Gabarito Oficial:\n{term}\n\n⚠️ Atenção ao distrator:\nA opção '{wrong_term}' é incorreta para este quadro clínico."
                    if wrong_term
                    else f"💡 Gabarito Oficial:\n{term}"
                )
        else:
            item["front"] = re.sub(r'{{c1::[A-Ea-e][\)\.\:\-]\s*(.*?)}}', r'{{c1::\1}}', front)

        items.append(item)

    return jsonify(items)


@bp.route("/flashcards/<int:fid>/review", methods=["POST"])
def review_flashcard(fid):
    try:
        data = FlashcardReviewIn.model_validate(request.get_json(force=True) or {})
    except ValidationError as e:
        return jsonify({"error": "invalid input", "details": validation_errors(e)}), 400
    confidence = data.confidence
        
    is_correct = 0 if confidence == "errei" else 1

    db = get_db()
    with db_transaction(db, immediate=True):
        card = db.execute("SELECT fsrs_card, anki_cid FROM flashcards WHERE id = ? AND user_id = ?", (fid, g.user_id)).fetchone()
        if not card:
            return jsonify({"error": "Flashcard nao encontrado."}), 404
        card_json, next_review = srs.review(card["fsrs_card"], is_correct, confidence if is_correct else "chutei")
        db.execute("""
            UPDATE flashcards 
            SET next_review_date = ?, fsrs_card = ? 
            WHERE id = ? AND user_id = ?
        """, (next_review, card_json, fid, g.user_id))

    invalidate_user_caches(g.user_id)
    record_domain_event(
        "flashcard_reviewed",
        user_id=g.user_id,
        flashcard_id=fid,
        confidence=confidence,
        is_correct=is_correct,
        next_review_date=next_review,
    )

    return jsonify({
        "id": fid,
        "next_review_date": next_review,
        "anki_cid": card["anki_cid"],
    })


@bp.route("/flashcards/<int:fid>/report", methods=["POST"])
def report_flashcard(fid):
    try:
        data = FlashcardReportIn.model_validate(request.get_json(force=True) or {})
    except ValidationError as e:
        return jsonify({"error": "invalid input", "details": validation_errors(e)}), 400
    reason = data.reason

    db = get_db()
    # Verifica se o card existe e pertence ao user
    card = db.execute("SELECT id FROM flashcards WHERE id = ? AND user_id = ?", (fid, g.user_id)).fetchone()
    if not card:
        return jsonify({"error": "Flashcard nao encontrado."}), 404

    try:
        with db_transaction(db, immediate=True):
            db.execute("""
                UPDATE flashcards 
                SET report_status = ? 
                WHERE id = ? AND user_id = ?
            """, (reason, fid, g.user_id))
        invalidate_user_caches(g.user_id)
    except Exception:
        logger.exception("Failed to report flashcard id=%s user_id=%s", fid, g.user_id)
        return jsonify({"error": "Internal Server Error"}), 500

    return jsonify({"success": True})


@bp.route("/flashcards/export/anki", methods=["GET"])
def export_anki():
    db = get_db()
    due_only = request.args.get("due_only", "false").lower() == "true"
    now = datetime.now(timezone.utc).isoformat()

    if due_only:
        rows = db.execute("""
            SELECT f.id, f.front, f.back, f.source_context, q.area, q.subtema, q.topic, q.institution_code
            FROM flashcards f
            JOIN questions q ON f.question_id = q.id
            WHERE f.user_id = ? AND f.next_review_date <= ?
            ORDER BY f.id ASC
        """, (g.user_id, now)).fetchall()
    else:
        rows = db.execute("""
            SELECT f.id, f.front, f.back, f.source_context, q.area, q.subtema, q.topic, q.institution_code
            FROM flashcards f
            JOIN questions q ON f.question_id = q.id
            WHERE f.user_id = ?
            ORDER BY f.id ASC
        """, (g.user_id,)).fetchall()

    header_lines = [
        "#separator:tab",
        "#html:true",
        "#tags column:3",
        "#deck:MedQuest::Revisão_Ativa",
        "#notetype:Cloze",
    ]

    card_lines = []
    for r in rows:
        front = (r["front"] or "").replace("\t", " ").replace("\r\n", "<br>").replace("\n", "<br>")
        back = (r["back"] or "").replace("\t", " ").replace("\r\n", "<br>").replace("\n", "<br>")
        
        tags = ["MedQuest"]
        if r["area"]:
            area_tag = re.sub(r"[^\w]+", "_", r["area"]).strip("_")
            tags.append(f"Area::{area_tag}")
        if r["subtema"]:
            sub_tag = re.sub(r"[^\w]+", "_", r["subtema"]).strip("_")
            tags.append(f"Subtema::{sub_tag}")
        if r["institution_code"]:
            inst_tag = re.sub(r"[^\w]+", "_", r["institution_code"]).strip("_")
            tags.append(f"Banca::{inst_tag}")

        tags_str = " ".join(tags)
        card_lines.append(f"{front}\t{back}\t{tags_str}")

    content = "\n".join(header_lines + card_lines)
    return Response(
        content,
        mimetype="text/plain; charset=utf-8",
        headers={
            "Content-Disposition": "attachment; filename=medquest_flashcards_anki.txt"
        }
    )
