import os
import json
import math
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode, quote

from flask import Blueprint, g, jsonify, request

from scripts.planner import USP_WEIGHTS, get_normalized_area

from .adaptive import build_learning_profile, fsrs_metrics
from .db import get_db, db_transaction
from .questions import invalidate_user_caches
from .observability import emit
from .edital_profiles import EditalProfile, get_edital_profile, CANONICAL_AREAS

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
_area_totals_cache = SimpleTTLCache(300)
_q_totals_cache = SimpleTTLCache(300)

def _get_cached_area_totals(db):
    cached = _area_totals_cache.get("area_totals")
    if cached is not None:
        return cached
    totals = db.execute(
        "SELECT area, COUNT(*) n FROM questions WHERE area IS NOT NULL AND area != '' GROUP BY area"
    ).fetchall()
    _area_totals_cache.set("area_totals", totals)
    return totals

def _get_cached_q_totals_map(db):
    cached = _q_totals_cache.get("q_totals_map")
    if cached is not None:
        return cached
    rows = db.execute("""
        SELECT area, subtema, COUNT(*) AS n_questions
        FROM questions
        WHERE missing_alts = 0 AND area IS NOT NULL AND area != '' AND subtema IS NOT NULL AND subtema != ''
        GROUP BY area, subtema
    """).fetchall()
    q_map = {}
    for r in rows:
        norm_a = get_normalized_area(r["area"])
        sub = r["subtema"]
        q_map[(norm_a, sub)] = r["n_questions"]
    _q_totals_cache.set("q_totals_map", q_map)
    return q_map


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

    config_row = db.execute(
        "SELECT * FROM planner_config WHERE user_id = ?", (g.user_id,)
    ).fetchone()
    config = dict(config_row) if config_row else {}

    local_today = (now_utc + timedelta(minutes=tz_offset)).date()
    local_today_str = str(local_today)
    streak = responsible_streak(days_studied, local_today, config.get("days_per_week") or 6)

    # Contagem de questões distintas resolvidas hoje no fuso local
    today_answered_row = db.execute(
        "SELECT COUNT(DISTINCT question_id) AS today_answered FROM attempts WHERE user_id = ? AND substr(answered_at, 1, 10) = ?",
        (g.user_id, local_today_str)
    ).fetchone()
    today_answered_count = today_answered_row["today_answered"] if today_answered_row else 0

    daily_target = config.get("questions_per_day") or 20
    exam_date_str = config.get("exam_date")
    days_until_exam = None
    if exam_date_str:
        try:
            ed = datetime.fromisoformat(exam_date_str.replace("Z", "+00:00")).date()
            days_until_exam = (ed - local_today).days
        except Exception:
            days_until_exam = None

    result = {
        "total_questions": total_q, "distinct_answered": distinct_answered,
        "total_attempts": total_attempts, "accuracy_all_attempts": accuracy,
        "accuracy_latest_attempt": accuracy_latest, "coverage_pct": coverage_pct,
        "srs_due_count": srs_due_count, "accuracy_last7": accuracy_last7,
        "accuracy_prev7": accuracy_prev7, "streak_days": streak["days"],
        "streak": streak,
        "flashcards_due_count": flashcards_due_count,
        "today_answered": today_answered_count,
        "daily_target": daily_target,
        "days_until_exam": days_until_exam,
        "exam_date": exam_date_str,
        "target_score": config.get("target_score"),
        "target_institution": config.get("target_institution"),
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
        min_attempts = int(request.args.get("min_attempts", 5))
    except (TypeError, ValueError):
        min_attempts = 3
    min_attempts = max(5, min(min_attempts, 1000))
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

    area_totals = _get_cached_area_totals(db)
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


def calculate_bayesian_readiness(area_records: list[dict], edital_profile: EditalProfile) -> dict:
    """
    Calcula a prontidão bayesiana agregada usando modelo Beta-Binomial
    conjugado com prior plano Beta(1, 1) em cada grande área médica.
    """
    # Mapeia registros recebidos usando normalização de área se necessário
    row_map = {}
    for r in area_records:
        norm_a = get_normalized_area(r.get("area", ""))
        if norm_a not in row_map:
            row_map[norm_a] = {
                "attempts": r.get("attempts", 0),
                "correct": r.get("correct", 0),
                "available": r.get("available", 0),
                "answered": r.get("answered", 0),
            }
        else:
            row_map[norm_a]["attempts"] += r.get("attempts", 0)
            row_map[norm_a]["correct"] += r.get("correct", 0)
            row_map[norm_a]["available"] += r.get("available", 0)
            row_map[norm_a]["answered"] += r.get("answered", 0)

    enriched_areas = []
    weighted_mean_sum = 0.0
    weighted_var_sum = 0.0
    area_attempts = {}

    for area in CANONICAL_AREAS:
        norm_key = get_normalized_area(area)
        r = row_map.get(norm_key, {})
        att = r.get("attempts", 0)
        cor = r.get("correct", 0)
        avail = r.get("available", 0)
        ans = r.get("answered", 0)
        w = edital_profile.weights.get(area, 0.20)

        # Prior Beta(1, 1) -> Posterior Beta(1 + cor, 1 + att - cor)
        alpha = 1.0 + cor
        beta = 1.0 + (att - cor)
        mean_i = alpha / (alpha + beta)
        var_i = (alpha * beta) / (((alpha + beta) ** 2) * (alpha + beta + 1.0))

        # Intervalo de credibilidade equal-tailed de 95% da posterior Beta.
        # Ao contrário da aproximação normal, ele continua válido em 0%/100%
        # de acerto e em amostras pequenas.
        ci_lower_i, ci_upper_i = beta_credible_interval(alpha, beta)

        weighted_mean_sum += w * mean_i
        weighted_var_sum += (w ** 2) * var_i
        area_attempts[area] = att

        cov = round(ans / avail, 4) if avail > 0 else 0.0
        acc = round(cor / att, 4) if att > 0 else None

        sample_status = "reliable" if att >= 20 else ("forming" if att >= 5 else "insufficient")

        enriched_areas.append({
            "area": area,
            "available": avail,
            "answered": ans,
            "coverage": cov,
            "attempts": att,
            "correct": cor,
            "accuracy": acc,
            "posterior_mean": round(mean_i, 4),
            "ci_lower": ci_lower_i,
            "ci_upper": ci_upper_i,
            "weight": round(w, 4),
            "sample": "sufficient" if att >= 20 else "limited",
            "sample_status": sample_status,
            "action": "/estudar?" + urlencode({"area": area, "status": "new", "limit": 20}),
        })

    readiness_score = round(weighted_mean_sum, 4)
    ci_lower, ci_upper = weighted_beta_credible_interval(weighted_mean_sum, weighted_var_sum)

    total_attempts = sum(area_attempts.values())
    active_weights = {a: w for a, w in edital_profile.weights.items() if w > 0}
    all_areas_have_5 = all(area_attempts.get(a, 0) >= 5 for a in active_weights)
    all_areas_have_10 = all(area_attempts.get(a, 0) >= 10 for a in active_weights)

    if total_attempts < 20 or not all_areas_have_5:
        evidence_status = "insufficient"
    elif total_attempts >= 50 and all_areas_have_10:
        evidence_status = "reliable"
    else:
        evidence_status = "forming"

    # Fatores e recomendações principais para o usuário fechar lacunas
    key_factors = []
    for a_info in enriched_areas:
        w_pct = round(a_info["weight"] * 100)
        att = a_info["attempts"]
        mean_pct = round(a_info["posterior_mean"] * 100)
        if att < 5:
            key_factors.append({
                "area": a_info["area"],
                "impact": f"Peso de {w_pct}% no edital com apenas {att} tentativa(s) observada(s).",
                "recommendation": f"Resolver pelo menos {max(1, 5 - att)} questão(ões) em {a_info['area']} para calibrar a evidência.",
                "factor_type": "low_sample",
            })
        elif a_info["posterior_mean"] < 0.60:
            key_factors.append({
                "area": a_info["area"],
                "impact": f"Acurácia posterior estimada em {mean_pct}% (peso de {w_pct}% no edital).",
                "recommendation": f"Revisar conceitos prioritários de {a_info['area']} para elevar a prontidão.",
                "factor_type": "low_accuracy",
            })

    limitations = [
        "A prontidão estimada reflete exclusivamente as questões resolvidas no MedQuest sob o perfil de edital configurado.",
        "Não constitui probabilidade de aprovação, garantia de classificação ou nota de corte oficial.",
        "Áreas com menos de 5 tentativas ampliam o intervalo de incerteza da prontidão global.",
        "O intervalo global é uma aproximação Beta por correspondência de momentos das áreas ponderadas.",
    ]

    return {
        "readiness_score": readiness_score,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "evidence_status": evidence_status,
        "enriched_areas": enriched_areas,
        "key_factors": key_factors,
        "limitations": limitations,
    }


def _beta_continued_fraction(a: float, b: float, x: float) -> float:
    """Fração contínua de Lentz para a beta incompleta regularizada."""
    max_iterations = 200
    epsilon = 3e-14
    tiny = 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    d = tiny if abs(d) < tiny else d
    d = 1.0 / d
    h = d
    for m in range(1, max_iterations + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = tiny if abs(d) < tiny else d
        c = 1.0 + aa / c
        c = tiny if abs(c) < tiny else c
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = tiny if abs(d) < tiny else d
        c = 1.0 + aa / c
        c = tiny if abs(c) < tiny else c
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < epsilon:
            break
    return h


def regularized_incomplete_beta(x: float, a: float, b: float) -> float:
    """CDF Beta(a, b), calculada sem dependências estatísticas externas."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    if a <= 0.0 or b <= 0.0:
        raise ValueError("Parâmetros Beta devem ser positivos")
    log_bt = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    log_bt += a * math.log(x) + b * math.log1p(-x)
    bt = math.exp(log_bt)
    if x < (a + 1.0) / (a + b + 2.0):
        value = bt * _beta_continued_fraction(a, b, x) / a
    else:
        value = 1.0 - bt * _beta_continued_fraction(b, a, 1.0 - x) / b
    return min(1.0, max(0.0, value))


def beta_quantile(probability: float, a: float, b: float) -> float:
    """Inverte a CDF Beta por bisseção determinística."""
    if probability <= 0.0:
        return 0.0
    if probability >= 1.0:
        return 1.0
    low, high = 0.0, 1.0
    for _ in range(80):
        mid = (low + high) / 2.0
        if regularized_incomplete_beta(mid, a, b) < probability:
            low = mid
        else:
            high = mid
    return (low + high) / 2.0


def beta_credible_interval(alpha: float, beta: float, mass: float = 0.95) -> tuple[float, float]:
    tail = (1.0 - mass) / 2.0
    return round(beta_quantile(tail, alpha, beta), 4), round(beta_quantile(1.0 - tail, alpha, beta), 4)


def weighted_beta_credible_interval(mean: float, variance: float) -> tuple[float, float]:
    """Intervalo global via Beta com momentos da soma ponderada independente."""
    bounded_mean = min(1.0 - 1e-12, max(1e-12, mean))
    maximum_variance = bounded_mean * (1.0 - bounded_mean)
    if variance <= 0.0 or variance >= maximum_variance:
        return round(bounded_mean, 4), round(bounded_mean, 4)
    concentration = maximum_variance / variance - 1.0
    if concentration <= 0.0:
        return 0.0, 1.0
    return beta_credible_interval(bounded_mean * concentration, (1.0 - bounded_mean) * concentration)


@bp.route("/stats/exam-readiness")
def exam_readiness():
    """Prontidão estimada por instituição/edital com modelo bayesiano Beta-Binomial."""
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

    area_records = [dict(row) for row in rows]
    profile = get_edital_profile(institution or None)
    bayesian_calc = calculate_bayesian_readiness(area_records, profile)

    areas = bayesian_calc["enriched_areas"]
    total_available = sum(item["available"] for item in areas)
    total_answered = sum(item["answered"] for item in areas)

    emit(
        "exam_readiness_viewed",
        profile_status=profile.status,
        evidence_status=bayesian_calc["evidence_status"],
    )

    return jsonify({
        "institution": institution or None,
        "institution_label": profile.institution_label,
        "coverage": round(total_answered / total_available, 4) if total_available else 0,
        "answered": total_answered,
        "available": total_available,
        "readiness_score": bayesian_calc["readiness_score"],
        "ci_lower": bayesian_calc["ci_lower"],
        "ci_upper": bayesian_calc["ci_upper"],
        "evidence_status": bayesian_calc["evidence_status"],
        "edital_profile": profile.model_dump(),
        "areas": areas,
        "key_factors": bayesian_calc["key_factors"],
        "limitations": bayesian_calc["limitations"],
        "disclaimer": "Prontidão estimada calculada via modelo Beta-Binomial ponderado por edital. Não reflete probabilidade de aprovação.",
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
    area_attempts = {}

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
        area_attempts[norm_area] = r["attempts"]

        projected_score_weighted += acc_pct * weight

    # Não normalizamos pelos temas já estudados: isso superestimaria quem
    # praticou apenas as próprias áreas fortes. A projeção só é considerada
    # confiável com pelo menos 20 tentativas em cada grande área.
    projected_score = round(projected_score_weighted, 1)
    is_reliable = all(area_attempts.get(area, 0) >= 20 for area in USP_WEIGHTS)

    return jsonify({
        "projected_score": projected_score,
        "target_score": target_score,
        "areas": sorted(areas_acc, key=lambda x: x["accuracy"], reverse=True),
        "is_reliable": is_reliable,
        "total_attempts": total_attempts,
        "minimum_attempts_per_area": 20,
    })

@bp.route("/stats/at-risk")
def at_risk():
    db = get_db()

    # Buscar cards de FSRS (questões) do usuário que têm fsrs_card e próxima revisão em breve
    # Como não temos uma tabela explícita unificada, pegamos das questões
    # Avalia todos os cartões do usuário antes de selecionar os dez tópicos
    # de maior risco; limitar antes da análise poderia esconder esquecimentos
    # mais graves apenas porque a próxima revisão era posterior.
    rows = db.execute("""
        SELECT q.subtema, sr.fsrs_card, sr.next_review_date
        FROM spaced_repetition sr
        JOIN questions q ON sr.question_id = q.id
        WHERE sr.user_id = ? AND sr.fsrs_card IS NOT NULL
        ORDER BY sr.next_review_date ASC
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
        with db_transaction(db, immediate=True):
            db.execute("DELETE FROM attempts WHERE user_id = ?", (g.user_id,))
            db.execute("DELETE FROM spaced_repetition WHERE user_id = ?", (g.user_id,))
            db.execute("DELETE FROM flashcards WHERE user_id = ?", (g.user_id,))
            db.execute("DELETE FROM planner_progress WHERE user_id = ?", (g.user_id,))
            db.execute("DELETE FROM planner_topic_progress WHERE user_id = ?", (g.user_id,))
            db.execute("DELETE FROM favorites WHERE user_id = ?", (g.user_id,))
            db.execute("DELETE FROM planner_config WHERE user_id = ?", (g.user_id,))
    except Exception:
        raise

    invalidate_user_caches(g.user_id)
    return jsonify({"success": True})


_cached_planner_meta = None
_cached_kat_subs = None


def _get_planner_metadata():
    global _cached_planner_meta, _cached_kat_subs
    if _cached_planner_meta is None:
        planner_data_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "plannerData.json")
        try:
            with open(planner_data_path, "r", encoding="utf-8") as f:
                _cached_planner_meta = json.load(f)
        except Exception:
            _cached_planner_meta = []
    if _cached_kat_subs is None:
        kat_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "katomartCourseDurations.json")
        try:
            with open(kat_path, "r", encoding="utf-8") as f:
                kat = json.load(f)
                _cached_kat_subs = kat.get("subtemas", {})
        except Exception:
            _cached_kat_subs = {}
    return _cached_planner_meta, _cached_kat_subs


