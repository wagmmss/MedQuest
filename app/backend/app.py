"""
MedQuest - app local de estudo para o banco de questões USP (EstratégiaMed).
Backend Flask: serve a API e os arquivos estáticos do frontend.

Uso:
    python app.py
    (depois abra http://localhost:5050 no navegador)
"""
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from planner import generate_annual_plan

from flask import Flask, g, jsonify, request, send_from_directory
from flask_cors import CORS

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.dirname(BACKEND_DIR)
STATIC_DIR = os.path.join(APP_DIR, "static")
DB_PATH = os.path.join(BACKEND_DIR, "medquest.db")

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="")
CORS(app)  # Permite requisições do frontend Next.js


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


# ---------------------------------------------------------------- estático

@app.route("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


# ---------------------------------------------------------------- meta / filtros

@app.route("/api/meta")
def api_meta():
    db = get_db()
    institutions = db.execute(
        """SELECT institution_code, institution_label, COUNT(*) n
           FROM questions GROUP BY institution_code ORDER BY n DESC"""
    ).fetchall()
    years = db.execute(
        "SELECT DISTINCT year FROM questions WHERE year IS NOT NULL ORDER BY year"
    ).fetchall()
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


@app.route("/api/subtemas")
def api_subtemas():
    """Autocomplete de subtema: opcionalmente filtrado por área e por um termo de busca."""
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


# ---------------------------------------------------------------- listagem / fila de estudo

def _question_filter_clauses(args):
    clauses = ["q.missing_alts = 0"]
    params = []

    institutions = args.getlist("institution")
    if institutions:
        clauses.append(f"q.institution_code IN ({','.join('?' * len(institutions))})")
        params.extend(institutions)

    years = args.getlist("year")
    if years:
        clauses.append(f"q.year IN ({','.join('?' * len(years))})")
        params.extend(years)

    sources = args.getlist("source")
    if sources:
        clauses.append(f"q.source_file IN ({','.join('?' * len(sources))})")
        params.extend(sources)

    areas = args.getlist("area")
    if areas:
        clauses.append(f"q.area IN ({','.join('?' * len(areas))})")
        params.extend(areas)

    subtemas = args.getlist("subtema")
    if subtemas:
        clauses.append(f"q.subtema IN ({','.join('?' * len(subtemas))})")
        params.extend(subtemas)

    status = args.get("status", "all")
    if status == "unanswered":
        clauses.append("q.id NOT IN (SELECT question_id FROM attempts)")
    elif status == "wrong":
        clauses.append("""q.id IN (
            SELECT question_id FROM attempts a1 WHERE a1.is_correct = 0
            AND a1.id = (SELECT MAX(a2.id) FROM attempts a2 WHERE a2.question_id = a1.question_id)
        )""")
    elif status == "answered":
        clauses.append("q.id IN (SELECT question_id FROM attempts)")
    elif status == "srs_due":
        clauses.append("q.id IN (SELECT question_id FROM spaced_repetition WHERE next_review_date <= ?)")
        params.append(datetime.now(timezone.utc).isoformat())

    favorite = args.get("favorite")
    if favorite == "1":
        clauses.append("q.id IN (SELECT question_id FROM favorites)")

    return clauses, params


@app.route("/api/questions")
def api_questions():
    db = get_db()
    args = request.args

    clauses, params = _question_filter_clauses(args)
    where = " AND ".join(clauses)
    limit = min(int(args.get("limit", 500)), 2000)

    rows = db.execute(
        f"""SELECT q.id, q.source_file, q.source_number, q.year, q.institution_code,
                   q.institution_label, q.topic, q.area, q.subtema
            FROM questions q
            WHERE {where}
            ORDER BY RANDOM()
            LIMIT ?""",
        (*params, limit),
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/questions/count")
def api_questions_count():
    db = get_db()
    clauses, params = _question_filter_clauses(request.args)
    where = " AND ".join(clauses)
    n = db.execute(f"SELECT COUNT(*) n FROM questions q WHERE {where}", params).fetchone()["n"]
    return jsonify({"count": n})


@app.route("/api/questions/<int:qid>")
def api_question_detail(qid):
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
        "alternatives": [dict(a) for a in alts],
        "images": [i["file_path"] for i in imgs],
        "already_answered": dict(last_attempt) if last_attempt else None,
        "is_favorite": bool(is_favorite),
    })


