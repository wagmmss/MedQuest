"""Coverage distributions and low-volume content gaps."""
from __future__ import annotations

import json
import sqlite3
import statistics
from pathlib import Path

from .connection import rows


def _distribution(db: sqlite3.Connection, query: str, dimensions: list[str], max_details: int) -> dict:
    data = rows(db, query)
    data.sort(key=lambda item: (-item["count"], *(str(item[key] if item[key] is not None else "") for key in dimensions)))
    total = len(data)
    limited = data[:max_details] if max_details > 0 else data
    return {"total_items": total, "returned_items": len(limited), "truncated": len(limited) < total, "data": limited}


def check_coverage(db: sqlite3.Connection, scripts_dir: Path, low_limit: int = 20, max_details: int = 0) -> dict:
    specs = {
        "area": ("SELECT COALESCE(area, 'Sem Área') AS area, COUNT(*) AS count FROM questions GROUP BY area", ["area"]),
        "institution": ("SELECT COALESCE(institution_code, 'Sem Instituição') AS institution, COUNT(*) AS count FROM questions GROUP BY institution_code", ["institution"]),
        "year": ("SELECT COALESCE(year, 0) AS year, COUNT(*) AS count FROM questions GROUP BY year", ["year"]),
        "area_institution": ("SELECT COALESCE(area, 'Sem Área') AS area, COALESCE(institution_code, 'Sem Instituição') AS institution, COUNT(*) AS count FROM questions GROUP BY area, institution_code", ["area", "institution"]),
        "area_year": ("SELECT COALESCE(area, 'Sem Área') AS area, COALESCE(year, 0) AS year, COUNT(*) AS count FROM questions GROUP BY area, year", ["area", "year"]),
        "subtema": ("SELECT COALESCE(subtema, 'Sem Subtema') AS subtema, COUNT(*) AS count FROM questions GROUP BY subtema", ["subtema"]),
        "subtema_institution": ("SELECT COALESCE(subtema, 'Sem Subtema') AS subtema, COALESCE(institution_code, 'Sem Instituição') AS institution, COUNT(*) AS count FROM questions GROUP BY subtema, institution_code", ["subtema", "institution"]),
        "subtema_year": ("SELECT COALESCE(subtema, 'Sem Subtema') AS subtema, COALESCE(year, 0) AS year, COUNT(*) AS count FROM questions GROUP BY subtema, year", ["subtema", "year"]),
    }
    distributions = {name: _distribution(db, query, dimensions, max_details) for name, (query, dimensions) in specs.items()}
    subtemas = rows(db, "SELECT subtema, COUNT(*) AS count, COUNT(DISTINCT institution_code) AS institutions, MAX(year) AS latest_year FROM questions WHERE trim(COALESCE(subtema, '')) != '' GROUP BY subtema ORDER BY subtema")
    counts = [item["count"] for item in subtemas]
    under = lambda limit: [{"subtema": item["subtema"], "count": item["count"]} for item in subtemas if item["count"] < limit]

    high_yield: set[str] = set()
    try:
        planner = json.loads((scripts_dir / "plannerData.json").read_text(encoding="utf-8"))
        for area in planner:
            for macro in area.get("macroThemes", []):
                if macro.get("highYield"):
                    high_yield.update(macro.get("dbSubtemas", []))
    except (OSError, UnicodeError, json.JSONDecodeError):
        pass
    count_by_subtema = {item["subtema"]: item["count"] for item in subtemas}
    high_yield_low = sorted(({"subtema": name, "count": count_by_subtema.get(name, 0)} for name in high_yield if count_by_subtema.get(name, 0) < low_limit), key=lambda item: (item["count"], item["subtema"]))
    quartiles = statistics.quantiles(counts, n=4) if len(counts) >= 4 else [0, 0, 0]
    return {
        "distributions": distributions,
        "stats": {"median_questions_per_subtema": statistics.median(counts) if counts else 0, "p25": quartiles[0], "p75": quartiles[2]},
        "gaps": {
            "under_5_questions": under(5),
            "under_10_questions": under(10),
            "under_20_questions": under(20),
            f"under_{low_limit}_questions": under(low_limit),
            "single_institution": [{"subtema": item["subtema"]} for item in subtemas if item["institutions"] == 1],
            "missing_year": [{"subtema": item["subtema"]} for item in subtemas if item["latest_year"] is None],
            "no_recent_questions_before_2023": [{"subtema": item["subtema"], "latest_year": item["latest_year"]} for item in subtemas if item["latest_year"] is not None and item["latest_year"] < 2023],
            f"high_yield_under_{low_limit}": high_yield_low,
        },
    }