@bp.route("/coverage")
def coverage():
    db = get_db()
    area_filter = request.args.get("area", "").strip()
    summary_only = request.args.get("summary_only", "false").lower() == "true"
    planner_meta, kat_subs = _get_planner_metadata()

    # 1. Total de questões por área e subtema (em memória/cache)
    q_map = _get_cached_q_totals_map(db)

    # 2. Resoluções do usuário
    user_rows = db.execute("""
        SELECT q.area, q.subtema,
               COUNT(DISTINCT a.question_id) AS answered,
               COUNT(a.id) AS attempts,
               COALESCE(SUM(a.is_correct), 0) AS correct
        FROM attempts a
        JOIN questions q ON q.id = a.question_id
        WHERE a.user_id = ? AND q.missing_alts = 0 AND q.area IS NOT NULL AND q.area != '' AND q.subtema IS NOT NULL AND q.subtema != ''
        GROUP BY q.area, q.subtema
    """, (g.user_id,)).fetchall()

    u_map = {}
    for r in user_rows:
        norm_a = get_normalized_area(r["area"])
        sub = r["subtema"]
        u_map[(norm_a, sub)] = {
            "answered": r["answered"],
            "attempts": r["attempts"],
            "correct": r["correct"]
        }

    # 3. Monta estrutura baseada no catálogo canônico
    areas_dict = {}
    for area_group in planner_meta:
        raw_area_name = area_group.get("area", "")
        area_name = get_normalized_area(raw_area_name)
        if area_name == "Outros":
            area_name = raw_area_name

        area_obj = areas_dict.setdefault(area_name, {
            "area": area_name,
            "n_questions": 0,
            "n_subtemas": 0,
            "answered_questions": 0,
            "attempts": 0,
            "correct": 0,
            "mastered": 0,
            "proficient": 0,
            "in_progress": 0,
            "not_started": 0,
            "subtemas": [],
            "high_yield_count": 0,
            "high_yield_mastered": 0
        })

        for macro in area_group.get("macroThemes", []):
            theme = macro.get("theme", "")
            is_high_yield = macro.get("highYield", False)
            db_subs = macro.get("dbSubtemas", [theme])

            theme_theory = 0.0
            for s in db_subs:
                k = kat_subs.get(s, {})
                theme_theory += k.get("theory_hours", 1.5)
            theory_hours = round(theme_theory, 2)

            total_n_q = sum(q_map.get((area_name, s), 0) for s in db_subs)
            total_ans = sum(u_map.get((area_name, s), {}).get("answered", 0) for s in db_subs)
            total_att = sum(u_map.get((area_name, s), {}).get("attempts", 0) for s in db_subs)
            total_cor = sum(u_map.get((area_name, s), {}).get("correct", 0) for s in db_subs)

            accuracy = (total_cor / total_att) if total_att > 0 else None
            coverage_pct = (total_ans / total_n_q) if total_n_q > 0 else 0.0

            # Duas questões não são evidência suficiente para afirmar domínio
            # de um tema; exigimos mais amostra antes de marcar como consolidado.
            if total_ans == 0:
                status = "not_started"
            elif total_att >= 10 and accuracy is not None and accuracy >= 0.7 and coverage_pct >= 0.5:
                status = "mastered"
            elif total_att >= 5 and accuracy is not None and accuracy >= 0.7:
                status = "proficient"
            else:
                status = "in_progress"

            area_obj["n_questions"] += total_n_q
            area_obj["n_subtemas"] += 1
            area_obj["answered_questions"] += total_ans
            area_obj["attempts"] += total_att
            area_obj["correct"] += total_cor
            area_obj[status] += 1
            if is_high_yield:
                area_obj["high_yield_count"] += 1
                if status == "mastered":
                    area_obj["high_yield_mastered"] += 1

            # O resumo é usado pelo dashboard e não devolve subtemas. Evitar
            # montar e ordenar centenas de objetos reduz alocação e latência.
            if not summary_only:
                area_obj["subtemas"].append({
                    "subtema": theme,
                    "area": area_name,
                    "n_questions": total_n_q,
                    "answered": total_ans,
                    "attempts": total_att,
                    "correct": total_cor,
                    "accuracy": accuracy,
                    "coverage_pct": round(coverage_pct, 4),
                    "status": status,
                    "highYield": is_high_yield,
                    "theory_hours": theory_hours,
                })

    area_order = ["Clínica Médica", "Cirurgia", "Ginecologia e Obstetrícia", "Pediatria", "Medicina Preventiva"]
    out = []
    for name in area_order:
        if name in areas_dict:
            a = areas_dict[name]
            a["accuracy"] = (a["correct"] / a["attempts"]) if a["attempts"] > 0 else None
            if not summary_only:
                a["subtemas"].sort(key=lambda s: (not s["highYield"], -s["n_questions"]))
            out.append(a)

    for k, a in areas_dict.items():
        if k not in area_order:
            a["accuracy"] = (a["correct"] / a["attempts"]) if a["attempts"] > 0 else None
            if not summary_only:
                a["subtemas"].sort(key=lambda s: (not s["highYield"], -s["n_questions"]))
            out.append(a)

    if area_filter:
        norm_filter = get_normalized_area(area_filter)
        out = [a for a in out if a["area"] == norm_filter or a["area"] == area_filter]

    if summary_only:
        summary_out = []
        for a in out:
            summary_out.append({
                "area": a["area"],
                "n_questions": a["n_questions"],
                "n_subtemas": a["n_subtemas"],
                "answered_questions": a["answered_questions"],
                "attempts": a["attempts"],
                "correct": a["correct"],
                "accuracy": a["accuracy"],
                "mastered": a["mastered"],
                "proficient": a["proficient"],
                "in_progress": a["in_progress"],
                "not_started": a["not_started"],
                "high_yield_count": a["high_yield_count"],
                "high_yield_mastered": a["high_yield_mastered"]
            })
        return jsonify({"areas": summary_out, "summary": True})

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