@app.route("/api/questions/<int:qid>/attempt", methods=["POST"])
def api_submit_attempt(qid):
    db = get_db()
    data = request.get_json(force=True)
    selected = data.get("selected_letter")

    q = db.execute("SELECT correct_letter FROM questions WHERE id = ?", (qid,)).fetchone()
    if not q:
        return jsonify({"error": "not found"}), 404

    is_correct = 1 if selected == q["correct_letter"] else 0
    db.execute(
        "INSERT INTO attempts (question_id, selected_letter, is_correct, answered_at) VALUES (?,?,?,?)",
        (qid, selected, is_correct, datetime.now(timezone.utc).isoformat()),
    )

    # Spaced Repetition logic (SM-2 simplified)
    sr = db.execute("SELECT efactor, interval FROM spaced_repetition WHERE question_id = ?", (qid,)).fetchone()
    efactor = sr["efactor"] if sr else 2.5
    interval = sr["interval"] if sr else 0

    if is_correct:
        if interval == 0:
            interval = 1
        elif interval == 1:
            interval = 6
        else:
            interval = int(round(interval * efactor))
        efactor = min(3.0, efactor + 0.1)
    else:
        interval = 1
        efactor = max(1.3, efactor - 0.2)

    next_review = (datetime.now(timezone.utc) + timedelta(days=interval)).isoformat()

    db.execute("""
        INSERT INTO spaced_repetition (question_id, efactor, interval, next_review_date)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(question_id) DO UPDATE SET
            efactor = excluded.efactor,
            interval = excluded.interval,
            next_review_date = excluded.next_review_date
    """, (qid, efactor, interval, next_review))

    db.commit()

    exp = db.execute(
        "SELECT explanation_text FROM explanations WHERE question_id = ?", (qid,)
    ).fetchone()

    return jsonify({
        "is_correct": bool(is_correct),
        "correct_letter": q["correct_letter"],
        "explanation": exp["explanation_text"] if exp else None,
    })


@app.route("/api/questions/<int:qid>/favorite", methods=["POST"])
def api_toggle_favorite(qid):
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


# ---------------------------------------------------------------- desempenho


@app.route("/api/stats/overview")
def api_stats_overview():
    db = get_db()
    total_q = db.execute("SELECT COUNT(*) n FROM questions WHERE missing_alts = 0").fetchone()["n"]
    total_attempts = db.execute("SELECT COUNT(*) n FROM attempts").fetchone()["n"]
    distinct_answered = db.execute("SELECT COUNT(DISTINCT question_id) n FROM attempts").fetchone()["n"]
    correct = db.execute("SELECT COUNT(*) n FROM attempts WHERE is_correct = 1").fetchone()["n"]
    accuracy = (correct / total_attempts) if total_attempts else None

    # acurácia considerando só a última tentativa de cada questão
    last_correct = db.execute("""
        SELECT COUNT(*) n FROM attempts a1 WHERE a1.is_correct = 1
        AND a1.id = (SELECT MAX(a2.id) FROM attempts a2 WHERE a2.question_id = a1.question_id)
    """).fetchone()["n"]
    accuracy_latest = (last_correct / distinct_answered) if distinct_answered else None

    coverage_pct = (distinct_answered / total_q) if total_q else None

    now_utc = datetime.now(timezone.utc)
    srs_due_count = db.execute(
        "SELECT COUNT(*) n FROM spaced_repetition WHERE next_review_date <= ?",
        (now_utc.isoformat(),),
    ).fetchone()["n"]

    # tendência: acurácia dos últimos 7 dias vs os 7 dias anteriores
    last7 = db.execute(
        "SELECT SUM(is_correct) c, COUNT(*) n FROM attempts WHERE answered_at >= ?",
        ((now_utc - timedelta(days=7)).isoformat(),),
    ).fetchone()
    accuracy_last7 = (last7["c"] / last7["n"]) if last7["n"] else None

    prev7 = db.execute(
        "SELECT SUM(is_correct) c, COUNT(*) n FROM attempts WHERE answered_at >= ? AND answered_at < ?",
        ((now_utc - timedelta(days=14)).isoformat(), (now_utc - timedelta(days=7)).isoformat()),
    ).fetchone()
    accuracy_prev7 = (prev7["c"] / prev7["n"]) if prev7["n"] else None

    # sequência de dias seguidos com pelo menos uma tentativa
    day_rows = db.execute(
        "SELECT DISTINCT substr(answered_at, 1, 10) AS day FROM attempts ORDER BY day DESC"
    ).fetchall()
    days_studied = {r["day"] for r in day_rows}
    streak_days = 0
    if days_studied:
        cursor_day = datetime.now(timezone.utc).date()
        if str(cursor_day) not in days_studied:
            cursor_day -= timedelta(days=1)
        while str(cursor_day) in days_studied:
            streak_days += 1
            cursor_day -= timedelta(days=1)

    return jsonify({
        "total_questions": total_q,
        "distinct_answered": distinct_answered,
        "total_attempts": total_attempts,
        "accuracy_all_attempts": accuracy,
        "accuracy_latest_attempt": accuracy_latest,
        "coverage_pct": coverage_pct,
        "srs_due_count": srs_due_count,
        "accuracy_last7": accuracy_last7,
        "accuracy_prev7": accuracy_prev7,
        "streak_days": streak_days,
    })


