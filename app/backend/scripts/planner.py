import json
import math
import os
from datetime import datetime, timedelta

USP_WEIGHTS = {
    "Clínica Médica": 0.30,
    "Cirurgia": 0.20,
    "Pediatria": 0.15,
    "Ginecologia e Obstetrícia": 0.15,
    "Preventiva": 0.20
}

DEFAULT_PRACTICE_HOURS_PER_SUBTEMA = 2.0

def get_normalized_area(raw_area):
    if not raw_area: return "Outros"
    # Using substrings to avoid encoding issues with the SQLite output
    if "Cirurgia" in raw_area: return "Cirurgia"
    if "nica" in raw_area: return "Clínica Médica"
    if "Ginecologia" in raw_area: return "Ginecologia e Obstetrícia"
    if "Preventiva" in raw_area: return "Preventiva"
    if "Pediatria" in raw_area: return "Pediatria"
    return "Outros"

def generate_annual_plan(rows, start_date_str, exam_date_str, hours_per_week, intensive=False, user_progress=None):
    """
    Gera um plano de estudos fatiado por semanas com base no tempo disponível
    e no peso histórico das áreas na prova de Residência da USP.
    """
    try:
        start_date = datetime.fromisoformat(start_date_str.replace("Z", "+00:00"))
        exam_date = datetime.fromisoformat(exam_date_str.replace("Z", "+00:00"))
    except ValueError:
        return {"error": "Formato de data inválido."}

    # Normaliza para naive: exam_date costuma vir só com a data (sem timezone),
    # enquanto start_date pode vir com timezone (ex.: default gerado no backend).
    if start_date.tzinfo is not None:
        start_date = start_date.replace(tzinfo=None)
    if exam_date.tzinfo is not None:
        exam_date = exam_date.replace(tzinfo=None)

    total_weeks = math.ceil((exam_date - start_date).days / 7)
    if total_weeks <= 0:
        return {"error": "A data da prova deve ser no futuro."}
        
    # Cap at 5 years to prevent memory/rendering issues in frontend
    total_weeks = min(total_weeks, 260)

    # Carrega o mesmo catálogo pedagógico exibido no frontend.
    planner_data_path = os.path.join(os.path.dirname(__file__), "plannerData.json")
    try:
        with open(planner_data_path, "r", encoding="utf-8") as f:
            planner_meta = json.load(f)
    except Exception:
        planner_meta = []

    duration_catalog_path = os.path.join(os.path.dirname(__file__), "katomartCourseDurations.json")
    try:
        with open(duration_catalog_path, "r", encoding="utf-8") as f:
            duration_catalog = json.load(f)
    except Exception:
        duration_catalog = {}

    katomart_subtemas = duration_catalog.get("subtemas", {})
    practice_hours_per_subtema = duration_catalog.get("source", {}).get(
        "practice_hours_per_subtema",
        DEFAULT_PRACTICE_HOURS_PER_SUBTEMA,
    )

    # Cria o catálogo canônico de subtemas para fácil acesso.  O banco pode
    # conter classificações históricas, incompletas ou ainda não migradas; ele
    # só deve complementar as estatísticas dos temas, nunca definir o edital.
    meta_dict = {}
    for area_group in planner_meta:
        canonical_area = get_normalized_area(area_group.get("area"))
        for macro in area_group.get("macroThemes", []):
            is_high_yield = macro.get("highYield", False)
            # Fallback pedagógico para subtemas sem correspondência segura no
            # catálogo local de aulas do Katomart.
            fallback_theory_hours = max(1.0, len(macro.get("details", [])) * 0.25)

            for db_subtema in macro.get("dbSubtemas", []):
                course_match = katomart_subtemas.get(db_subtema)
                meta_dict[db_subtema] = {
                    "area": canonical_area,
                    "highYield": is_high_yield,
                    "theory_hours": (
                        course_match.get("theory_hours", fallback_theory_hours)
                        if course_match
                        else fallback_theory_hours
                    ),
                    "theory_source": "curriculum" if course_match else "pedagogical_estimate",
                    "course_module": course_match.get("module") if course_match else None,
                }

    # Consolida as estatísticas do banco apenas para os 170 temas do catálogo.
    # Isso também protege contra a mesma classificação aparecer em mais de uma
    # área durante uma migração de dados.
    row_stats = {
        subtema: {"q_count": 0, "subtopics": []}
        for subtema in meta_dict
    }
    for row in rows:
        subtema = row.get("subtema")
        if subtema not in row_stats:
            continue
        stats = row_stats[subtema]
        try:
            stats["q_count"] += int(row.get("q_count") or 0)
        except (TypeError, ValueError):
            pass
        topics = row.get("topics")
        if topics:
            stats["subtopics"].extend(topic for topic in str(topics).split(",") if topic)

    # Prepara exatamente os tópicos canônicos, calculando as horas de cada um.
    all_topics = []
    total_required_hours = 0.0

    if user_progress is None:
        user_progress = {}

    for subtema, meta in meta_dict.items():
        stats = row_stats[subtema]
        norm_area = meta["area"]
        q_count = stats["q_count"]
        
        prog = user_progress.get(subtema, {"ans_count": 0, "correct_count": 0, "attempts": 0})
        prog_dict = dict(prog) if prog else {}
        ans_count = prog_dict.get("ans_count") or 0
        attempts = prog_dict.get("attempts") or 0
        correct_count = prog_dict.get("correct_count") or 0
        acc = (correct_count / attempts) if attempts > 0 else 0
        
        remaining_q = max(0, q_count - ans_count)
        
        if intensive and not meta["highYield"]:
            continue
            
        theory_hours = meta["theory_hours"]
        practice_hours = practice_hours_per_subtema
        total_topic_hours = theory_hours + practice_hours
        
        total_required_hours += total_topic_hours
        
        # Priority score: High Yield = 100, plus area weight
        weight = USP_WEIGHTS.get(norm_area, 0.1)
        priority = 100 if meta["highYield"] else 0
        priority += weight * 10
        
        # Boost priority if accuracy is low (user needs to study this!)
        if attempts >= 3 and acc < 0.6:
            priority += 50
        
        all_topics.append({
            "area": norm_area,
            "subtema": subtema,
            "subtopics": stats["subtopics"],
            "questions_available": remaining_q,
            "estimated_theory_hours": round(theory_hours, 2),
            "estimated_practice_hours": round(practice_hours, 2),
            "estimated_hours": round(total_topic_hours, 2),
            "theory_source": meta["theory_source"],
            "course_module": meta["course_module"],
            "priority": priority
        })

    # Sort topics by priority (descending)
    all_topics.sort(key=lambda x: x["priority"], reverse=True)
    
    total_available_hours = total_weeks * hours_per_week
    warning_msg = None
    if total_required_hours > total_available_hours:
        warning_msg = f"Você tem {total_available_hours} horas disponíveis, mas precisa de {round(total_required_hours)} horas para cobrir {'este plano' if intensive else 'todo o edital'}."

    # Group by area
    topics_by_area = {}
    for t in all_topics:
        topics_by_area.setdefault(t['area'], []).append(t)

    plan = []
    
    for week in range(1, total_weeks + 1):
        week_topics = []
        current_week_hours = 0.0
        
        areas_sorted = sorted(USP_WEIGHTS.keys(), key=lambda x: USP_WEIGHTS[x], reverse=True)
        for area in topics_by_area:
            if area not in areas_sorted:
                areas_sorted.append(area)
        
        added_in_cycle = True
        while added_in_cycle and current_week_hours < hours_per_week:
            added_in_cycle = False
            for area in areas_sorted:
                if len(topics_by_area.get(area, [])) > 0:
                    topic = topics_by_area[area][0]
                    # Permite um pequeno estouro de até 1.5h na semana total (não por área!)
                    if current_week_hours + topic["estimated_hours"] <= hours_per_week + 1.5:
                        week_topics.append(topic)
                        current_week_hours += topic["estimated_hours"]
                        topics_by_area[area].pop(0)
                        added_in_cycle = True
                        
            # Se nenhum tópico coube, mas a semana está menos de 80% cheia, forçamos o menor tópico disponível
            if not added_in_cycle and current_week_hours < hours_per_week * 0.8:
                smallest = None
                smallest_area = None
                for area in areas_sorted:
                    if len(topics_by_area.get(area, [])) > 0:
                        t = topics_by_area[area][0]
                        if smallest is None or t["estimated_hours"] < smallest["estimated_hours"]:
                            smallest = t
                            smallest_area = area
                
                if smallest:
                    week_topics.append(smallest)
                    current_week_hours += smallest["estimated_hours"]
                    topics_by_area[smallest_area].pop(0)
                    added_in_cycle = True
                
        if not week_topics:
            break
            
        plan.append({
            "week": week,
            "date": (start_date + timedelta(weeks=week-1)).isoformat(),
            "topics": week_topics,
            "recommended_hours": hours_per_week,
            "allocated_hours": round(current_week_hours, 1)
        })
        
    result = {"plan": plan}
    if warning_msg:
        result["warning"] = warning_msg
        result["total_required_hours"] = round(total_required_hours)
        result["total_available_hours"] = round(total_available_hours)
        
    return result