@bp.route("/stats/benchmark")
def benchmark():
    """Inspirado no benchmark de concorrentes/corte da Medway (MedBrain)."""
    db = get_db()
    now_utc = datetime.now(timezone.utc)
    last7_start = (now_utc - timedelta(days=7)).isoformat()

    stats_row = db.execute("""
        SELECT
            COUNT(a.id) AS total_attempts,
            SUM(a.is_correct) AS total_correct,
            SUM(CASE WHEN a.answered_at >= ? THEN 1 ELSE 0 END) AS last7_attempts,
            SUM(CASE WHEN a.answered_at >= ? THEN a.is_correct ELSE 0 END) AS last7_correct
        FROM attempts a
        WHERE a.user_id = ?
    """, (last7_start, last7_start, g.user_id)).fetchone()

    total_attempts = stats_row["total_attempts"] or 0
    total_correct = stats_row["total_correct"] or 0
    last7_attempts = stats_row["last7_attempts"] or 0
    last7_correct = stats_row["last7_correct"] or 0

    accuracy_overall = (total_correct / total_attempts) if total_attempts > 0 else None
    accuracy_last7 = (last7_correct / last7_attempts) if last7_attempts > 0 else None

    config = None
    try:
        config_row = db.execute("SELECT * FROM planner_config WHERE user_id = ?", (g.user_id,)).fetchone()
        if config_row:
            config = dict(config_row)
    except Exception:
        config = None

    target_score_pct = (config.get("target_score") if config and config.get("target_score") else 76.0)
    target_score = target_score_pct / 100.0

    weekly_target_questions = 80
    if config and config.get("days_per_week"):
        daily_q = config.get("questions_per_day") or 15
        weekly_target_questions = max(20, config["days_per_week"] * daily_q)

    diff_pct = round((accuracy_overall - target_score) * 100, 1) if accuracy_overall is not None else None
    weekly_progress_pct = min(100.0, round((last7_attempts / weekly_target_questions) * 100, 1)) if weekly_target_questions > 0 else 0.0

    status_label = "iniciando"
    if accuracy_overall is not None:
        if diff_pct >= 0:
            status_label = "aprovado"
        elif diff_pct >= -10:
            status_label = "competitivo"
        else:
            status_label = "em_evolucao"

    return jsonify({
        "accuracy_overall": accuracy_overall,
        "accuracy_last7": accuracy_last7,
        "target_score": target_score,
        "target_score_pct": target_score_pct,
        "diff_pct": diff_pct,
        "status_label": status_label,
        "total_attempts": total_attempts,
        "total_correct": total_correct,
        "is_reliable_sample": total_attempts >= 20,
        "last7_attempts": last7_attempts,
        "weekly_target_questions": weekly_target_questions,
        "weekly_progress_pct": weekly_progress_pct,
        "competitors_average_pct": 76.0
    })