def _breakdown(db, group_col, label_col=None):
    label_expr = label_col or group_col
    rows = db.execute(f"""
        SELECT q.{group_col} AS key, MIN({label_expr}) AS label,
               COUNT(a.id) AS attempts,
               SUM(a.is_correct) AS correct
        FROM attempts a
        JOIN questions q ON q.id = a.question_id
        WHERE q.{group_col} IS NOT NULL AND q.{group_col} != ''
        GROUP BY q.{group_col}
        ORDER BY attempts DESC
    """).fetchall()
    out = []
    for r in rows:
        acc = (r["correct"] / r["attempts"]) if r["attempts"] else 0
        out.append({"key": r["key"], "label": r["label"], "attempts": r["attempts"],
                     "correct": r["correct"], "accuracy": acc})
    return out


@app.route("/api/stats/breakdown")
def api_stats_breakdown():
    db = get_db()
    by = request.args.get("by", "institution_code")
    col_map = {
        "institution": ("institution_code", "institution_label"),
        "source": ("source_file", "source_file"),
        "year": ("year", "year"),
        "topic": ("topic", "topic"),
        "area": ("area", "area"),
        "subtema": ("subtema", "subtema"),
    }
    if by not in col_map:
        return jsonify({"error": "invalid 'by'"}), 400
    col, label_col = col_map[by]
    return jsonify(_breakdown(db, col, label_col))


@app.route("/api/stats/timeline")
def api_stats_timeline():
    db = get_db()
    rows = db.execute("""
        SELECT substr(answered_at, 1, 10) AS day,
               COUNT(*) AS attempts,
               SUM(is_correct) AS correct
        FROM attempts
        GROUP BY day
        ORDER BY day
    """).fetchall()
    out = []
    for r in rows:
        acc = (r["correct"] / r["attempts"]) if r["attempts"] else 0
        out.append({"day": r["day"], "attempts": r["attempts"], "correct": r["correct"], "accuracy": acc})
    return jsonify(out)


@app.route("/api/stats/weak-topics")
def api_stats_weak_topics():
    db = get_db()
    min_attempts = int(request.args.get("min_attempts", 3))
    rows = db.execute("""
        SELECT COALESCE(NULLIF(q.subtema, ''), q.topic) AS topic,
               COUNT(a.id) AS attempts, SUM(a.is_correct) AS correct
        FROM attempts a JOIN questions q ON q.id = a.question_id
        WHERE COALESCE(NULLIF(q.subtema, ''), q.topic) IS NOT NULL
        GROUP BY topic
        HAVING attempts >= ?
        ORDER BY (CAST(correct AS FLOAT) / attempts) ASC
        LIMIT 15
    """, (min_attempts,)).fetchall()
    out = []
    for r in rows:
        acc = (r["correct"] / r["attempts"]) if r["attempts"] else 0
        out.append({"topic": r["topic"], "attempts": r["attempts"], "correct": r["correct"], "accuracy": acc})
    return jsonify(out)


