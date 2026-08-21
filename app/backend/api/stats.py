"""Blueprint: desempenho, recomendações e mapa de cobertura."""
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from flask import Blueprint, g, jsonify, request

from scripts.planner import USP_WEIGHTS, get_normalized_area

from .adaptive import build_learning_profile, fsrs_metrics
from .db import get_db

bp = Blueprint("stats", __name__)

from threading import Lock


class SimpleTTLCache:
    def __init__(self, ttl_seconds, max_size=500):
        self.ttl = ttl_seconds
        self.max_size = max_size
        self.cache = {}
        self.expiry = {}
        self.lock = Lock()
        
    def get(self, key):
        with self.lock:
            if key in self.cache and time.time() < self.expiry[key]:
                return self.cache[key]
            if key in self.cache:
                del self.cache[key]
                del self.expiry[key]
            return None
            
    def set(self, key, value):
        with self.lock:
            now = time.time()
            stale = [k for k, exp in self.expiry.items() if now >= exp]
            for k in stale:
                del self.cache[k]
                del self.expiry[k]
            if len(self.cache) >= self.max_size:
                oldest = min(self.expiry, key=self.expiry.get)
                del self.cache[oldest]
                del self.expiry[oldest]
            self.cache[key] = value
            self.expiry[key] = now + self.ttl

    def clear_user(self, user_id):
        with self.lock:
            keys_to_delete = [k for k in self.cache.keys() if str(k).startswith(str(user_id))]
            for k in keys_to_delete:
                del self.cache[k]
                del self.expiry[k]
                
overview_cache = SimpleTTLCache(60)


def responsible_streak(days_studied, today, days_per_week=6):
    """Count active days while honoring configured weekly rest days.

    Rest days preserve continuity but never inflate the displayed streak.
    """
    active = {str(day) for day in days_studied if day}
    target = max(1, min(7, int(days_per_week or 6)))
    rest_budget = 7 - target
    active_count = 0
    cursor = today
    examined = 0
    rests_in_block = 0
    while examined < 366:
        if str(cursor) in active:
            active_count += 1
        elif rests_in_block < rest_budget:
            rests_in_block += 1
        else:
            break
        examined += 1
        if examined % 7 == 0:
            rests_in_block = 0
        cursor -= timedelta(days=1)
    current_week_active = sum(str(today - timedelta(days=offset)) in active for offset in range(7))
    return {
        "days": active_count,
        "weekly_target": target,
        "active_days_last_7": current_week_active,
        "rest_days_available": max(0, rest_budget - (7 - current_week_active)),
        "policy": "rest_days_preserve_continuity",
    }