@bp.route("/stats/bottlenecks")
def bottlenecks():
    """Inspirado no worst-tags-performance da Medcof: identifica os principais gargalos."""
    db = get_db()
    try:
        limit = int(request.args.get("limit", 5))
    except (ValueError, TypeError):
        limit = 5
    limit = max(1, min(limit, 20))

    rows = db.execute("""
        SELECT
            q.subtema,
            MIN(q.area) AS area,
            COUNT(a.id) AS attempts,
            SUM(a.is_correct) AS correct,
            SUM(CASE WHEN a.is_correct = 0 THEN 1 ELSE 0 END) AS wrong_count,
            SUM(CASE WHEN a.answered_at >= date('now', '-60 days') AND a.is_correct = 0 THEN 1 ELSE 0 END) AS recent_wrong_count,
            SUM(CASE WHEN a.answered_at >= date('now', '-60 days') THEN 1 ELSE 0 END) AS recent_attempts
        FROM attempts a
        JOIN questions q ON q.id = a.question_id
        WHERE a.user_id = ? AND q.subtema IS NOT NULL AND q.subtema != ''
        GROUP BY q.subtema
        HAVING attempts >= 2 AND wrong_count > 0
        ORDER BY
            (CASE WHEN recent_attempts > 0 THEN (CAST(recent_wrong_count AS FLOAT) / recent_attempts) * 1.5 ELSE 0 END) +
            (CAST(wrong_count AS FLOAT) / attempts) DESC,
            wrong_count DESC,
            attempts DESC
        LIMIT ?
    """, (g.user_id, limit)).fetchall()

    out = []
    for r in rows:
        acc = (r["correct"] / r["attempts"]) if r["attempts"] > 0 else 0.0
        out.append({
            "subtema": r["subtema"],
            "area": r["area"],
            "attempts": r["attempts"],
            "correct": r["correct"],
            "wrong_count": r["wrong_count"],
            "accuracy": round(acc, 3),
            "accuracy_pct": round(acc * 100, 1),
            "practice_url": f"/estudar?subtema={quote(r['subtema'])}&status=all&limit=10"
        })
    return jsonify(out)


