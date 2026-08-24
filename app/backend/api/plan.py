"""Blueprint: planejador (config, progresso semanal, revisões, geração de plano)."""
from datetime import datetime, timedelta, timezone

from flask import Blueprint, Response, g, jsonify, request

# planner.py (raiz do backend) — geração do plano anual por pesos históricos USP
from scripts.planner import generate_annual_plan

from .db import db_transaction, get_db
from .questions import invalidate_user_caches
from .schemas import (
    GeneratePlanIn,
    PlannerConfigIn,
    PlannerRevisionIn,
    PlannerStudyIn,
    ValidationError,
    validation_errors,
)

bp = Blueprint("plan", __name__)


@bp.route("/planner/config/reset", methods=["POST"])
def planner_config_reset():
    db = get_db()
    with db_transaction(db, immediate=True):
        db.execute("DELETE FROM planner_config WHERE user_id = ?", (g.user_id,))
        db.execute("DELETE FROM planner_progress WHERE user_id = ?", (g.user_id,))
    invalidate_user_caches(g.user_id)
    return jsonify({"success": True})


@bp.route("/planner/config", methods=["GET", "POST"])
def planner_config():
    db = get_db()
    if request.method == "POST":
        try:
            cfg = PlannerConfigIn.model_validate(request.get_json(force=True) or {})
        except ValidationError as e:
            return jsonify({"error": "invalid input", "details": validation_errors(e)}), 400
        
        target_inst = cfg.target_institution
        if not target_inst and cfg.target_institutions:
            target_inst = ", ".join(cfg.target_institutions)

        with db_transaction(db, immediate=True):
            try:
                db.execute("""
                    INSERT INTO planner_config (user_id, exam_date, start_date, days_per_week, questions_per_day, updated_at, target_score, target_institution, target_specialty)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET
                        exam_date = excluded.exam_date, start_date = excluded.start_date,
                        days_per_week = excluded.days_per_week, questions_per_day = excluded.questions_per_day,
                        updated_at = excluded.updated_at, target_score = excluded.target_score,
                        target_institution = excluded.target_institution, target_specialty = excluded.target_specialty
                """, (g.user_id, cfg.exam_date, cfg.start_date, cfg.days_per_week, cfg.hours_per_day,
                      datetime.now(timezone.utc).isoformat(), cfg.target_score, target_inst, cfg.target_specialty))
            except Exception as e:
                err_msg = str(e).lower()
                if any(k in err_msg for k in ("target_score", "target_institution", "target_specialty", "has no column", "no such column")):
                    try:
                        db.execute("ALTER TABLE planner_config ADD COLUMN target_score REAL")
                    except Exception:
                        pass
                    try:
                        db.execute("ALTER TABLE planner_config ADD COLUMN target_institution TEXT")
                    except Exception:
                        pass
                    try:
                        db.execute("ALTER TABLE planner_config ADD COLUMN target_specialty TEXT")
                    except Exception:
                        pass
                    db.execute("""
                        INSERT INTO planner_config (user_id, exam_date, start_date, days_per_week, questions_per_day, updated_at, target_score, target_institution, target_specialty)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(user_id) DO UPDATE SET
                            exam_date = excluded.exam_date, start_date = excluded.start_date,
                            days_per_week = excluded.days_per_week, questions_per_day = excluded.questions_per_day,
                            updated_at = excluded.updated_at, target_score = excluded.target_score,
                            target_institution = excluded.target_institution, target_specialty = excluded.target_specialty
                    """, (g.user_id, cfg.exam_date, cfg.start_date, cfg.days_per_week, cfg.hours_per_day,
                          datetime.now(timezone.utc).isoformat(), cfg.target_score, target_inst, cfg.target_specialty))
                else:
                    raise e
        invalidate_user_caches(g.user_id)
        return jsonify({"success": True})

    row = db.execute("SELECT * FROM planner_config WHERE user_id = ?", (g.user_id,)).fetchone()
    if not row:
        return jsonify({})
    row_keys = row.keys() if hasattr(row, 'keys') else []
    inst_str = row["target_institution"] if "target_institution" in row_keys else None
    inst_list = [i.strip() for i in inst_str.split(",") if i.strip()] if inst_str else []
    return jsonify({
        "exam_date": row["exam_date"], "start_date": row["start_date"],
        "days_per_week": row["days_per_week"], "hours_per_day": row["questions_per_day"],
        "target_score": row["target_score"] if "target_score" in row_keys else None,
        "target_institution": inst_str,
        "target_institutions": inst_list,
        "target_specialty": row["target_specialty"] if "target_specialty" in row_keys else None,
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
        return jsonify({"error": "invalid input", "details": validation_errors(e)}), 400
    studied = 1 if data.studied else 0
    if studied:
        studied_at = datetime.now(timezone.utc).isoformat()
        with db_transaction(db, immediate=True):
            db.execute("""
                INSERT INTO planner_progress (week, studied, studied_at, rev24h, rev7d, rev30d, user_id)
                VALUES (?, 1, ?, 0, 0, 0, ?)
                ON CONFLICT(week, user_id) DO UPDATE SET studied = 1, studied_at = excluded.studied_at
            """, (week, studied_at, g.user_id))
    else:
        studied_at = None
        with db_transaction(db, immediate=True):
            db.execute("""
                INSERT INTO planner_progress (week, studied, studied_at, rev24h, rev7d, rev30d, user_id)
                VALUES (?, 0, NULL, 0, 0, 0, ?)
                ON CONFLICT(week, user_id) DO UPDATE SET studied = 0, studied_at = NULL, rev24h = 0, rev7d = 0, rev30d = 0
            """, (week, g.user_id))
    invalidate_user_caches(g.user_id)
    return jsonify({"success": True, "studied": bool(studied), "studied_at": studied_at})


@bp.route("/planner/<int:week>/revision", methods=["POST"])
def planner_revision(week):
    db = get_db()
    try:
        data = PlannerRevisionIn.model_validate(request.get_json(force=True) or {})
    except ValidationError as e:
        return jsonify({"error": "invalid input", "details": validation_errors(e)}), 400
        
    allowed_columns = {'rev24h', 'rev7d', 'rev30d'}
    if data.type not in allowed_columns:
        return jsonify({'error': 'invalid type'}), 400
        
    checked = 1 if data.checked else 0
    with db_transaction(db, immediate=True):
        db.execute(f"""
            INSERT INTO planner_progress (week, {data.type}, user_id) VALUES (?, ?, ?)
            ON CONFLICT(week, user_id) DO UPDATE SET {data.type} = excluded.{data.type}
        """, (week, checked, g.user_id))
    invalidate_user_caches(g.user_id)
    return jsonify({"success": True, "type": data.type, "checked": bool(checked)})


@bp.route("/generate_plan", methods=["POST"])
def generate_plan():
    try:
        data = GeneratePlanIn.model_validate(request.get_json(force=True) or {})
    except ValidationError as e:
        return jsonify({"error": "invalid input", "details": validation_errors(e)}), 400
    start_date = data.start_date or datetime.now(timezone.utc).isoformat()
    
    db = get_db()
    q_query = """
        SELECT area, subtema, GROUP_CONCAT(DISTINCT topic) as topics, COUNT(id) as q_count 
        FROM questions 
        WHERE area IS NOT NULL AND subtema IS NOT NULL
        GROUP BY area, subtema
    """
    a_query = """
        SELECT q.subtema, COUNT(DISTINCT a.question_id) as ans_count, SUM(a.is_correct) as correct_count, COUNT(a.id) as attempts
        FROM attempts a
        JOIN questions q ON q.id = a.question_id
        WHERE a.user_id = ? AND q.subtema IS NOT NULL
        GROUP BY q.subtema
    """
    
    if hasattr(db, "batch"):
        res = db.batch([
            (q_query, ()),
            (a_query, (g.user_id,))
        ])
        rows = res[0].fetchall()
        answered = res[1].fetchall()
    else:
        rows = [dict(r) for r in db.execute(q_query).fetchall()]
        answered = [dict(r) for r in db.execute(a_query, (g.user_id,)).fetchall()]
    
    answered_map = {r["subtema"]: r for r in answered}
    
    plan = generate_annual_plan(
        rows, start_date, data.exam_date, data.hours_per_week, 
        intensive=data.intensive, user_progress=answered_map
    )
    return jsonify(plan)


@bp.route("/planner/export/ics", methods=["GET"])
def export_ics():
    db = get_db()
    row = db.execute("SELECT * FROM planner_config WHERE user_id = ?", (g.user_id,)).fetchone()
    
    if not row or not row["exam_date"]:
        start_date = datetime.now(timezone.utc).isoformat()
        exam_date = (datetime.now(timezone.utc) + timedelta(days=120)).isoformat()
        hours_per_week = 24
    else:
        start_date = row["start_date"] or datetime.now(timezone.utc).isoformat()
        exam_date = row["exam_date"]
        days = row["days_per_week"] or 6
        hours = row["questions_per_day"] or 4
        hours_per_week = min(168, days * hours)

    q_query = """
        SELECT area, subtema, GROUP_CONCAT(DISTINCT topic) as topics, COUNT(id) as q_count 
        FROM questions 
        WHERE area IS NOT NULL AND subtema IS NOT NULL
        GROUP BY area, subtema
    """
    a_query = """
        SELECT q.subtema, COUNT(DISTINCT a.question_id) as ans_count, SUM(a.is_correct) as correct_count, COUNT(a.id) as attempts
        FROM attempts a
        JOIN questions q ON q.id = a.question_id
        WHERE a.user_id = ? AND q.subtema IS NOT NULL
        GROUP BY q.subtema
    """
    rows = [dict(r) for r in db.execute(q_query).fetchall()]
    answered = [dict(r) for r in db.execute(a_query, (g.user_id,)).fetchall()]
    answered_map = {r["subtema"]: r for r in answered}

    plan_result = generate_annual_plan(
        rows, start_date, exam_date, hours_per_week, 
        intensive=False, user_progress=answered_map
    )

    plan_weeks = plan_result.get("plan", [])
    now_dt = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    ics_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//MedQuest//Cronograma de Estudos//PT-BR",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:MedQuest - Cronograma de Residência Médica",
        "X-WR-TIMEZONE:America/Sao_Paulo",
    ]

    for w in plan_weeks:
        w_num = w.get("week")
        w_date_str = w.get("date", "")[:10]
        if not w_date_str:
            continue
        
        try:
            w_dt = datetime.strptime(w_date_str, "%Y-%m-%d")
        except Exception:
            continue

        topics = w.get("topics", [])
        topic_names = [t.get("subtema", "") for t in topics if t.get("subtema")]
        subtema_title = topic_names[0] if topic_names else "Revisão Geral"
        topics_desc = "\\n".join([f"- {t.get('subtema')} ({t.get('area')}): {t.get('estimated_hours', 0)}h" for t in topics]) or "Semana de consolidação."

        start_str = w_dt.strftime("%Y%m%dT090000Z")
        end_str = w_dt.strftime("%Y%m%dT120000Z")
        uid = f"medquest-week-{w_num}-{g.user_id}-{w_date_str}@medquest.app"

        ics_lines.extend([
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{now_dt}",
            f"DTSTART:{start_str}",
            f"DTEND:{end_str}",
            f"SUMMARY:[MedQuest] Semana {w_num}: {subtema_title}",
            f"DESCRIPTION:Meta da Semana {w_num} ({w.get('allocated_hours', 0)}h de estudo):\\n{topics_desc}\\n\\n🔗 Acesse em: https://medquest.app/planner",
            "STATUS:CONFIRMED",
            "END:VEVENT",
        ])

        rev24_dt = w_dt + timedelta(days=1)
        ics_lines.extend([
            "BEGIN:VEVENT",
            f"UID:medquest-rev24-{w_num}-{g.user_id}-{w_date_str}@medquest.app",
            f"DTSTAMP:{now_dt}",
            f"DTSTART:{rev24_dt.strftime('%Y%m%dT190000Z')}",
            f"DTEND:{rev24_dt.strftime('%Y%m%dT193000Z')}",
            f"SUMMARY:[MedQuest] 🔄 Revisão 24h: {subtema_title}",
            f"DESCRIPTION:Revisão rápida de 24h dos temas da Semana {w_num}.\\n\\n🔗 https://medquest.app/revisao-ativa",
            "STATUS:CONFIRMED",
            "END:VEVENT",
        ])

        rev7_dt = w_dt + timedelta(days=7)
        ics_lines.extend([
            "BEGIN:VEVENT",
            f"UID:medquest-rev7-{w_num}-{g.user_id}-{w_date_str}@medquest.app",
            f"DTSTAMP:{now_dt}",
            f"DTSTART:{rev7_dt.strftime('%Y%m%dT190000Z')}",
            f"DTEND:{rev7_dt.strftime('%Y%m%dT193000Z')}",
            f"SUMMARY:[MedQuest] 🔄 Revisão 7d: {subtema_title}",
            f"DESCRIPTION:Revisão de 7 dias dos temas da Semana {w_num}.\\n\\n🔗 https://medquest.app/revisao-ativa",
            "STATUS:CONFIRMED",
            "END:VEVENT",
        ])

    ics_lines.append("END:VCALENDAR")
    content = "\r\n".join(ics_lines)

    return Response(
        content,
        mimetype="text/calendar; charset=utf-8",
        headers={
            "Content-Disposition": "attachment; filename=medquest_cronograma.ics"
        }
    )

