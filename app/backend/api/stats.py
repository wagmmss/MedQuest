"""Blueprint: desempenho, recomendações e mapa de cobertura."""
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request, g

from .db import get_db

bp = Blueprint("stats", __name__)


@bp.route("/stats/overview")
def overview():
    db = get_db()
    total_q = db.execute("SELECT COUNT(*) n FROM questions WHERE missing_alts = 0").fetchone()["n"]
    total_attempts = db.execute("SELECT COUNT(*) n FROM attempts WHERE user_id = ?", (g.user_id,)).fetchone()["n"]
    distinct_answered = db.execute("SELECT COUNT(DISTINCT question_id) n FROM attempts WHERE user_id = ?", (g.user_id,)).fetchone()["n"]
    correct = db.execute("SELECT COUNT(*) n FROM attempts WHERE user_id = ? AND is_correct = 1", (g.user_id,)).fetchone()["n"]
    accuracy = (correct / total_attempts) if total_attempts else None

    last_correct = db.execute("""
        SELECT COUNT(*) n FROM attempts a1 WHERE a1.user_id = ? AND a1.is_correct = 1
        AND a1.id = (SELECT MAX(a2.id) FROM attempts a2 WHERE a2.user_id = ? AND a2.question_id = a1.question_id)
    """, (g.user_id, g.user_id)).fetchone()["n"]
    accuracy_latest = (last_correct / distinct_answered) if distinct_answered else None
    coverage_pct = (distinct_answered / total_q) if total_q else None

    now_utc = datetime.now(timezone.utc)
    srs_due_count = db.execute(
        "SELECT COUNT(*) n FROM spaced_repetition WHERE next_review_date <= ? AND user_id = ?", (now_utc.isoformat(), g.user_id)
    ).fetchone()["n"]
    flashcards_due_count = db.execute(
        "SELECT COUNT(*) n FROM flashcards WHERE next_review_date <= ? AND user_id = ?", (now_utc.isoformat(), g.user_id)
    ).fetchone()["n"]

    last7 = db.execute(
        "SELECT SUM(is_correct) c, COUNT(*) n FROM attempts WHERE answered_at >= ? AND user_id = ?",
        ((now_utc - timedelta(days=7)).isoformat(), g.user_id),
    ).fetchone()
    accuracy_last7 = (last7["c"] / last7["n"]) if last7["n"] else None

    prev7 = db.execute(
        "SELECT SUM(is_correct) c, COUNT(*) n FROM attempts WHERE answered_at >= ? AND answered_at < ? AND user_id = ?",
        ((now_utc - timedelta(days=14)).isoformat(), (now_utc - timedelta(days=7)).isoformat(), g.user_id),
    ).fetchone()
    accuracy_prev7 = (prev7["c"] / prev7["n"]) if prev7["n"] else None

    day_rows = db.execute(
        "SELECT DISTINCT substr(answered_at, 1, 10) AS day FROM attempts WHERE user_id = ? ORDER BY day DESC", (g.user_id,)
    ).fetchall()
    days_studied = {r["day"] for r in day_rows}
    streak_days = 0
    if days_studied:
        try:
            tz_offset = int(request.args.get('tz_offset', 0))
        except (ValueError, TypeError):
            tz_offset = 0
        local_now = datetime.now(timezone.utc) + timedelta(minutes=tz_offset)
        cursor_day = local_now.date()
        if str(cursor_day) not in days_studied:
            cursor_day -= timedelta(days=1)
        while str(cursor_day) in days_studied:
            streak_days += 1
            cursor_day -= timedelta(days=1)

    return jsonify({
        "total_questions": total_q, "distinct_answered": distinct_answered,
        "total_attempts": total_attempts, "accuracy_all_attempts": accuracy,
        "accuracy_latest_attempt": accuracy_latest, "coverage_pct": coverage_pct,
        "srs_due_count": srs_due_count, "accuracy_last7": accuracy_last7,
        "accuracy_prev7": accuracy_prev7, "streak_days": streak_days,
        "flashcards_due_count": flashcards_due_count,
    })