@bp.route("/stats/domain-summary")
def domain_summary():
    """Inspirado no MedBrain da Medway: progresso de domínio de focos/subtemas por Grande Área."""
    db = get_db()

    rows = db.execute("""
        SELECT
            q.area,
            q.subtema,
            COUNT(DISTINCT q.id) AS total_questions,
            COUNT(a.id) AS attempts,
            COALESCE(SUM(a.is_correct), 0) AS correct
        FROM questions q
        LEFT JOIN attempts a ON a.question_id = q.id AND a.user_id = ?
        WHERE q.missing_alts = 0 AND q.area IS NOT NULL AND q.area != '' AND q.subtema IS NOT NULL AND q.subtema != ''
        GROUP BY q.area, q.subtema
    """, (g.user_id,)).fetchall()

    areas_map = {}
    canonical_order = ["Clínica Médica", "Cirurgia", "Ginecologia e Obstetrícia", "Pediatria", "Medicina Preventiva"]

    for area_name in canonical_order:
        areas_map[area_name] = {
            "area": area_name,
            "total_subtemas": 0,
            "mastered_subtemas": 0,
            "proficient_subtemas": 0,
            "in_progress_subtemas": 0,
            "not_started_subtemas": 0,
            "attempts": 0,
            "correct": 0,
            "accuracy": None,
            "domain_pct": 0.0
        }

    for r in rows:
        area = r["area"]
        if area not in areas_map:
            areas_map[area] = {
                "area": area,
                "total_subtemas": 0,
                "mastered_subtemas": 0,
                "proficient_subtemas": 0,
                "in_progress_subtemas": 0,
                "not_started_subtemas": 0,
                "attempts": 0,
                "correct": 0,
                "accuracy": None,
                "domain_pct": 0.0
            }

        item = areas_map[area]
        item["total_subtemas"] += 1
        att = r["attempts"] or 0
        cor = r["correct"] or 0
        item["attempts"] += att
        item["correct"] += cor

        if att == 0:
            item["not_started_subtemas"] += 1
        else:
            acc = cor / att
            # Critério pedagógico robusto:
            # - Dominado/Consolidado: >= 15 tentativas e acurácia >= 75%
            # - Proficiente / Sinal de domínio: 5 a 14 tentativas e acurácia >= 70%
            if att >= 15 and acc >= 0.75:
                item["mastered_subtemas"] += 1
            elif att >= 5 and acc >= 0.70:
                item["proficient_subtemas"] += 1
            else:
                item["in_progress_subtemas"] += 1

    result = []
    for area_name in canonical_order:
        if area_name in areas_map:
            item = areas_map[area_name]
            if item["attempts"] > 0:
                item["accuracy"] = round(item["correct"] / item["attempts"], 3)
            if item["total_subtemas"] > 0:
                item["domain_pct"] = round((item["mastered_subtemas"] / item["total_subtemas"]) * 100, 1)
            result.append(item)

    for k, item in areas_map.items():
        if k not in canonical_order:
            if item["attempts"] > 0:
                item["accuracy"] = round(item["correct"] / item["attempts"], 3)
            if item["total_subtemas"] > 0:
                item["domain_pct"] = round((item["mastered_subtemas"] / item["total_subtemas"]) * 100, 1)
            result.append(item)

    total_subtemas_all = sum(x["total_subtemas"] for x in result)
    total_mastered_all = sum(x["mastered_subtemas"] for x in result)
    overall_domain_pct = round((total_mastered_all / total_subtemas_all) * 100, 1) if total_subtemas_all > 0 else 0.0

    return jsonify({
        "overall_domain_pct": overall_domain_pct,
        "total_mastered": total_mastered_all,
        "total_subtemas": total_subtemas_all,
        "areas": result
    })


