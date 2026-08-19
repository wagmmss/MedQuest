"""Blueprint: planejador (config, progresso semanal, revisões, geração de plano)."""
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request, g

from .db import get_db, DB_PATH
from .schemas import PlannerConfigIn, PlannerStudyIn, PlannerRevisionIn, GeneratePlanIn, ValidationError

# planner.py (raiz do backend) — geração do plano anual por pesos históricos USP
from planner import generate_annual_plan

bp = Blueprint("plan", __name__)


@bp.route("/planner/config/reset", methods=["POST"])
def planner_config_reset():
    db = get_db()
    db.execute("DELETE FROM planner_config WHERE user_id = ?", (g.user_id,))
    db.execute("DELETE FROM planner_progress WHERE user_id = ?", (g.user_id,))
    db.commit()
    return jsonify({"success": True})

@bp.route("/planner/config", methods=["GET", "POST"])
def planner_config():
    db = get_db()
    if request.method == "POST":
        try:
            cfg = PlannerConfigIn.model_validate(request.get_json(force=True) or {})
        except ValidationError as e:
            return jsonify({"error": "invalid input", "details": e.errors()}), 400
        db.execute("""
            INSERT INTO planner_config (user_id, exam_date, start_date, days_per_week, questions_per_day, updated_at, target_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                exam_date = excluded.exam_date, start_date = excluded.start_date,
                days_per_week = excluded.days_per_week, questions_per_day = excluded.questions_per_day,
                updated_at = excluded.updated_at, target_score = excluded.target_score
        """, (g.user_id, cfg.exam_date, cfg.start_date, cfg.days_per_week, cfg.hours_per_day,
              datetime.now(timezone.utc).isoformat(), cfg.target_score))
        db.commit()
        return jsonify({"success": True})

    row = db.execute("SELECT * FROM planner_config WHERE user_id = ?", (g.user_id,)).fetchone()
    if not row:
        return jsonify({})
    return jsonify({
        "exam_date": row["exam_date"], "start_date": row["start_date"],
        "days_per_week": row["days_per_week"], "hours_per_day": row["questions_per_day"],
        "target_score": row["target_score"] if "target_score" in row.keys() else None,
    })


@bp.route("/planner")
def get_planner():
    db = get_db()
    rows = db.execute("SELECT * FROM planner_progress WHERE user_id = ?", (g.user_id,)).fetchall()
    return jsonify({r["week"]: {
        "studied": bool(r["studied"]), "studied_at": r["studied_at"],
        "rev24h": bool(r["rev24h"]), "rev7d": bool(r["rev7d"]), "rev30d": bool(r["rev30d"]),
    } for r in rows})


@bp.route("/planner/<int:week>/study", methods=["POST"])
def planner_study(week):
    db = get_db()
    try:
        data = PlannerStudyIn.model_validate(request.get_json(force=True) or {})
    except ValidationError as e:
        return jsonify({"error": "invalid input", "details": e.errors()}), 400
    studied = 1 if data.studied else 0
    studied_at = datetime.now(timezone.utc).isoformat() if studied else None
    if studied:
        db.execute("""
            INSERT INTO planner_progress (week, studied, studied_at, user_id) VALUES (?, 1, ?, ?)
            ON CONFLICT(week, user_id) DO UPDATE SET studied = 1, studied_at = excluded.studied_at
        """, (week, studied_at, g.user_id))
    else:
        db.execute("""
            INSERT INTO planner_progress (week, studied, studied_at, rev24h, rev7d, rev30d, user_id)
            VALUES (?, 0, NULL, 0, 0, 0, ?)
            ON CONFLICT(week, user_id) DO UPDATE SET studied = 0, studied_at = NULL, rev24h = 0, rev7d = 0, rev30d = 0
        """, (week, g.user_id))
    db.commit()
    return jsonify({"success": True, "studied": bool(studied), "studied_at": studied_at})


@bp.route("/planner/<int:week>/revision", methods=["POST"])
def planner_revision(week):
    db = get_db()
    try:
        data = PlannerRevisionIn.model_validate(request.get_json(force=True) or {})
    except ValidationError as e:
        return jsonify({"error": "invalid input", "details": e.errors()}), 400
        
    allowed_columns = {'rev24h', 'rev7d', 'rev30d'}
    if data.type not in allowed_columns:
        return jsonify({'error': 'invalid type'}), 400
        
    checked = 1 if data.checked else 0
    db.execute(f"""
        INSERT INTO planner_progress (week, {data.type}, user_id) VALUES (?, ?, ?)
        ON CONFLICT(week, user_id) DO UPDATE SET {data.type} = excluded.{data.type}
    """, (week, checked, g.user_id))
    db.commit()
    return jsonify({"success": True, "type": data.type, "checked": bool(checked)})


@bp.route("/generate_plan", methods=["POST"])
def generate_plan():
    try:
        data = GeneratePlanIn.model_validate(request.get_json(force=True) or {})
    except ValidationError as e:
        return jsonify({"error": "invalid input", "details": e.errors()}), 400
    start_date = data.start_date or datetime.now(timezone.utc).isoformat()
    
    db = get_db()
    rows = db.execute("""
        SELECT area, subtema, COUNT(id) as q_count 
        FROM questions 
        WHERE area IS NOT NULL AND subtema IS NOT NULL
        GROUP BY area, subtema
    """).fetchall()
    
    plan = generate_annual_plan(rows, start_date, data.exam_date, data.hours_per_week, intensive=data.intensive)
    return jsonify(plan) # generate_annual_plan now returns a dict that might contain warning
