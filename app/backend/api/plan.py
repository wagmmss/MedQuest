import urllib.parse
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
    PlannerTopicProgressIn,
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
        db.execute("DELETE FROM planner_topic_progress WHERE user_id = ?", (g.user_id,))
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
                    INSERT INTO planner_config (user_id, exam_date, start_date, days_per_week, questions_per_day, hours_per_day, updated_at, target_score, target_institution, target_specialty)
                    VALUES (?, ?, ?, ?, 30, ?, ?, ?, ?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET
                        exam_date = excluded.exam_date, start_date = excluded.start_date,
                        days_per_week = excluded.days_per_week, hours_per_day = excluded.hours_per_day,
                        updated_at = excluded.updated_at, target_score = excluded.target_score,
                        target_institution = excluded.target_institution, target_specialty = excluded.target_specialty
                """, (g.user_id, cfg.exam_date, cfg.start_date, cfg.days_per_week, cfg.hours_per_day,
                      datetime.now(timezone.utc).isoformat(), cfg.target_score, target_inst, cfg.target_specialty))
            except Exception as e:
                err_msg = str(e).lower()
                if any(k in err_msg for k in ("target_score", "target_institution", "target_specialty", "hours_per_day", "has no column", "no such column")):
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
                    try:
                        db.execute("ALTER TABLE planner_config ADD COLUMN hours_per_day INTEGER DEFAULT 4")
                    except Exception:
                        pass
                    db.execute("""
                        INSERT INTO planner_config (user_id, exam_date, start_date, days_per_week, questions_per_day, hours_per_day, updated_at, target_score, target_institution, target_specialty)
                        VALUES (?, ?, ?, ?, 30, ?, ?, ?, ?, ?)
                        ON CONFLICT(user_id) DO UPDATE SET
                            exam_date = excluded.exam_date, start_date = excluded.start_date,
                            days_per_week = excluded.days_per_week, hours_per_day = excluded.hours_per_day,
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
        "days_per_week": row["days_per_week"], "hours_per_day": row["hours_per_day"] if "hours_per_day" in row_keys else row["questions_per_day"],
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


@bp.route("/planner/topics")
def get_planner_topics():
    db = get_db()
    rows = db.execute("SELECT week, subtema, completed FROM planner_topic_progress WHERE user_id = ?", (g.user_id,)).fetchall()
    return jsonify({f"{r['week']}:{r['subtema']}": bool(r["completed"]) for r in rows})


@bp.route("/planner/<int:week>/topic", methods=["POST"])
def planner_topic(week):
    try:
        data = PlannerTopicProgressIn.model_validate(request.get_json(force=True) or {})
    except ValidationError as e:
        return jsonify({"error": "invalid input", "details": validation_errors(e)}), 400
    completed = 1 if data.completed else 0
    completed_at = datetime.now(timezone.utc).isoformat() if completed else None
    db = get_db()
    with db_transaction(db, immediate=True):
        db.execute("""INSERT INTO planner_topic_progress (week, subtema, completed, completed_at, user_id)
                      VALUES (?, ?, ?, ?, ?)
                      ON CONFLICT(week, subtema, user_id) DO UPDATE SET completed = excluded.completed, completed_at = excluded.completed_at""",
                   (week, data.subtema, completed, completed_at, g.user_id))
    return jsonify({"success": True, "completed": bool(completed)})


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
        WHERE area IS NOT NULL AND subtema IS NOT NULL AND missing_alts = 0
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


def _generate_calendar_ics_content(db, user_id):
    row = db.execute("SELECT * FROM planner_config WHERE user_id = ?", (user_id,)).fetchone()
    
    if not row or not row["exam_date"]:
        start_date = datetime.now(timezone.utc).isoformat()
        exam_date = (datetime.now(timezone.utc) + timedelta(days=120)).isoformat()
        hours_per_week = 24
        days = 6
    else:
        start_date = row["start_date"] or datetime.now(timezone.utc).isoformat()
        exam_date = row["exam_date"]
        days = row["days_per_week"] or 6
        row_keys = row.keys() if hasattr(row, "keys") else []
        hours = (row["hours_per_day"] if "hours_per_day" in row_keys else row["questions_per_day"]) or 4
        hours_per_week = min(168, days * hours)

    q_query = """
        SELECT area, subtema, GROUP_CONCAT(DISTINCT topic) as topics, COUNT(id) as q_count 
        FROM questions 
        WHERE area IS NOT NULL AND subtema IS NOT NULL AND missing_alts = 0
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
    answered = [dict(r) for r in db.execute(a_query, (user_id,)).fetchall()]
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

    study_days_count = max(1, min(7, days))

    base_url = ""
    try:
        req_origin = request.headers.get("Origin") or request.headers.get("Referer")
        if req_origin:
            parsed = urllib.parse.urlparse(req_origin)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
        elif request.host_url:
            base_url = request.host_url.rstrip("/")
            if ":5050" in base_url:
                base_url = "http://localhost:3000"
    except Exception:
        base_url = ""

    for w in plan_weeks:
        w_num = w.get("week")
        w_date_str = w.get("date", "")[:10]
        if not w_date_str:
            continue
        
        try:
            week_start_dt = datetime.strptime(w_date_str, "%Y-%m-%d")
        except Exception:
            continue

        topics = w.get("topics", [])
        day_slot_minutes = [0] * study_days_count
        if not topics:
            start_str = week_start_dt.strftime("%Y%m%dT080000")
            end_str = (week_start_dt + timedelta(hours=3)).strftime("%Y%m%dT110000")
            uid = f"medquest-week-consolidation-{w_num}-{user_id}-{w_date_str}@medquest"
            ics_lines.extend([
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{now_dt}",
                f"DTSTART:{start_str}",
                f"DTEND:{end_str}",
                f"SUMMARY:[MedQuest] Semana {w_num}: Revisão Geral & Consolidação",
                f"DESCRIPTION:Semana reservada para consolidação de metas e simulados.{f'\\n\\n🔗 {base_url}/planner' if base_url else ''}",
                "STATUS:CONFIRMED",
                "END:VEVENT",
            ])
            continue

        for t_idx, topic in enumerate(topics):
            subtema = topic.get("subtema", "Aula")
            area = topic.get("area", "Geral")
            theory_h = topic.get("estimated_theory_hours", 1.0)
            practice_h = topic.get("estimated_practice_hours", 2.0)
            total_h = topic.get("estimated_hours", theory_h + practice_h)
            
            day_offset = t_idx % study_days_count
            topic_date = week_start_dt + timedelta(days=day_offset)
            date_str = topic_date.strftime("%Y%m%d")
            topic_id_clean = urllib.parse.quote(subtema[:30]).replace("%", "")

            # Duração REAL da aula (minutos calculados com precisão)
            duration_minutes = max(30, int(round(total_h * 60)))
            start_minutes = (8 * 60) + day_slot_minutes[day_offset]
            dt_start = topic_date.replace(hour=start_minutes // 60, minute=start_minutes % 60, second=0)
            dt_end = dt_start + timedelta(minutes=duration_minutes)
            day_slot_minutes[day_offset] += duration_minutes + 15

            start_str = dt_start.strftime("%Y%m%dT%H%M%S")
            end_str = dt_end.strftime("%Y%m%dT%H%M%S")
            uid_lecture = f"medquest-lec-{w_num}-{t_idx}-{topic_id_clean}-{user_id}-{date_str}@medquest"

            encoded_sub = urllib.parse.quote(subtema)
            # O subtema canônico é a chave de associação estável. Não inclua
            # a área aqui: nomes de área de bases antigas podem divergir da
            # normalização exibida no planner e zerar indevidamente a fila.
            study_url_text = f"\\n\\n🔗 Questões: {base_url}/estudar?subtema={encoded_sub}" if base_url else ""

            ics_lines.extend([
                "BEGIN:VEVENT",
                f"UID:{uid_lecture}",
                f"DTSTAMP:{now_dt}",
                f"DTSTART:{start_str}",
                f"DTEND:{end_str}",
                f"SUMMARY:[MedQuest] 📖 {subtema} ({area})",
                f"DESCRIPTION:📚 Carga: {total_h}h (Teoria: {theory_h}h + Questões: {practice_h}h)\\nSemana {w_num} • {area}{study_url_text}",
                "STATUS:CONFIRMED",
                "END:VEVENT",
            ])

            # Evento Individual de Revisão 24h (Dia D + 1, às 19:00 - 19:30)
            rev24_dt = topic_date + timedelta(days=1)
            rev24_start = rev24_dt.replace(hour=19, minute=0, second=0).strftime("%Y%m%dT%H%M%S")
            rev24_end = rev24_dt.replace(hour=19, minute=30, second=0).strftime("%Y%m%dT%H%M%S")
            uid_rev24 = f"medquest-rev24-{w_num}-{t_idx}-{topic_id_clean}-{user_id}-{date_str}@medquest"
            rev24_url_text = f"\\n\\n🔗 Revisar: {base_url}/revisao-ativa" if base_url else ""

            ics_lines.extend([
                "BEGIN:VEVENT",
                f"UID:{uid_rev24}",
                f"DTSTAMP:{now_dt}",
                f"DTSTART:{rev24_start}",
                f"DTEND:{rev24_end}",
                f"SUMMARY:[MedQuest] 🔄 Revisão 24h: {subtema}",
                f"DESCRIPTION:🔄 Revisão Ativa de 24h: {subtema}.{rev24_url_text}",
                "STATUS:CONFIRMED",
                "END:VEVENT",
            ])

            # Evento Individual de Revisão 7d (Dia D + 7, às 19:00 - 19:30)
            rev7_dt = topic_date + timedelta(days=7)
            rev7_start = rev7_dt.replace(hour=19, minute=0, second=0).strftime("%Y%m%dT%H%M%S")
            rev7_end = rev7_dt.replace(hour=19, minute=30, second=0).strftime("%Y%m%dT%H%M%S")
            uid_rev7 = f"medquest-rev7-{w_num}-{t_idx}-{topic_id_clean}-{user_id}-{date_str}@medquest"
            rev7_url_text = f"\\n\\n🔗 Revisar: {base_url}/revisao-ativa" if base_url else ""

            ics_lines.extend([
                "BEGIN:VEVENT",
                f"UID:{uid_rev7}",
                f"DTSTAMP:{now_dt}",
                f"DTSTART:{rev7_start}",
                f"DTEND:{rev7_end}",
                f"SUMMARY:[MedQuest] 🔄 Revisão 7d: {subtema}",
                f"DESCRIPTION:🔄 Revisão Ativa de 7 dias: {subtema}.{rev7_url_text}",
                "STATUS:CONFIRMED",
                "END:VEVENT",
            ])

            # Evento Individual de Revisão 30d (Dia D + 30, às 19:00 - 19:30)
            rev30_dt = topic_date + timedelta(days=30)
            rev30_start = rev30_dt.replace(hour=19, minute=0, second=0).strftime("%Y%m%dT%H%M%S")
            rev30_end = rev30_dt.replace(hour=19, minute=30, second=0).strftime("%Y%m%dT%H%M%S")
            uid_rev30 = f"medquest-rev30-{w_num}-{t_idx}-{topic_id_clean}-{user_id}-{date_str}@medquest"
            rev30_url_text = f"\\n\\n🔗 Revisar: {base_url}/revisao-ativa" if base_url else ""

            ics_lines.extend([
                "BEGIN:VEVENT",
                f"UID:{uid_rev30}",
                f"DTSTAMP:{now_dt}",
                f"DTSTART:{rev30_start}",
                f"DTEND:{rev30_end}",
                f"SUMMARY:[MedQuest] 🔄 Revisão 30d: {subtema}",
                f"DESCRIPTION:🔄 Revisão Ativa de 30 dias: {subtema}.{rev30_url_text}",
                "STATUS:CONFIRMED",
                "END:VEVENT",
            ])

    ics_lines.append("END:VCALENDAR")
    return "\r\n".join(ics_lines)


@bp.route("/planner/export/ics", methods=["GET"])
def export_ics():
    db = get_db()
    content = _generate_calendar_ics_content(db, g.user_id)
    return Response(
        content,
        mimetype="text/calendar; charset=utf-8",
        headers={
            "Content-Disposition": "attachment; filename=medquest_cronograma.ics"
        }
    )


@bp.route("/planner/calendar/feed", methods=["GET"])
def calendar_feed():
    db = get_db()
    # A identidade é definida exclusivamente pelo middleware de autenticação.
    # Aceitar user_id na URL permitia que um usuário autenticado lesse o plano
    # de qualquer outro usuário ao trocar o parâmetro.
    content = _generate_calendar_ics_content(db, g.user_id)
    return Response(
        content,
        mimetype="text/calendar; charset=utf-8",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Content-Disposition": "inline; filename=medquest_feed.ics"
        }
    )