@bp.route("/stats/error-notebook-summary")
def error_notebook_summary():
    """Inspirado no ever-answered-wrong da Medcof: contador e resumo de questões erradas."""
    db = get_db()

    row = db.execute("""
        SELECT
            COUNT(DISTINCT a.question_id) AS ever_wrong_count,
            COUNT(DISTINCT CASE WHEN last_attempt.is_correct = 0 THEN a.question_id END) AS currently_unresolved_count
        FROM attempts a
        LEFT JOIN (
            SELECT a1.question_id, a1.is_correct
            FROM attempts a1
            WHERE a1.user_id = ? AND a1.id = (
                SELECT MAX(a2.id) FROM attempts a2 WHERE a2.user_id = ? AND a2.question_id = a1.question_id
            )
        ) last_attempt ON last_attempt.question_id = a.question_id
        WHERE a.user_id = ? AND a.is_correct = 0
    """, (g.user_id, g.user_id, g.user_id)).fetchone()

    ever_wrong = row["ever_wrong_count"] if row and row["ever_wrong_count"] else 0
    currently_unresolved = row["currently_unresolved_count"] if row and row["currently_unresolved_count"] else 0

    return jsonify({
        "ever_wrong_count": ever_wrong,
        "currently_unresolved_count": currently_unresolved,
        "practice_url": "/estudar?status=wrong&limit=20"
    })


