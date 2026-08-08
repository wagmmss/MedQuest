from datetime import datetime, timedelta
import sqlite3
import math

USP_WEIGHTS = {
    "Clínica Médica": 0.30,
    "Cirurgia": 0.20,
    "Pediatria": 0.15,
    "Ginecologia e Obstetrícia": 0.15,
    "Preventiva": 0.20
}

def generate_annual_plan(db_path, start_date_str, exam_date_str, hours_per_week):
    """
    Gera um plano de estudos fatiado por semanas com base no tempo disponível
    e no peso histórico das áreas na prova de Residência da USP.
    """
    start_date = datetime.fromisoformat(start_date_str)
    exam_date = datetime.fromisoformat(exam_date_str)

    # Normaliza para naive: exam_date costuma vir só com a data (sem timezone),
    # enquanto start_date pode vir com timezone (ex.: default gerado no backend).
    if start_date.tzinfo is not None:
        start_date = start_date.replace(tzinfo=None)
    if exam_date.tzinfo is not None:
        exam_date = exam_date.replace(tzinfo=None)

    total_weeks = math.ceil((exam_date - start_date).days / 7)
    if total_weeks <= 0:
        return {"error": "A data da prova deve ser no futuro."}

    # Fetch available subtopics per area
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT area, subtema, COUNT(id) as q_count 
        FROM questions 
        WHERE area IS NOT NULL AND subtema IS NOT NULL
        GROUP BY area, subtema
    """).fetchall()
    conn.close()

    area_subtemas = {}
    for r in rows:
        area = r['area']
        if area not in area_subtemas:
            area_subtemas[area] = []
        area_subtemas[area].append({"name": r['subtema'], "questions": r['q_count']})

    # Simplistic slicing algorithm:
    # Distribute topics across total_weeks based on area weight.
    
    plan = []
    for week in range(1, total_weeks + 1):
        week_topics = []
        for area, weight in USP_WEIGHTS.items():
            if area in area_subtemas and len(area_subtemas[area]) > 0:
                # pick a topic proportionally
                # (For the sake of MVP, we just take one topic from the highest weight areas)
                if len(week_topics) < 3: # 3 topics per week
                    topic = area_subtemas[area].pop(0)
                    week_topics.append({
                        "area": area,
                        "subtema": topic["name"],
                        "questions_available": topic["questions"]
                    })
                    
        plan.append({
            "week": week,
            "date": (start_date + timedelta(weeks=week-1)).isoformat(),
            "topics": week_topics,
            "recommended_hours": hours_per_week
        })

    return plan
