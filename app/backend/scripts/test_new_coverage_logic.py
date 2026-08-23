import json
import os
import sqlite3

def get_normalized_area(raw_area):
    if not raw_area: return "Outros"
    if "Cirurgia" in raw_area: return "Cirurgia"
    if "nica" in raw_area: return "Clínica Médica"
    if "Ginecologia" in raw_area: return "Ginecologia e Obstetrícia"
    if "Preventiva" in raw_area: return "Medicina Preventiva"
    if "Pediatria" in raw_area: return "Pediatria"
    return "Outros"

def build_coverage(db, user_id):
    # Load plannerData.json
    planner_data_path = os.path.join(os.path.dirname(__file__), "plannerData.json")
    try:
        with open(planner_data_path, "r", encoding="utf-8") as f:
            planner_meta = json.load(f)
    except Exception:
        planner_meta = []

    # Load katomart
    kat_path = os.path.join(os.path.dirname(__file__), "katomartCourseDurations.json")
    try:
        with open(kat_path, "r", encoding="utf-8") as f:
            kat = json.load(f)
    except Exception:
        kat = {}
    kat_subs = kat.get("subtemas", {})

    # 1. Get totals from questions table
    q_totals_rows = db.execute("""
        SELECT area, subtema, COUNT(*) AS n_questions
        FROM questions
        WHERE missing_alts = 0 AND area IS NOT NULL AND area != '' AND subtema IS NOT NULL AND subtema != ''
        GROUP BY area, subtema
    """).fetchall()
    
    q_map = {}
    for r in q_totals_rows:
        norm_a = get_normalized_area(r["area"])
        sub = r["subtema"]
        q_map[(norm_a, sub)] = r["n_questions"]

    # 2. Get user attempts
    user_rows = db.execute("""
        SELECT q.area, q.subtema,
               COUNT(DISTINCT a.question_id) AS answered,
               COUNT(a.id) AS attempts,
               COALESCE(SUM(a.is_correct), 0) AS correct
        FROM attempts a
        JOIN questions q ON q.id = a.question_id
        WHERE a.user_id = ? AND q.missing_alts = 0 AND q.area IS NOT NULL AND q.area != '' AND q.subtema IS NOT NULL AND q.subtema != ''
        GROUP BY q.area, q.subtema
    """, (user_id,)).fetchall()
    
    u_map = {}
    for r in user_rows:
        norm_a = get_normalized_area(r["area"])
        sub = r["subtema"]
        u_map[(norm_a, sub)] = {
            "answered": r["answered"],
            "attempts": r["attempts"],
            "correct": r["correct"]
        }

    # 3. Build coverage structured by canonical taxonomy
    areas_dict = {}
    
    # Process from planner_meta
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
            
            # Theory hours
            theme_theory = 0.0
            for s in db_subs:
                k = kat_subs.get(s, {})
                theme_theory += k.get("theory_hours", 1.5)
            theory_hours = round(theme_theory, 2)
            
            # Aggregate questions & attempts across dbSubtemas
            total_n_q = sum(q_map.get((area_name, s), 0) for s in db_subs)
            total_ans = sum(u_map.get((area_name, s), {}).get("answered", 0) for s in db_subs)
            total_att = sum(u_map.get((area_name, s), {}).get("attempts", 0) for s in db_subs)
            total_cor = sum(u_map.get((area_name, s), {}).get("correct", 0) for s in db_subs)

            accuracy = (total_cor / total_att) if total_att > 0 else None
            coverage_pct = (total_ans / total_n_q) if total_n_q > 0 else 0.0

            if total_ans == 0:
                status = "not_started"
            elif total_att >= 2 and accuracy is not None and accuracy >= 0.7 and coverage_pct >= 0.5:
                status = "mastered"
            elif total_att >= 2 and accuracy is not None and accuracy >= 0.7:
                status = "proficient"
            else:
                status = "in_progress"

            sub_item = {
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
                "theory_hours": theory_hours
            }

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

            area_obj["subtemas"].append(sub_item)

    area_order = ["Clínica Médica", "Cirurgia", "Ginecologia e Obstetrícia", "Pediatria", "Medicina Preventiva"]
    out = []
    for name in area_order:
        if name in areas_dict:
            a = areas_dict[name]
            a["accuracy"] = (a["correct"] / a["attempts"]) if a["attempts"] > 0 else None
            # Sort subtemas: HighYield first, then by n_questions DESC
            a["subtemas"].sort(key=lambda s: (not s["highYield"], -s["n_questions"]))
            out.append(a)

    for k, a in areas_dict.items():
        if k not in area_order:
            a["accuracy"] = (a["correct"] / a["attempts"]) if a["attempts"] > 0 else None
            a["subtemas"].sort(key=lambda s: (not s["highYield"], -s["n_questions"]))
            out.append(a)

    return {"areas": out}

conn = sqlite3.connect("app/backend/medquest.db")
conn.row_factory = sqlite3.Row
res = build_coverage(conn, "test-user")
print(f"Built coverage with {len(res['areas'])} areas:")
for a in res["areas"]:
    print(f" - {a['area']}: {a['n_subtemas']} subtemas | {a['n_questions']} questions | {a['high_yield_count']} high-yield")