@bp.route("/stats/overview")
def overview():
    try:
        tz_offset = int(request.args.get('tz_offset', 0))
    except (ValueError, TypeError):
        tz_offset = 0

    cache_key = f"{g.user_id}_{tz_offset}"
    cached = overview_cache.get(cache_key)
    if cached:
        return jsonify(cached)

    db = get_db()
    now_utc = datetime.now(timezone.utc)
    last7_start = (now_utc - timedelta(days=7)).isoformat()
    prev7_start = (now_utc - timedelta(days=14)).isoformat()
    now_value = now_utc.isoformat()

    # Turso is remote in production. Keep the dashboard summary to one round
    # trip rather than issuing a separate remote query for each metric.
    overview = db.execute("""
        SELECT
            (SELECT COUNT(*) FROM questions WHERE missing_alts = 0) AS total_q,
            (SELECT COUNT(*) FROM attempts WHERE user_id = ?) AS total_attempts,
            (SELECT COUNT(DISTINCT question_id) FROM attempts WHERE user_id = ?) AS distinct_answered,
            (SELECT COUNT(*) FROM attempts WHERE user_id = ? AND is_correct = 1) AS correct,
            (SELECT COUNT(*) FROM attempts a1
             WHERE a1.user_id = ? AND a1.is_correct = 1
               AND a1.id = (SELECT MAX(a2.id) FROM attempts a2
                            WHERE a2.user_id = ? AND a2.question_id = a1.question_id)) AS last_correct,
            (SELECT COUNT(*) FROM spaced_repetition
             WHERE next_review_date <= ? AND user_id = ?) AS srs_due_count,
            (SELECT COUNT(*) FROM flashcards
             WHERE next_review_date <= ? AND user_id = ?) AS flashcards_due_count,
            (SELECT SUM(is_correct) FROM attempts WHERE answered_at >= ? AND user_id = ?) AS last7_correct,
            (SELECT COUNT(*) FROM attempts WHERE answered_at >= ? AND user_id = ?) AS last7_total,
            (SELECT SUM(is_correct) FROM attempts
             WHERE answered_at >= ? AND answered_at < ? AND user_id = ?) AS prev7_correct,
            (SELECT COUNT(*) FROM attempts
             WHERE answered_at >= ? AND answered_at < ? AND user_id = ?) AS prev7_total
    """, (
        g.user_id, g.user_id, g.user_id, g.user_id, g.user_id,
        now_value, g.user_id, now_value, g.user_id,
        last7_start, g.user_id, last7_start, g.user_id,
        prev7_start, last7_start, g.user_id,
        prev7_start, last7_start, g.user_id,
    )).fetchone()
    total_q = overview["total_q"]
    total_attempts = overview["total_attempts"]
    distinct_answered = overview["distinct_answered"]
    correct = overview["correct"]
    accuracy = (correct / total_attempts) if total_attempts else None
    last_correct = overview["last_correct"]
    accuracy_latest = (last_correct / distinct_answered) if distinct_answered else None
    coverage_pct = (distinct_answered / total_q) if total_q else None

    srs_due_count = overview["srs_due_count"]
    flashcards_due_count = overview["flashcards_due_count"]
    accuracy_last7 = (overview["last7_correct"] / overview["last7_total"]) if overview["last7_total"] else None
    accuracy_prev7 = (overview["prev7_correct"] / overview["prev7_total"]) if overview["prev7_total"] else None

    day_rows = db.execute(
        "SELECT DISTINCT substr(answered_at, 1, 10) AS day FROM attempts WHERE user_id = ? ORDER BY day DESC", (g.user_id,)
    ).fetchall()
    days_studied = {r["day"] for r in day_rows}
    config = db.execute(
        "SELECT days_per_week FROM planner_config WHERE user_id = ?", (g.user_id,)
    ).fetchone()
    local_today = (now_utc + timedelta(minutes=tz_offset)).date()
    streak = responsible_streak(days_studied, local_today, config["days_per_week"] if config else 6)

    result = {
        "total_questions": total_q, "distinct_answered": distinct_answered,
        "total_attempts": total_attempts, "accuracy_all_attempts": accuracy,
        "accuracy_latest_attempt": accuracy_latest, "coverage_pct": coverage_pct,
        "srs_due_count": srs_due_count, "accuracy_last7": accuracy_last7,
        "accuracy_prev7": accuracy_prev7, "streak_days": streak["days"],
        "streak": streak,
        "flashcards_due_count": flashcards_due_count,
    }
    overview_cache.set(cache_key, result)
    return jsonify(result)


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
        "specialty": ("specialty", "specialty"),
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

    attempt_count = db.execute(
        "SELECT COUNT(*) n FROM attempts WHERE user_id = ?", (g.user_id,)
    ).fetchone()["n"]
    if attempt_count >= 3:
        recs.append({
            "type": "adaptive", "icon": "ph-brain",
            "title": "Sessão adaptativa personalizada",
            "description": "Uma fila equilibrada por revisões vencidas, risco de esquecimento, erros recentes e lacunas de cobertura.",
            "cta": "Iniciar sessão", "filters": {"mode": "adaptive", "limit": "30"},
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


@bp.route("/stats/learning-profile")
def learning_profile():
    return jsonify(build_learning_profile(get_db(), g.user_id))


@bp.route("/stats/exam-readiness")
def exam_readiness():
    """Coverage report for an institution/editable exam scope, isolated by user."""
    db = get_db()
    institution = request.args.get("institution", "").strip()[:64]
    institution_clause = "AND q.institution_code = ?" if institution else ""
    params = [g.user_id]
    if institution:
        params.append(institution)
    rows = db.execute(f"""
        SELECT q.area AS area,
               COUNT(DISTINCT q.id) AS available,
               COUNT(DISTINCT a.question_id) AS answered,
               COUNT(a.id) AS attempts,
               COALESCE(SUM(a.is_correct), 0) AS correct
        FROM questions q
        LEFT JOIN attempts a ON a.question_id = q.id AND a.user_id = ?
        WHERE q.missing_alts = 0 AND q.area IS NOT NULL AND q.area != ''
              {institution_clause}
        GROUP BY q.area
        ORDER BY available DESC
    """, params).fetchall()
    areas = []
    for row in rows:
        attempts = row["attempts"]
        available = row["available"]
        areas.append({
            "area": row["area"],
            "available": available,
            "answered": row["answered"],
            "coverage": round(row["answered"] / available, 4) if available else 0,
            "attempts": attempts,
            "accuracy": round(row["correct"] / attempts, 4) if attempts else None,
            "sample": "sufficient" if attempts >= 20 else "limited",
            "action": "/estudar?" + urlencode({"area": row["area"], "status": "new", "limit": 20}),
        })
    areas.sort(key=lambda item: (item["coverage"], item["accuracy"] if item["accuracy"] is not None else -1, item["area"]))
    total_available = sum(item["available"] for item in areas)
    total_answered = sum(item["answered"] for item in areas)
    return jsonify({
        "institution": institution or None,
        "coverage": round(total_answered / total_available, 4) if total_available else 0,
        "answered": total_answered,
        "available": total_available,
        "areas": areas,
        "disclaimer": "Projeções com menos de 20 tentativas por área têm amostra limitada.",
    })


@bp.route("/stats/predictive-score")
def predictive_score():
    db = get_db()
    # Pega o target_score do planner_config
    config_row = db.execute("SELECT * FROM planner_config WHERE user_id = ?", (g.user_id,)).fetchone()
    target_score = config_row["target_score"] if config_row and "target_score" in config_row.keys() else None

    # Calcula acurácia por área
    areas_stats = db.execute("""
        SELECT q.area AS area, COUNT(a.id) AS attempts, SUM(a.is_correct) AS correct
        FROM attempts a JOIN questions q ON q.id = a.question_id
        WHERE a.user_id = ? AND q.area IS NOT NULL AND q.area != ''
        GROUP BY q.area
    """, (g.user_id,)).fetchall()

    if not areas_stats:
        return jsonify({
            "projected_score": 0,
            "target_score": target_score,
            "areas": []
        })

    areas_acc = []
    projected_score_weighted = 0.0
    total_weights = 0.0

    for r in areas_stats:
        norm_area = get_normalized_area(r["area"])
        weight = USP_WEIGHTS.get(norm_area, 0.1)
        
        # Penaliza acurácia se tiver menos de 5 tentativas
        acc = (r["correct"] / r["attempts"]) if r["attempts"] >= 5 else (r["correct"] / 5.0)
        acc_pct = round(acc * 100, 1)
        areas_acc.append({
            "area": r["area"],
            "accuracy": acc_pct,
            "attempts": r["attempts"]
        })
        
        projected_score_weighted += acc_pct * weight
        total_weights += weight

    # Se a soma dos pesos for menor que 1 (ex: não respondeu todas as áreas ainda), projetamos proativamente baseando no peso atingido
    # Ex: se só respondeu Clínica (0.3), projetamos a nota apenas nessa proporção? 
    # Não, se ele só respondeu clínica, assumimos que as outras são 0 até que ele estude, ou normalizamos?
    # Para ser realista na prova, o que ele não estudou é 0. Mas para motivação inicial, vamos normalizar.
    projected_score = round(projected_score_weighted / total_weights, 1) if total_weights > 0 else 0.0

    return jsonify({
        "projected_score": projected_score,
        "target_score": target_score,
        "areas": sorted(areas_acc, key=lambda x: x["accuracy"], reverse=True)
    })

@bp.route("/stats/at-risk")
def at_risk():
    db = get_db()
    
    # Buscar cards de FSRS (questões) do usuário que têm fsrs_card e próxima revisão em breve
    # Como não temos uma tabela explícita unificada, pegamos das questões
    now_utc = datetime.now(timezone.utc).isoformat()
    # Pega os 10 mais urgentes
    rows = db.execute("""
        SELECT q.subtema, sr.fsrs_card, sr.next_review_date
        FROM spaced_repetition sr
        JOIN questions q ON sr.question_id = q.id
        WHERE sr.user_id = ? AND sr.fsrs_card IS NOT NULL
        ORDER BY sr.next_review_date ASC
        LIMIT 50
    """, (g.user_id,)).fetchall()
    
    topics_risk = {}
    for r in rows:
        subtema = r["subtema"]
        if not subtema: continue
        metrics = fsrs_metrics(r["fsrs_card"])
        retrievability = metrics["retrievability"]
        if retrievability is None:
            continue
            
        if subtema not in topics_risk:
            topics_risk[subtema] = {"count": 0, "min_retrievability": retrievability}
        
        topics_risk[subtema]["count"] += 1
        topics_risk[subtema]["min_retrievability"] = min(topics_risk[subtema]["min_retrievability"], retrievability)
            
    # A retenção desejada padrão do FSRS é 90%; abaixo disso há risco de esquecimento.
    at_risk_list = []
    for subtema, data in topics_risk.items():
        if data["min_retrievability"] < 0.9:
            at_risk_list.append({
                "subtema": subtema,
                "items_count": data["count"],
                "retrievability": round(data["min_retrievability"], 4),
                "stability": None,
            })
            
    at_risk_list.sort(key=lambda x: (x["retrievability"], x["subtema"]))
    return jsonify(at_risk_list[:10])


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
        
    overview_cache.clear_user(g.user_id)
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