def _breakdown(db, group_col, label_col=None):
    label_expr = label_col or group_col
    rows = db.execute(f"""
        SELECT q.{group_col} AS key, MIN({label_expr}) AS label,
               COUNT(a.id) AS attempts, SUM(a.is_correct) AS correct
        FROM attempts a JOIN questions q ON q.id = a.question_id
        WHERE a.user_id = ? AND q.{group_col} IS NOT NULL AND q.{group_col} != ''
        GROUP BY q.{group_col} ORDER BY attempts DESC
    """, (g.user_id,)).fetchall()
    out = []
    for r in rows:
        acc = (r["correct"] / r["attempts"]) if r["attempts"] else 0
        out.append({"key": r["key"], "label": r["label"], "attempts": r["attempts"],
                    "correct": r["correct"], "accuracy": acc})
    return out


@bp.route("/stats/breakdown")
def breakdown():
    db = get_db()
    by = request.args.get("by", "institution")
    col_map = {
        "institution": ("institution_code", "institution_label"),
        "source": ("source_file", "source_file"),
        "year": ("year", "year"), "topic": ("topic", "topic"),
        "area": ("area", "area"), "subtema": ("subtema", "subtema"),
    }
    if by not in col_map:
        return jsonify({"error": "invalid 'by'"}), 400
    col, label_col = col_map[by]
    return jsonify(_breakdown(db, col, label_col))


@bp.route("/stats/timeline")
def timeline():
    db = get_db()
    days_param = request.args.get("days")
    try:
        days = int(days_param) if days_param else None
    except ValueError:
        days = None

    if days is not None:
        rows = db.execute("""
            SELECT substr(answered_at, 1, 10) AS day, COUNT(*) AS attempts, SUM(is_correct) AS correct
            FROM attempts 
            WHERE user_id = ? AND answered_at >= date('now', ?)
            GROUP BY day ORDER BY day
        """, (g.user_id, f'-{days} days')).fetchall()
    else:
        rows = db.execute("""
            SELECT substr(answered_at, 1, 10) AS day, COUNT(*) AS attempts, SUM(is_correct) AS correct
            FROM attempts WHERE user_id = ? GROUP BY day ORDER BY day
        """, (g.user_id,)).fetchall()
        
    return jsonify([
        {"day": r["day"], "attempts": r["attempts"], "correct": r["correct"],
         "accuracy": (r["correct"] / r["attempts"]) if r["attempts"] else 0}
        for r in rows
    ])


@bp.route("/stats/weak-topics")
def weak_topics():
    db = get_db()
    try:
        min_attempts = int(request.args.get("min_attempts", 3))
    except (TypeError, ValueError):
        min_attempts = 3
    min_attempts = max(1, min(min_attempts, 1000))
    rows = db.execute("""
        SELECT COALESCE(NULLIF(q.subtema, ''), q.topic) AS topic,
               COUNT(a.id) AS attempts, SUM(a.is_correct) AS correct
        FROM attempts a JOIN questions q ON q.id = a.question_id
        WHERE a.user_id = ? AND COALESCE(NULLIF(q.subtema, ''), q.topic) IS NOT NULL
        GROUP BY topic HAVING attempts >= ?
        ORDER BY (CAST(correct AS FLOAT) / attempts) ASC LIMIT 15
    """, (g.user_id, min_attempts)).fetchall()
    return jsonify([
        {"topic": r["topic"], "attempts": r["attempts"], "correct": r["correct"],
         "accuracy": (r["correct"] / r["attempts"]) if r["attempts"] else 0}
        for r in rows
    ])