@app.route("/api/stats/recommendations")
def api_stats_recommendations():
    """Gera sugestões de estudo acionáveis a partir do histórico de tentativas."""
    db = get_db()
    recs = []

    # 1) Revisões de repetição espaçada vencidas hoje
    srs_due = db.execute(
        "SELECT COUNT(*) n FROM spaced_repetition WHERE next_review_date <= ?",
        (datetime.now(timezone.utc).isoformat(),),
    ).fetchone()["n"]
    if srs_due > 0:
        recs.append({
            "type": "srs_due",
            "icon": "ph-alarm",
            "title": f"{srs_due} questão(ões) para revisar hoje",
            "description": "Sua repetição espaçada tem itens prontos para revisão. Reforce agora o que você já viu antes de esquecer.",
            "cta": "Revisar agora",
            "filters": {"status": "srs_due"},
        })

    # 2) Subtemas mais fracos (mínimo de tentativas para ter significância)
    weak_subtemas = db.execute("""
        SELECT q.subtema AS subtema, MIN(q.area) AS area,
               COUNT(a.id) AS attempts, SUM(a.is_correct) AS correct
        FROM attempts a JOIN questions q ON q.id = a.question_id
        WHERE q.subtema IS NOT NULL AND q.subtema != ''
        GROUP BY q.subtema
        HAVING attempts >= 3
        ORDER BY (CAST(correct AS FLOAT) / attempts) ASC
        LIMIT 3
    """).fetchall()
    covered_areas = set()
    for r in weak_subtemas:
        acc = r["correct"] / r["attempts"]
        if acc < 0.65:
            covered_areas.add(r["area"])
            recs.append({
                "type": "weak_topic",
                "icon": "ph-warning-circle",
                "title": f"Reforce {r['subtema']}",
                "description": f"Sua acurácia aqui é de {round(acc * 100)}% em {r['attempts']} tentativas. Vale revisar a teoria e praticar mais questões.",
                "cta": "Praticar agora",
                "filters": {"subtema": r["subtema"]},
            })

    # 3) Área mais fraca (caso não haja subtema específico já sugerido)
    weak_areas = db.execute("""
        SELECT q.area AS area, COUNT(a.id) AS attempts, SUM(a.is_correct) AS correct
        FROM attempts a JOIN questions q ON q.id = a.question_id
        WHERE q.area IS NOT NULL AND q.area != ''
        GROUP BY q.area
        HAVING attempts >= 5
        ORDER BY (CAST(correct AS FLOAT) / attempts) ASC
        LIMIT 1
    """).fetchall()
    for r in weak_areas:
        acc = r["correct"] / r["attempts"]
        if acc < 0.65 and r["area"] not in covered_areas:
            recs.append({
                "type": "weak_area",
                "icon": "ph-chart-bar",
                "title": f"Sua acurácia em {r['area']} está baixa",
                "description": f"{round(acc * 100)}% de acerto em {r['attempts']} tentativas nessa área. Considere revisar os fundamentos antes de continuar.",
                "cta": "Estudar área",
                "filters": {"area": r["area"]},
            })

    # 4) Área pouco explorada: muitas questões no banco, poucas respondidas
    area_totals = db.execute("""
        SELECT area, COUNT(*) n FROM questions
        WHERE area IS NOT NULL AND area != '' GROUP BY area
    """).fetchall()
    area_answered = db.execute("""
        SELECT q.area AS area, COUNT(DISTINCT a.question_id) n
        FROM attempts a JOIN questions q ON q.id = a.question_id
        WHERE q.area IS NOT NULL AND q.area != ''
        GROUP BY q.area
    """).fetchall()
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
            "type": "explore",
            "icon": "ph-compass",
            "title": f"Explore mais {least_explored['area']}",
            "description": f"Você ainda não praticou quase nada nessa área ({round(least_explored['coverage'] * 100)}% de {least_explored['total']} questões). Bom momento para começar.",
            "cta": "Começar a explorar",
            "filters": {"area": least_explored["area"], "status": "unanswered"},
        })

    # 5) Elogio quando o desempenho geral está bom e não há pendências urgentes
    total_attempts = db.execute("SELECT COUNT(*) n FROM attempts").fetchone()["n"]
    last_correct = db.execute("""
        SELECT COUNT(*) n FROM attempts a1 WHERE a1.is_correct = 1
        AND a1.id = (SELECT MAX(a2.id) FROM attempts a2 WHERE a2.question_id = a1.question_id)
    """).fetchone()["n"]
    distinct_answered = db.execute("SELECT COUNT(DISTINCT question_id) n FROM attempts").fetchone()["n"]
    accuracy_latest = (last_correct / distinct_answered) if distinct_answered else None

    if not recs and distinct_answered >= 10 and accuracy_latest is not None and accuracy_latest >= 0.8:
        recs.append({
            "type": "praise",
            "icon": "ph-trophy",
            "title": "Ótimo desempenho geral!",
            "description": f"Você está acertando {round(accuracy_latest * 100)}% das últimas tentativas. Que tal se desafiar em um simulado cronometrado?",
            "cta": "Ir para os filtros",
            "filters": {},
        })
    elif not recs and total_attempts < 10:
        recs.append({
            "type": "start",
            "icon": "ph-rocket-launch",
            "title": "Comece a responder questões",
            "description": "Ainda não há tentativas suficientes para gerar recomendações personalizadas. Responda algumas questões para começar.",
            "cta": "Ir para os filtros",
            "filters": {},
        })

    return jsonify(recs[:5])


