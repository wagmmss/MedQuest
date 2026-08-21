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

    # Cria dicionário de subtemas para fácil acesso.
    meta_dict = {}
    for area_group in planner_meta:
        for macro in area_group.get("macroThemes", []):
            is_high_yield = macro.get("highYield", False)
            # Cada objetivo representa cerca de 15 min de teoria, com piso de
            # 1 h por tema para que tópicos curtos não desapareçam do plano.
            theory_hours = max(1.0, len(macro.get("details", [])) * 0.25)

            for db_subtema in macro.get("dbSubtemas", []):
                meta_dict[db_subtema] = {
                    "highYield": is_high_yield,
                    "theory_hours": theory_hours
                }

    # Rows now provided via argument

    # Prepara a lista de todos os tópicos disponíveis, calculando as horas de cada um
    all_topics = []
    total_required_hours = 0.0

    if user_progress is None:
        user_progress = {}

    for r in rows:
        raw_area = r['area']
        norm_area = get_normalized_area(raw_area)
        subtema = r['subtema']
        q_count = r['q_count']
        
        prog = user_progress.get(subtema, {"ans_count": 0, "correct_count": 0, "attempts": 0})
        prog_dict = dict(prog) if prog else {}
        ans_count = prog_dict.get("ans_count") or 0
        attempts = prog_dict.get("attempts") or 0
        correct_count = prog_dict.get("correct_count") or 0
        acc = (correct_count / attempts) if attempts > 0 else 0
        
        remaining_q = max(0, q_count - ans_count)
        
        meta = meta_dict.get(subtema, {"highYield": False, "theory_hours": 1.0})
        
        if intensive and not meta["highYield"]:
            continue
            
        theory_hours = meta["theory_hours"]
        # Reduce theory time significantly if user is already highly proficient
        if ans_count >= 5 and acc >= 0.7:
            theory_hours = theory_hours * 0.3
            
        # 3 mins (0.05h) per question
        practice_hours = remaining_q * 0.05
        total_topic_hours = theory_hours + practice_hours
        
        # Skip if topic requires almost no time and user is already very proficient
        if total_topic_hours < 0.2 and acc >= 0.7:
            continue
            
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
            "questions_available": remaining_q,
            "estimated_hours": total_topic_hours,
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
