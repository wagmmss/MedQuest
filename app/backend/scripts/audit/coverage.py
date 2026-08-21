import sqlite3
import statistics
import json
from pathlib import Path
from .connection import rows

def _build_dist(db, query, max_details, keys_to_sort):
    data = rows(db, query)
    
    # Sort deterministically
    def sort_key(item):
        k = [-item["count"]]
        for key in keys_to_sort:
            val = item[key]
            if val is None: val = ""
            if isinstance(val, int): val = str(val).zfill(10)
            k.append(val)
        return tuple(k)
        
    data.sort(key=sort_key)
    
    total = len(data)
    if max_details and max_details > 0 and total > max_details:
        returned = data[:max_details]
        truncated = True
    else:
        returned = data
        truncated = False
        
    return {
        "total_items": total,
        "returned_items": len(returned),
        "truncated": truncated,
        "data": returned
    }

def check_coverage(db: sqlite3.Connection, scripts_dir: Path, low_limit: int = 20, max_details: int = 0) -> dict:
    area = _build_dist(db, "SELECT coalesce(area, 'Sem Área') as area, COUNT(*) as count FROM questions GROUP BY area", max_details, ["area"])
    institution = _build_dist(db, "SELECT coalesce(institution_code, 'Sem Instituição') as inst, COUNT(*) as count FROM questions GROUP BY institution_code", max_details, ["inst"])
    year = _build_dist(db, "SELECT coalesce(year, 0) as year, COUNT(*) as count FROM questions GROUP BY year", max_details, ["year"])
    
    area_inst = _build_dist(db, "SELECT coalesce(area, 'Sem Área') as area, coalesce(institution_code, 'Sem Inst') as inst, COUNT(*) as count FROM questions GROUP BY area, institution_code", max_details, ["area", "inst"])
    area_year = _build_dist(db, "SELECT coalesce(area, 'Sem Área') as area, coalesce(year, 0) as year, COUNT(*) as count FROM questions GROUP BY area, year", max_details, ["area", "year"])
    
    subtema = _build_dist(db, "SELECT coalesce(subtema, 'Sem Subtema') as subtema, COUNT(*) as count FROM questions GROUP BY subtema", max_details, ["subtema"])
    subtema_inst = _build_dist(db, "SELECT coalesce(subtema, 'Sem Subtema') as subtema, coalesce(institution_code, 'Sem Inst') as inst, COUNT(*) as count FROM questions GROUP BY subtema, institution_code", max_details, ["subtema", "inst"])
    subtema_year = _build_dist(db, "SELECT coalesce(subtema, 'Sem Subtema') as subtema, coalesce(year, 0) as year, COUNT(*) as count FROM questions GROUP BY subtema, year", max_details, ["subtema", "year"])
    
    raw_subtema = rows(db, "SELECT coalesce(subtema, 'Sem Subtema') as subtema, COUNT(*) as count FROM questions GROUP BY subtema")
    subtema_counts = [r["count"] for r in raw_subtema if r["subtema"] != 'Sem Subtema']
    median = statistics.median(subtema_counts) if subtema_counts else 0
    
    try:
        p25 = statistics.quantiles(subtema_counts, n=4)[0] if len(subtema_counts) >= 4 else 0
        p75 = statistics.quantiles(subtema_counts, n=4)[2] if len(subtema_counts) >= 4 else 0
    except statistics.StatisticsError:
        p25 = p75 = 0
        
    under_5 = sorted([r["subtema"] for r in raw_subtema if r["subtema"] != 'Sem Subtema' and r["count"] < 5])
    under_10 = sorted([r["subtema"] for r in raw_subtema if r["subtema"] != 'Sem Subtema' and r["count"] < 10])
    under_20 = sorted([r["subtema"] for r in raw_subtema if r["subtema"] != 'Sem Subtema' and r["count"] < 20])
    under_limit = sorted([r["subtema"] for r in raw_subtema if r["subtema"] != 'Sem Subtema' and r["count"] < low_limit])
    
    # Subtemas in only one institution
    raw_subtema_inst = rows(db, "SELECT coalesce(subtema, 'Sem Subtema') as subtema, coalesce(institution_code, 'Sem Inst') as inst FROM questions GROUP BY subtema, institution_code")
    sub_inst_counts = {}
    for r in raw_subtema_inst:
        s = r["subtema"]
        if s == 'Sem Subtema': continue
        if s not in sub_inst_counts: sub_inst_counts[s] = []
        sub_inst_counts[s].append(r["inst"])
        
    single_institution_subtemas = {k: v[0] for k, v in sorted(sub_inst_counts.items()) if len(v) == 1}
    
    # Subtemas sem questoes recentes (max year < 2023)
    raw_subtema_year = rows(db, "SELECT coalesce(subtema, 'Sem Subtema') as subtema, coalesce(year, 0) as year FROM questions")
    sub_year_max = {}
    missing_year_subtemas = set()
    for r in raw_subtema_year:
        s = r["subtema"]
        if s == 'Sem Subtema': continue
        y = r["year"]
        if y == 0:
            missing_year_subtemas.add(s)
            continue
            
        if s not in sub_year_max or y > sub_year_max[s]:
            sub_year_max[s] = y
            
    no_recent_questions = {k: v for k, v in sorted(sub_year_max.items()) if v < 2023}
    
    # High Yield coverage
    high_yield_subtemas = set()
    planner_file = scripts_dir / "plannerData.json"
    if planner_file.is_file():
        with planner_file.open("r", encoding="utf-8") as f:
            planner_data = json.load(f)
            for a in planner_data:
                for m in a.get("macroThemes", []):
                    if m.get("highYield"):
                        for s in m.get("dbSubtemas", []):
                            high_yield_subtemas.add(s)
                            
    high_yield_low_coverage = []
    for s in sorted(list(high_yield_subtemas)):
        c = next((r["count"] for r in raw_subtema if r["subtema"] == s), 0)
        if c < low_limit:
            high_yield_low_coverage.append({"subtema": s, "count": c})
            
    high_yield_low_coverage.sort(key=lambda x: (x["count"], x["subtema"]))

    return {
        "distributions": {
            "area": area,
            "institution": institution,
            "year": year,
            "area_institution": area_inst,
            "area_year": area_year,
            "subtema": subtema,
            "subtema_institution": subtema_inst,
            "subtema_year": subtema_year
        },
        "stats": {
            "median_questions_per_subtema": median,
            "p25": p25,
            "p75": p75
        },
        "gaps": {
            "under_5_questions": under_5,
            "under_10_questions": under_10,
            "under_20_questions": under_20,
            f"under_{low_limit}_questions": under_limit,
            "single_institution": single_institution_subtemas,
            "missing_year": sorted(list(missing_year_subtemas)),
            "no_recent_questions_before_2023": no_recent_questions,
            f"high_yield_under_{low_limit}": high_yield_low_coverage
        }
    }