@app.route("/api/stats/reset", methods=["DELETE"])
def api_reset_stats():
    db = get_db()
    db.execute("DELETE FROM attempts")
    db.execute("DELETE FROM spaced_repetition")
    db.commit()
    return jsonify({"success": True})


@app.route("/api/coverage")
def api_coverage():
    """Mapa de cobertura: por área e subtema, cruza nº de questões com o seu desempenho.
    Serve para identificar lacunas (subtemas não iniciados ou fracos)."""
    db = get_db()
    rows = db.execute("""
        SELECT q.area AS area, q.subtema AS subtema,
               COUNT(DISTINCT q.id) AS n_questions,
               COUNT(DISTINCT a.question_id) AS answered,
               COUNT(a.id) AS attempts,
               COALESCE(SUM(a.is_correct), 0) AS correct
        FROM questions q
        LEFT JOIN attempts a ON a.question_id = q.id
        WHERE q.missing_alts = 0 AND q.area IS NOT NULL AND q.area != ''
              AND q.subtema IS NOT NULL AND q.subtema != ''
        GROUP BY q.area, q.subtema
        ORDER BY q.area, n_questions DESC
    """).fetchall()

    areas = {}
    for r in rows:
        attempts = r["attempts"]
        accuracy = (r["correct"] / attempts) if attempts else None
        if r["answered"] == 0:
            status = "not_started"
        elif attempts >= 2 and accuracy is not None and accuracy >= 0.7:
            status = "mastered"
        else:
            status = "in_progress"

        sub = {
            "subtema": r["subtema"],
            "n_questions": r["n_questions"],
            "answered": r["answered"],
            "attempts": attempts,
            "correct": r["correct"],
            "accuracy": accuracy,
            "status": status,
        }
        a = areas.setdefault(r["area"], {
            "area": r["area"], "n_questions": 0, "n_subtemas": 0,
            "answered_questions": 0, "attempts": 0, "correct": 0,
            "mastered": 0, "in_progress": 0, "not_started": 0, "subtemas": [],
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


@app.route("/api/planner/config", methods=["GET", "POST"])
def api_planner_config():
    """Configuração do planejamento anual (data da prova, início, ritmo de estudo)."""
    db = get_db()
    if request.method == "POST":
        data = request.get_json(force=True)
        db.execute("""
            INSERT INTO planner_config (id, exam_date, start_date, days_per_week, questions_per_day, updated_at)
            VALUES (1, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                exam_date = excluded.exam_date,
                start_date = excluded.start_date,
                days_per_week = excluded.days_per_week,
                questions_per_day = excluded.questions_per_day,
                updated_at = excluded.updated_at
        """, (
            data.get("exam_date"),
            data.get("start_date"),
            int(data.get("days_per_week") or 6),
            int(data.get("questions_per_day") or 30),
            datetime.now(timezone.utc).isoformat(),
        ))
        db.commit()
        return jsonify({"success": True})

    row = db.execute("SELECT * FROM planner_config WHERE id = 1").fetchone()
    if not row:
        return jsonify({})
    return jsonify({
        "exam_date": row["exam_date"],
        "start_date": row["start_date"],
        "days_per_week": row["days_per_week"],
        "questions_per_day": row["questions_per_day"],
    })


@app.route("/api/planner")
def api_get_planner():
    db = get_db()
    rows = db.execute("SELECT * FROM planner_progress").fetchall()
    return jsonify({r["week"]: {
        "studied": bool(r["studied"]),
        "studied_at": r["studied_at"],
        "rev24h": bool(r["rev24h"]),
        "rev7d": bool(r["rev7d"]),
        "rev30d": bool(r["rev30d"])
    } for r in rows})


@app.route("/api/planner/<int:week>/study", methods=["POST"])
def api_post_planner_study(week):
    db = get_db()
    data = request.get_json(force=True)
    studied = 1 if data.get("studied") else 0
    studied_at = datetime.now(timezone.utc).isoformat() if studied else None
    
    if studied:
        db.execute("""
            INSERT INTO planner_progress (week, studied, studied_at)
            VALUES (?, 1, ?)
            ON CONFLICT(week) DO UPDATE SET studied = 1, studied_at = ?
        """, (week, studied_at, studied_at))
    else:
        db.execute("""
            INSERT INTO planner_progress (week, studied, studied_at, rev24h, rev7d, rev30d)
            VALUES (?, 0, NULL, 0, 0, 0)
            ON CONFLICT(week) DO UPDATE SET studied = 0, studied_at = NULL, rev24h = 0, rev7d = 0, rev30d = 0
        """, (week,))
    db.commit()
    return jsonify({"success": True, "studied": bool(studied), "studied_at": studied_at})


@app.route("/api/planner/<int:week>/revision", methods=["POST"])
def api_post_planner_revision(week):
    db = get_db()
    data = request.get_json(force=True)
    rev_type = data.get("type")
    checked = 1 if data.get("checked") else 0
    
    if rev_type not in ["rev24h", "rev7d", "rev30d"]:
        return jsonify({"error": "invalid revision type"}), 400
        
    db.execute(f"""
        INSERT INTO planner_progress (week, {rev_type})
        VALUES (?, ?)
        ON CONFLICT(week) DO UPDATE SET {rev_type} = ?
    """, (week, checked, checked))
    db.commit()
    return jsonify({"success": True, "type": rev_type, "checked": bool(checked)})


@app.route("/api/v1/generate_plan", methods=["POST"])
def api_generate_plan():
    data = request.get_json(force=True)
    start_date = data.get("start_date", datetime.now(timezone.utc).isoformat())
    exam_date = data.get("exam_date")
    hours = data.get("hours_per_week", 20)
    
    if not exam_date:
        return jsonify({"error": "exam_date is required"}), 400
        
    plan = generate_annual_plan(DB_PATH, start_date, exam_date, hours)
    return jsonify({"plan": plan})


def init_db():
    with app.app_context():
        db = get_db()
        db.execute("CREATE TABLE IF NOT EXISTS favorites (question_id INTEGER PRIMARY KEY)")
        db.execute("CREATE TABLE IF NOT EXISTS spaced_repetition (question_id INTEGER PRIMARY KEY, efactor REAL, interval INTEGER, next_review_date TEXT)")
        db.execute("""
            CREATE TABLE IF NOT EXISTS planner_progress (
                week INTEGER PRIMARY KEY,
                studied INTEGER DEFAULT 0,
                studied_at TEXT,
                rev24h INTEGER DEFAULT 0,
                rev7d INTEGER DEFAULT 0,
                rev30d INTEGER DEFAULT 0
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS planner_config (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                exam_date TEXT,
                start_date TEXT,
                days_per_week INTEGER DEFAULT 6,
                questions_per_day INTEGER DEFAULT 30,
                updated_at TEXT
            )
        """)
        db.commit()


if __name__ == "__main__":
    init_db()
    # host 0.0.0.0 = aceita conexões da rede local (para acessar pelo celular no mesmo WiFi)
    app.run(host="0.0.0.0", port=5050, debug=True)