@bp.route("/stats/recommendations")
def recommendations():
    db = get_db()
    recs = []
    srs_due = db.execute(
        "SELECT COUNT(*) n FROM spaced_repetition WHERE next_review_date <= ? AND user_id = ?",
        (datetime.now(timezone.utc).isoformat(), g.user_id),
    ).fetchone()["n"]
    if srs_due > 0:
        recs.append({
            "type": "srs_due", "icon": "ph-alarm",
            "title": f"{srs_due} questão(ões) para revisar hoje",
            "description": "Sua repetição espaçada tem itens prontos para revisão. Reforce agora o que você já viu antes de esquecer.",
            "cta": "Revisar agora", "filters": {"status": "srs_due"},
        })

    weak_subtemas = db.execute("""
        SELECT q.subtema AS subtema, MIN(q.area) AS area,
               COUNT(a.id) AS attempts, SUM(a.is_correct) AS correct
        FROM attempts a JOIN questions q ON q.id = a.question_id
        WHERE a.user_id = ? AND q.subtema IS NOT NULL AND q.subtema != ''
        GROUP BY q.subtema HAVING attempts >= 3
        ORDER BY (CAST(correct AS FLOAT) / attempts) ASC LIMIT 3
    """, (g.user_id,)).fetchall()
    covered_areas = set()
    for r in weak_subtemas:
        acc = r["correct"] / r["attempts"]
        if acc < 0.65:
            covered_areas.add(r["area"])
            recs.append({
                "type": "weak_topic", "icon": "ph-warning-circle",
                "title": f"Reforce {r['subtema']}",
                "description": f"Sua acurácia aqui é de {round(acc * 100)}% em {r['attempts']} tentativas. Vale revisar a teoria e praticar mais questões.",
                "cta": "Praticar agora", "filters": {"subtema": r["subtema"]},
            })

    weak_areas = db.execute("""
        SELECT q.area AS area, COUNT(a.id) AS attempts, SUM(a.is_correct) AS correct
        FROM attempts a JOIN questions q ON q.id = a.question_id
        WHERE a.user_id = ? AND q.area IS NOT NULL AND q.area != ''
        GROUP BY q.area HAVING attempts >= 5
        ORDER BY (CAST(correct AS FLOAT) / attempts) ASC LIMIT 1
    """, (g.user_id,)).fetchall()
    for r in weak_areas:
        acc = r["correct"] / r["attempts"]
        if acc < 0.65 and r["area"] not in covered_areas:
            recs.append({
                "type": "weak_area", "icon": "ph-chart-bar",
                "title": f"Sua acurácia em {r['area']} está baixa",
                "description": f"{round(acc * 100)}% de acerto em {r['attempts']} tentativas nessa área. Considere revisar os fundamentos antes de continuar.",
                "cta": "Estudar área", "filters": {"area": r["area"]},
            })

    area_totals = db.execute(
        "SELECT area, COUNT(*) n FROM questions WHERE area IS NOT NULL AND area != '' GROUP BY area"
    ).fetchall()
    area_answered = db.execute("""
        SELECT q.area AS area, COUNT(DISTINCT a.question_id) n
        FROM attempts a JOIN questions q ON q.id = a.question_id
        WHERE a.user_id = ? AND q.area IS NOT NULL AND q.area != '' GROUP BY q.area
    """, (g.user_id,)).fetchall()
    answered_map = {r["area"]: r["n"] for r in area_answered}
    least_explored = None
    for r in area_totals:
        if r["n"] < 20:
            continue
        coverage = answered_map.get(r["area"], 0) / r["n"]
        if least_explored is None or coverage < least_explored["coverage"]:
            least_explored = {"area": r["area"], "coverage": coverage, "total": r["n"]}
    if least_explored is not None and least_explored["coverage"] < 0.1:
        recs.append({
            "type": "explore", "icon": "ph-compass",
            "title": f"Explore mais {least_explored['area']}",
            "description": f"Você ainda não praticou quase nada nessa área ({round(least_explored['coverage'] * 100)}% de {least_explored['total']} questões). Bom momento para começar.",
            "cta": "Começar a explorar",
            "filters": {"area": least_explored["area"], "status": "unanswered"},
        })

    total_attempts = db.execute("SELECT COUNT(*) n FROM attempts WHERE user_id = ?", (g.user_id,)).fetchone()["n"]
    last_correct = db.execute("""
        SELECT COUNT(*) n FROM attempts a1 WHERE a1.user_id = ? AND a1.is_correct = 1
        AND a1.id = (SELECT MAX(a2.id) FROM attempts a2 WHERE a2.user_id = ? AND a2.question_id = a1.question_id)
    """, (g.user_id, g.user_id)).fetchone()["n"]
    distinct_answered = db.execute("SELECT COUNT(DISTINCT question_id) n FROM attempts WHERE user_id = ?", (g.user_id,)).fetchone()["n"]
    accuracy_latest = (last_correct / distinct_answered) if distinct_answered else None

    if not recs and distinct_answered >= 10 and accuracy_latest is not None and accuracy_latest >= 0.8:
        recs.append({
            "type": "praise", "icon": "ph-trophy", "title": "Ótimo desempenho geral!",
            "description": f"Você está acertando {round(accuracy_latest * 100)}% das últimas tentativas. Que tal se desafiar em um simulado cronometrado?",
            "cta": "Ir para os filtros", "filters": {},
        })
    elif not recs and total_attempts < 10:
        recs.append({
            "type": "start", "icon": "ph-rocket-launch", "title": "Comece a responder questões",
            "description": "Ainda não há tentativas suficientes para gerar recomendações personalizadas. Responda algumas questões para começar.",
    rows = db.execute("""
        SELECT COALESCE(NULLIF(q.subtema, ''), q.topic) AS topic,
               COUNT(a.id) AS attempts, SUM(a.is_correct) AS correct
        FROM attempts a JOIN questions q ON q.id = a.question_id
        WHERE a.user_id = ? AND COALESCE(NULLIF(q.subtema, ''), q.topic) IS NOT NULL
        GROUP BY topic HAVING attempts >= ?
        ORDER BY (CAST(correct AS FLOAT) / attempts) ASC LIMIT 15
    """, (g.user_id, min_attempts)).fetchall()
    return jsonify([
        {"topic": r["topic"], "attempts": r["attempts"], "correct": r["correct"],
         "accuracy": (r["correct"] / r["attempts"]) if r["attempts"] else 0}
        for r in rows
    ])


@bp.route("/stats/recommendations")
def recommendations():
    db = get_db()
    recs = []
    srs_due = db.execute(
        "SELECT COUNT(*) n FROM spaced_repetition WHERE next_review_date <= ? AND user_id = ?",
        (datetime.now(timezone.utc).isoformat(), g.user_id),
    ).fetchone()["n"]
    if srs_due > 0:
        recs.append({
            "type": "srs_due", "icon": "ph-alarm",
            "title": f"{srs_due} questão(ões) para revisar hoje",
            "description": "Sua repetição espaçada tem itens prontos para revisão. Reforce agora o que você já viu antes de esquecer.",
            "cta": "Revisar agora", "filters": {"status": "srs_due"},
        })

    weak_subtemas = db.execute("""
        SELECT q.subtema AS subtema, MIN(q.area) AS area,
               COUNT(a.id) AS attempts, SUM(a.is_correct) AS correct
        FROM attempts a JOIN questions q ON q.id = a.question_id
        WHERE a.user_id = ? AND q.subtema IS NOT NULL AND q.subtema != ''
        GROUP BY q.subtema HAVING attempts >= 3
        ORDER BY (CAST(correct AS FLOAT) / attempts) ASC LIMIT 3
    """, (g.user_id,)).fetchall()
    covered_areas = set()
    for r in weak_subtemas:
        acc = r["correct"] / r["attempts"]
        if acc < 0.65:
            covered_areas.add(r["area"])
            recs.append({
                "type": "weak_topic", "icon": "ph-warning-circle",
                "title": f"Reforce {r['subtema']}",
                "description": f"Sua acurácia aqui é de {round(acc * 100)}% em {r['attempts']} tentativas. Vale revisar a teoria e praticar mais questões.",
                "cta": "Praticar agora", "filters": {"subtema": r["subtema"]},
            })

    weak_areas = db.execute("""
        SELECT q.area AS area, COUNT(a.id) AS attempts, SUM(a.is_correct) AS correct
        FROM attempts a JOIN questions q ON q.id = a.question_id
        WHERE a.user_id = ? AND q.area IS NOT NULL AND q.area != ''
        GROUP BY q.area HAVING attempts >= 5
        ORDER BY (CAST(correct AS FLOAT) / attempts) ASC LIMIT 1
    """, (g.user_id,)).fetchall()
    for r in weak_areas:
        acc = r["correct"] / r["attempts"]
        if acc < 0.65 and r["area"] not in covered_areas:
            recs.append({
                "type": "weak_area", "icon": "ph-chart-bar",
                "title": f"Sua acurácia em {r['area']} está baixa",
                "description": f"{round(acc * 100)}% de acerto em {r['attempts']} tentativas nessa área. Considere revisar os fundamentos antes de continuar.",
                "cta": "Estudar área", "filters": {"area": r["area"]},
            })

    area_totals = db.execute(
        "SELECT area, COUNT(*) n FROM questions WHERE area IS NOT NULL AND area != '' GROUP BY area"
    ).fetchall()
    area_answered = db.execute("""
        SELECT q.area AS area, COUNT(DISTINCT a.question_id) n
        FROM attempts a JOIN questions q ON q.id = a.question_id
        WHERE a.user_id = ? AND q.area IS NOT NULL AND q.area != '' GROUP BY q.area
    """, (g.user_id,)).fetchall()
    answered_map = {r["area"]: r["n"] for r in area_answered}
    least_explored = None
    for r in area_totals:
        if r["n"] < 20:
            continue
        coverage = answered_map.get(r["area"], 0) / r["n"]
        if least_explored is None or coverage < least_explored["coverage"]:
            least_explored = {"area": r["area"], "coverage": coverage, "total": r["n"]}
    if least_explored is not None and least_explored["coverage"] < 0.1:
        recs.append({
            "type": "explore", "icon": "ph-compass",
            "title": f"Explore mais {least_explored['area']}",
            "description": f"Você ainda não praticou quase nada nessa área ({round(least_explored['coverage'] * 100)}% de {least_explored['total']} questões). Bom momento para começar.",
            "cta": "Começar a explorar",
            "filters": {"area": least_explored["area"], "status": "unanswered"},
        })

    total_attempts = db.execute("SELECT COUNT(*) n FROM attempts WHERE user_id = ?", (g.user_id,)).fetchone()["n"]
    last_correct = db.execute("""
        SELECT COUNT(*) n FROM attempts a1 WHERE a1.user_id = ? AND a1.is_correct = 1
        AND a1.id = (SELECT MAX(a2.id) FROM attempts a2 WHERE a2.user_id = ? AND a2.question_id = a1.question_id)
    """, (g.user_id, g.user_id)).fetchone()["n"]
    distinct_answered = db.execute("SELECT COUNT(DISTINCT question_id) n FROM attempts WHERE user_id = ?", (g.user_id,)).fetchone()["n"]
    accuracy_latest = (last_correct / distinct_answered) if distinct_answered else None

    if not recs and distinct_answered >= 10 and accuracy_latest is not None and accuracy_latest >= 0.8:
        recs.append({
            "type": "praise", "icon": "ph-trophy", "title": "Ótimo desempenho geral!",
            "description": f"Você está acertando {round(accuracy_latest * 100)}% das últimas tentativas. Que tal se desafiar em um simulado cronometrado?",
            "cta": "Ir para os filtros", "filters": {},
        })
    elif not recs and total_attempts < 10:
        recs.append({
            "type": "start", "icon": "ph-rocket-launch", "title": "Comece a responder questões",
            "description": "Ainda não há tentativas suficientes para gerar recomendações personalizadas. Responda algumas questões para começar.",
            "cta": "Ir para os filtros", "filters": {},
        })
    return jsonify(recs[:5])


@bp.route("/stats/reset", methods=["DELETE"])
def reset_stats():
    db = get_db()
    try:
        db.execute("DELETE FROM attempts WHERE user_id = ?", (g.user_id,))
        db.execute("DELETE FROM spaced_repetition WHERE user_id = ?", (g.user_id,))
        db.execute("DELETE FROM flashcards WHERE user_id = ?", (g.user_id,))
        db.execute("DELETE FROM planner_progress WHERE user_id = ?", (g.user_id,))
        db.execute("DELETE FROM favorites WHERE user_id = ?", (g.user_id,))
        db.execute("DELETE FROM planner_config WHERE user_id = ?", (g.user_id,))
        db.commit()
    except Exception:
        raise
    return jsonify({"success": True})


@bp.route("/coverage")
def coverage():
    db = get_db()
    rows = db.execute("""
        SELECT q.area AS area, q.subtema AS subtema,
               COUNT(DISTINCT q.id) AS n_questions,
               COUNT(DISTINCT a.question_id) AS answered,
               COUNT(a.id) AS attempts, COALESCE(SUM(a.is_correct), 0) AS correct
        FROM questions q LEFT JOIN attempts a ON a.question_id = q.id AND a.user_id = ?
        WHERE q.missing_alts = 0 AND q.area IS NOT NULL AND q.area != ''
              AND q.subtema IS NOT NULL AND q.subtema != ''
        GROUP BY q.area, q.subtema ORDER BY q.area, n_questions DESC
    """, (g.user_id,)).fetchall()

    areas = {}
    for r in rows:
        attempts = r["attempts"]
        accuracy = (r["correct"] / attempts) if attempts else None
        coverage_pct = (r["answered"] / r["n_questions"]) if r["n_questions"] else 0
        if r["answered"] == 0:
            status = "not_started"
        elif attempts >= 2 and accuracy is not None and accuracy >= 0.7 and coverage_pct >= 0.5:
            status = "mastered"
        elif attempts >= 2 and accuracy is not None and accuracy >= 0.7:
            status = "proficient"
        else:
            status = "in_progress"
        sub = {"subtema": r["subtema"], "n_questions": r["n_questions"], "answered": r["answered"],
               "attempts": attempts, "correct": r["correct"], "accuracy": accuracy,
               "coverage_pct": coverage_pct, "status": status}
        a = areas.setdefault(r["area"], {
            "area": r["area"], "n_questions": 0, "n_subtemas": 0, "answered_questions": 0,
            "attempts": 0, "correct": 0, "mastered": 0, "proficient": 0,
            "in_progress": 0, "not_started": 0, "subtemas": [],
        })
        a["n_questions"] += r["n_questions"]
        a["n_subtemas"] += 1
        a["answered_questions"] += r["answered"]
        a["attempts"] += attempts
        a["correct"] += r["correct"]
        a[status] += 1
        a["subtemas"].append(sub)

    out = []
    for a in areas.values():
        a["accuracy"] = (a["correct"] / a["attempts"]) if a["attempts"] else None
        out.append(a)
    out.sort(key=lambda x: x["n_questions"], reverse=True)
    return jsonify({"areas": out})


@bp.route("/stats/distractors")
def distractors():
    """NOVO: análise de distratores — qual alternativa errada você mais escolhe por subtema."""
    db = get_db()
    rows = db.execute("""
        SELECT q.subtema AS subtema, a.selected_letter AS letter, COUNT(*) AS n
        FROM attempts a JOIN questions q ON q.id = a.question_id
        WHERE a.user_id = ? AND a.is_correct = 0 AND q.subtema IS NOT NULL AND q.subtema != ''
        GROUP BY q.subtema, a.selected_letter
        ORDER BY q.subtema, n DESC
    """, (g.user_id,)).fetchall()
    by_sub = {}
    for r in rows:
        by_sub.setdefault(r["subtema"], []).append({"letter": r["letter"], "count": r["n"]})
    out = [{"subtema": s, "wrong_choices": v, "total_wrong": sum(x["count"] for x in v)}
           for s, v in by_sub.items()]
    out.sort(key=lambda x: x["total_wrong"], reverse=True)
    return jsonify(out[:20])
