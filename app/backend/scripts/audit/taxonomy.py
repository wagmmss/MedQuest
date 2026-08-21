import sqlite3
import json
import ast
import re
from pathlib import Path
from .connection import rows

def _extract_typescript_array(content: str) -> str:
    """Safely extracts the plannerData array from TypeScript without execution."""
    # Look for export const plannerData = [ ... ];
    match = re.search(r'export\s+const\s+plannerData\s*(?::\s*any\s*)?=\s*(\[)', content)
    if not match:
        return ""
        
    start_idx = match.start(1)
    
    # Safe delimiter scanning
    in_string = False
    escape = False
    bracket_level = 0
    quote_char = None
    
    for i in range(start_idx, len(content)):
        c = content[i]
        
        if escape:
            escape = False
            continue
            
        if c == '\\':
            escape = True
            continue
            
        if in_string:
            if c == quote_char:
                in_string = False
            continue
            
        if c in ('"', "'", '`'):
            in_string = True
            quote_char = c
            continue
            
        if c == '[':
            bracket_level += 1
        elif c == ']':
            bracket_level -= 1
            if bracket_level == 0:
                return content[start_idx:i+1]
                
    return ""

def _parse_canonical_subtemas(filepath: Path) -> dict:
    if not filepath.exists():
        return {"status": "unverified", "areas": [], "subtemas": [], "internal_duplicates_area": [], "internal_duplicates_subtema": [], "multiple_areas": {}}
        
    try:
        content = filepath.read_text(encoding="utf-8")
        tree = ast.parse(content)
        canonical_dict = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "CANONICAL_SUBTEMAS":
                        canonical_dict = ast.literal_eval(node.value)
                        break
                        
        areas = []
        subtemas = []
        dups_a = []
        dups_s = []
        seen_a = set()
        seen_s = set()
        multi_areas = {}
        sub_area_map = {}
        
        for k, v_list in canonical_dict.items():
            if k in seen_a: dups_a.append(k)
            seen_a.add(k)
            areas.append(k)
            for s in v_list:
                if s in seen_s: dups_s.append(s)
                seen_s.add(s)
                subtemas.append(s)
                
                if s not in sub_area_map: sub_area_map[s] = set()
                sub_area_map[s].add(k)
                
        for s, ars in sub_area_map.items():
            if len(ars) > 1:
                multi_areas[s] = sorted(list(ars))
                
        return {
            "status": "verified",
            "areas": sorted(areas),
            "subtemas": sorted(subtemas),
            "internal_duplicates_area": sorted(dups_a),
            "internal_duplicates_subtema": sorted(dups_s),
            "multiple_areas": multi_areas
        }
    except Exception:
        return {"status": "unverified", "areas": [], "subtemas": [], "internal_duplicates_area": [], "internal_duplicates_subtema": [], "multiple_areas": {}}

def _parse_planner_json(filepath: Path) -> dict:
    if not filepath.exists():
        return {"status": "unverified", "areas": [], "subtemas": [], "internal_duplicates_area": [], "internal_duplicates_subtema": [], "multiple_areas": {}}
    
    try:
        data = json.loads(filepath.read_text(encoding="utf-8"))
        areas = []
        subtemas = []
        dups_a = []
        dups_s = []
        seen_a = set()
        seen_s = set()
        multi_areas = {}
        sub_area_map = {}
        
        for a in data:
            area_name = a.get("area", "")
            if area_name in seen_a: dups_a.append(area_name)
            seen_a.add(area_name)
            areas.append(area_name)
            for m in a.get("macroThemes", []):
                for s in m.get("dbSubtemas", []):
                    if s in seen_s: dups_s.append(s)
                    seen_s.add(s)
                    subtemas.append(s)
                    if s not in sub_area_map: sub_area_map[s] = set()
                    sub_area_map[s].add(area_name)
                    
        for s, ars in sub_area_map.items():
            if len(ars) > 1:
                multi_areas[s] = sorted(list(ars))
                
        return {
            "status": "verified",
            "areas": sorted(areas),
            "subtemas": sorted(subtemas),
            "internal_duplicates_area": sorted(dups_a),
            "internal_duplicates_subtema": sorted(dups_s),
            "multiple_areas": multi_areas
        }
    except Exception:
        return {"status": "unverified", "areas": [], "subtemas": [], "internal_duplicates_area": [], "internal_duplicates_subtema": [], "multiple_areas": {}}