def calculate_wilson_ci(k: int, n: int, confidence: float = 0.95) -> tuple[float | None, float | None]:
    """Calcula o Intervalo de Confiança de Wilson para uma proporção binomial.

    Reproduzível e matematicamente estável para taxas de acerto com amostras pequenas ou grandes.
    Retorna (ci_lower, ci_upper) limitados no intervalo [0.0, 1.0].
    Se n == 0, retorna (None, None).
    """
    if n <= 0:
        return None, None

    z = 1.959964  # z-score para 95% de confiança
    p_hat = k / n
    z2 = z * z
    denominator = 1.0 + (z2 / n)
    center = (p_hat + (z2 / (2.0 * n))) / denominator
    margin = (z / denominator) * math.sqrt((p_hat * (1.0 - p_hat) / n) + (z2 / (4.0 * n * n)))

    lower = max(0.0, round(center - margin, 4))
    upper = min(1.0, round(center + margin, 4))
    return lower, upper


def get_sample_status(attempts: int) -> str:
    """Classifica a robustez estatística da amostra.

    - 'insufficient': < 20 tentativas (bloqueia qualquer conclusão de competitividade).
    - 'forming': 20 a 49 tentativas.
    - 'reliable': >= 50 tentativas.
    """
    if attempts < 20:
        return "insufficient"
    if attempts < 50:
        return "forming"
    return "reliable"


def _build_institution_stats(db, user_id: str, institution_code: str | None = None):
    canonical_order = [
        "Clínica Médica",
        "Cirurgia",
        "Ginecologia e Obstetrícia",
        "Pediatria",
        "Medicina Preventiva",
    ]

    inst_clause = "AND q.institution_code = ?" if institution_code else ""
    inst_params = [user_id]
    if institution_code:
        inst_params.append(institution_code)

    rows = db.execute(f"""
        SELECT
            q.area,
            COUNT(DISTINCT q.id) AS available,
            COUNT(DISTINCT a.question_id) AS answered,
            COUNT(a.id) AS attempts,
            COALESCE(SUM(a.is_correct), 0) AS correct
        FROM questions q
        LEFT JOIN attempts a ON a.question_id = q.id AND a.user_id = ?
        WHERE q.missing_alts = 0 AND q.area IS NOT NULL AND q.area != ''
              {inst_clause}
        GROUP BY q.area
    """, inst_params).fetchall()

    row_map = {r["area"]: r for r in rows}

    label = None
    if institution_code:
        l_row = db.execute(
            "SELECT institution_label FROM questions WHERE institution_code = ? LIMIT 1",
            (institution_code,)
        ).fetchone()
        label = l_row["institution_label"] if l_row else institution_code
    else:
        label = "Desempenho Geral"

    areas = []
    total_available = 0
    total_answered = 0
    total_attempts = 0
    total_correct = 0

    for area_name in canonical_order:
        r = row_map.get(area_name)
        avail = r["available"] if r else 0
        ans = r["answered"] if r else 0
        att = r["attempts"] if r else 0
        cor = r["correct"] if r else 0

        total_available += avail
        total_answered += ans
        total_attempts += att
        total_correct += cor

        acc = round(cor / att, 4) if att > 0 else None
        cov = round(ans / avail, 4) if avail > 0 else 0.0
        ci_lower, ci_upper = calculate_wilson_ci(cor, att)
        sample_status = get_sample_status(att)

        # Priority gap subtemas
        sub_params = [user_id, area_name]
        if institution_code:
            sub_params.append(institution_code)

        sub_rows = db.execute(f"""
            SELECT
                q.subtema,
                COUNT(DISTINCT q.id) AS sub_available,
                COUNT(DISTINCT a.question_id) AS sub_answered,
                COUNT(a.id) AS sub_attempts,
                COALESCE(SUM(a.is_correct), 0) AS sub_correct
            FROM questions q
            LEFT JOIN attempts a ON a.question_id = q.id AND a.user_id = ?
            WHERE q.missing_alts = 0 AND q.area = ? {inst_clause}
                  AND q.subtema IS NOT NULL AND q.subtema != ''
            GROUP BY q.subtema
            ORDER BY
                (CASE WHEN COUNT(a.id) = 0 THEN 0 WHEN (CAST(COALESCE(SUM(a.is_correct), 0) AS FLOAT) / COUNT(a.id)) < 0.65 THEN 1 ELSE 2 END) ASC,
                (CASE WHEN COUNT(a.id) > 0 THEN (CAST(COALESCE(SUM(a.is_correct), 0) AS FLOAT) / COUNT(a.id)) ELSE 0 END) ASC,
                sub_available DESC
            LIMIT 3
        """, sub_params).fetchall()

        priority_topics = []
        for sr in sub_rows:
            s_att = sr["sub_attempts"]
            s_cor = sr["sub_correct"]
            s_acc = round(s_cor / s_att, 4) if s_att > 0 else None

            if s_att == 0:
                gap_type = "unanswered"
            elif s_acc is not None and s_acc < 0.65:
                gap_type = "low_accuracy"
            else:
                gap_type = "low_coverage"

            study_params = {"area": area_name, "subtema": sr["subtema"], "status": "all", "limit": 20}
            simulado_params = {"area": area_name}
            if institution_code:
                study_params["institution"] = institution_code
                simulado_params["institutions"] = institution_code

            priority_topics.append({
                "subtema": sr["subtema"],
                "available": sr["sub_available"],
                "answered": sr["sub_answered"],
                "attempts": s_att,
                "correct": s_cor,
                "accuracy": s_acc,
                "gap_type": gap_type,
                "study_url": f"/estudar?{urlencode(study_params)}",
                "simulado_url": f"/simulado?{urlencode(simulado_params)}",
                "review_url": "/revisao-ativa",
            })

        areas.append({
            "area": area_name,
            "available": avail,
            "answered": ans,
            "coverage": cov,
            "attempts": att,
            "correct": cor,
            "accuracy": acc,
            "ci_lower": ci_lower,
            "ci_upper": ci_upper,
            "sample_status": sample_status,
            "priority_topics": priority_topics,
        })

    overall_acc = round(total_correct / total_attempts, 4) if total_attempts > 0 else None
    overall_cov = round(total_answered / total_available, 4) if total_available > 0 else 0.0
    overall_ci_lower, overall_ci_upper = calculate_wilson_ci(total_correct, total_attempts)
    overall_sample_status = get_sample_status(total_attempts)

    return {
        "code": institution_code,
        "label": label,
        "total_available": total_available,
        "total_answered": total_answered,
        "coverage": overall_cov,
        "total_attempts": total_attempts,
        "total_correct": total_correct,
        "accuracy": overall_acc,
        "ci_lower": overall_ci_lower,
        "ci_upper": overall_ci_upper,
        "sample_status": overall_sample_status,
        "areas": areas,
    }


@bp.route("/stats/institution-radar")
def institution_radar():
    """Radar Comparativo de Bancas por Grande Área e Incerteza Estatística."""
    db = get_db()
    institution = request.args.get("institution", "").strip()[:64]
    compare_institution = request.args.get("compare_institution", "").strip()[:64]

    # Se nenhuma instituição foi passada, tenta descobrir a mais praticada ou configurada
    if not institution:
        top_inst_row = db.execute("""
            SELECT q.institution_code, COUNT(a.id) AS n
            FROM attempts a
            JOIN questions q ON q.id = a.question_id
            WHERE a.user_id = ? AND q.institution_code IS NOT NULL AND q.institution_code != ''
            GROUP BY q.institution_code
            ORDER BY n DESC
            LIMIT 1
        """, (g.user_id,)).fetchone()
        if top_inst_row:
            institution = top_inst_row["institution_code"]
        else:
            cfg_row = db.execute("SELECT target_institution FROM planner_config WHERE user_id = ?", (g.user_id,)).fetchone()
            if cfg_row and cfg_row["target_institution"]:
                institution = cfg_row["target_institution"]
            else:
                institution = "USP-SP"

    primary_data = _build_institution_stats(db, g.user_id, institution)

    # Comparison data
    if compare_institution and compare_institution.upper() != institution.upper():
        comp_stats = _build_institution_stats(db, g.user_id, compare_institution)
        comparison_data = {
            "type": "institution",
            **comp_stats,
        }
    else:
        comp_stats = _build_institution_stats(db, g.user_id, None)
        comparison_data = {
            "type": "global",
            **comp_stats,
        }

    has_comparator = bool(compare_institution and compare_institution.upper() != institution.upper())
    emit(
        "institution_radar_viewed",
        has_comparator=has_comparator,
        sample_status=primary_data["sample_status"],
    )


    return jsonify({
        "institution": primary_data,
        "comparison": comparison_data,
        "disclaimer": "As métricas refletem exclusivamente o histórico resolvido no MedQuest. Menos de 20 tentativas por área indicam amostra limitada e incerteza elevada.",
        "sample_thresholds": {
            "insufficient": "< 20 tentativas (conclusões bloqueadas)",
            "forming": "20 a 49 tentativas",
            "reliable": "≥ 50 tentativas"
        }
    })


ALLOWED_RADAR_ACTIONS = {"study", "simulado", "review"}


@bp.route("/stats/institution-radar/action", methods=["POST"])
def log_radar_action():
    """Registra evento de ação originada no Radar Comparativo de Bancas."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON body"}), 400
    action = data.get("action")
    if not isinstance(action, str) or action not in ALLOWED_RADAR_ACTIONS:
        return jsonify({"error": "Invalid action", "allowed": sorted(ALLOWED_RADAR_ACTIONS)}), 400

    emit(
        "institution_radar_action_clicked",
        action=action,
    )
    return jsonify({"success": True})