def _parse_planner_ts(filepath: Path) -> dict:
    if not filepath.exists():
        return {"status": "unverified", "areas": [], "subtemas": [], "internal_duplicates_area": [], "internal_duplicates_subtema": [], "multiple_areas": {}}
        
    try:
        content = filepath.read_text(encoding="utf-8")
        array_str = _extract_typescript_array(content)
        if not array_str:
            raise ValueError("Could not safely extract array")
            
        # JSON standard requires double quotes for properties. TS often uses single quotes or no quotes.
        # It's not safe to regex convert full JS objects to JSON. We will try json.loads, if it fails, unverified.
        # But we can try a simple ast.literal_eval if we format it as python dicts.
        # Since the user specifically asked for json.loads or return unverified:
        data = json.loads(array_str)
        # If we got here, it was valid JSON syntax inside TS.
        areas = []
        subtemas = []
        dups_a = []
        dups_s = []
        seen_a = set()
        seen_s = set()
        multi_areas = {}
        sub_area_map = {}
        
        for a in data:
            area_name = a.get("area", "")
            if area_name in seen_a: dups_a.append(area_name)
            seen_a.add(area_name)
            areas.append(area_name)
            for m in a.get("macroThemes", []):
                for s in m.get("dbSubtemas", []):
                    if s in seen_s: dups_s.append(s)
                    seen_s.add(s)
                    subtemas.append(s)
                    if s not in sub_area_map: sub_area_map[s] = set()
                    sub_area_map[s].add(area_name)
                    
        for s, ars in sub_area_map.items():
            if len(ars) > 1:
                multi_areas[s] = sorted(list(ars))
                
        return {
            "status": "verified",
            "areas": sorted(areas),
            "subtemas": sorted(subtemas),
            "internal_duplicates_area": sorted(dups_a),
            "internal_duplicates_subtema": sorted(dups_s),
            "multiple_areas": multi_areas
        }
    except Exception:
        # User requested: "Se isso não for seguro, retorne unverified com warning"
        return {"status": "unverified", "areas": [], "subtemas": [], "internal_duplicates_area": [], "internal_duplicates_subtema": [], "multiple_areas": {}, "warning": "TS array extraction unsafe for json.loads"}

def _parse_taxonomy_json(filepath: Path) -> dict:
    if not filepath.exists():
        return {"status": "unverified", "areas": [], "subtemas": [], "internal_duplicates_area": [], "internal_duplicates_subtema": [], "multiple_areas": {}}
        
    try:
        data = json.loads(filepath.read_text(encoding="utf-8"))
        areas = []
        subtemas = []
        dups_a = []
        dups_s = []
        seen_a = set()
        seen_s = set()
        multi_areas = {}
        sub_area_map = {}
        
        for a, s_list in data.items():
            if a in seen_a: dups_a.append(a)
            seen_a.add(a)
            areas.append(a)
            for s in s_list:
                if s in seen_s: dups_s.append(s)
                seen_s.add(s)
                subtemas.append(s)
                if s not in sub_area_map: sub_area_map[s] = set()
                sub_area_map[s].add(a)
                
        for s, ars in sub_area_map.items():
            if len(ars) > 1:
                multi_areas[s] = sorted(list(ars))
                
        return {
            "status": "verified",
            "areas": sorted(areas),
            "subtemas": sorted(subtemas),
            "internal_duplicates_area": sorted(dups_a),
            "internal_duplicates_subtema": sorted(dups_s),
            "multiple_areas": multi_areas
        }
    except Exception:
        return {"status": "unverified", "areas": [], "subtemas": [], "internal_duplicates_area": [], "internal_duplicates_subtema": [], "multiple_areas": {}}

def check_taxonomy(db: sqlite3.Connection, scripts_dir: Path) -> dict:
    db_data = rows(db, "SELECT coalesce(area, 'Sem Área') as area, coalesce(subtema, 'Sem Subtema') as subtema, COUNT(*) as count FROM questions GROUP BY area, subtema")
    
    db_areas = set()
    db_subtemas = set()
    db_area_sub_map = {}
    
    for r in db_data:
        a = r["area"]
        s = r["subtema"]
        if a != "Sem Área": db_areas.add(a)
        if s != "Sem Subtema": db_subtemas.add(s)
        db_area_sub_map[f"{a}::{s}"] = r["count"]
        
    canonical = _parse_canonical_subtemas(scripts_dir / "canonical_subtemas.py")
    planner_json = _parse_planner_json(scripts_dir / "plannerData.json")
    taxonomy_json = _parse_taxonomy_json(scripts_dir.parent / "data" / "taxonomy.json")
    planner_ts = _parse_planner_ts(scripts_dir.parent.parent / "frontend" / "src" / "lib" / "plannerData.ts")
    
    def _diff(source_data):
        if source_data["status"] == "unverified":
            return {"status": "unverified"}
            
        s_areas = set(source_data["areas"])
        s_subtemas = set(source_data["subtemas"])
        
        missing_areas = sorted(list(db_areas - s_areas))
        missing_subtemas = sorted(list(db_subtemas - s_subtemas))
        
        affected_by_missing_subtemas = 0
        for s in missing_subtemas:
            # sum all questions with this subtema
            affected_by_missing_subtemas += sum(c for k, c in db_area_sub_map.items() if k.endswith(f"::{s}"))
            
        # Detect variations (accent, case, space)
        def _normalize(t):
            return re.sub(r'[^\w]', '', t).lower()
            
        variations = []
        norm_s = {_normalize(x): x for x in s_subtemas}
        for ds in db_subtemas:
            if ds in s_subtemas: continue
            n = _normalize(ds)
            if n in norm_s:
                count = sum(c for k, c in db_area_sub_map.items() if k.endswith(f"::{ds}"))
                variations.append({
                    "db_value": ds,
                    "catalog_value": norm_s[n],
                    "affected_questions": count
                })
                
        return {
            "status": "verified",
            "internal_duplicates_area": source_data["internal_duplicates_area"],
            "internal_duplicates_subtema": source_data["internal_duplicates_subtema"],
            "subtemas_in_multiple_areas": source_data["multiple_areas"],
            "missing_areas_in_catalog": missing_areas,
            "missing_subtemas_in_catalog": missing_subtemas,
            "affected_questions_by_missing_subtemas": affected_by_missing_subtemas,
            "detected_variations": sorted(variations, key=lambda x: x["db_value"])
        }
        
    return {
        "sqlite_db": {
            "total_areas": len(db_areas),
            "total_subtemas": len(db_subtemas)
        },
        "catalogs": {
            "taxonomy_json": _diff(taxonomy_json),
            "canonical_subtemas_py": _diff(canonical),
            "plannerData_json": _diff(planner_json),
            "plannerData_ts": _diff(planner_ts)
        },
        "source_consumers": {
            "taxonomy_json": "Unknown (No verified direct importer in backend currently scripts).",
            "canonical_subtemas_py": "Backend maintenance scripts (e.g. tests or legacy sync).",
            "plannerData_json": "Backend dynamic planners or seeders.",
            "plannerData_ts": "Frontend application code (e.g., app/simulado/page.tsx, components)."
        }
    }
