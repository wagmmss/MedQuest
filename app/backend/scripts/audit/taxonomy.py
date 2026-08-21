"""Safe, non-executing taxonomy source readers and comparisons."""
from __future__ import annotations

import ast
import json
import re
import sqlite3
import unicodedata
from pathlib import Path

from .connection import rows


def _normalize(value: str) -> str:
    value = re.sub(r"[\u200b\u200c\u200d\u2060\ufeff]", "", str(value or ""))
    value = "".join(char for char in unicodedata.normalize("NFD", value) if unicodedata.category(char) != "Mn")
    return re.sub(r"\s+", " ", value).strip().casefold()


def _validate_catalog(value: object) -> list[dict]:
    if not isinstance(value, list):
        raise ValueError("catalog root must be a list")
    for area in value:
        if not isinstance(area, dict) or not isinstance(area.get("area"), str) or not isinstance(area.get("macroThemes", []), list):
            raise ValueError("invalid area entry")
        for macro in area.get("macroThemes", []):
            if not isinstance(macro, dict) or not isinstance(macro.get("dbSubtemas", []), list):
                raise ValueError("invalid macro theme")
            if not all(isinstance(item, str) for item in macro.get("dbSubtemas", [])):
                raise ValueError("dbSubtemas must contain strings")
    return value


def _load_json(path: Path) -> dict:
    try:
        return {"status": "verified", "data": _validate_catalog(json.loads(path.read_text(encoding="utf-8"))), "warnings": []}
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        return {"status": "unverified", "data": [], "warnings": [f"{path}: {exc}"]}


def _canonical_to_catalog(value: object) -> list[dict]:
    if not isinstance(value, dict):
        raise ValueError("CANONICAL must be a dictionary")
    catalog = []
    for area, subtemas in value.items():
        if not isinstance(area, str) or not isinstance(subtemas, (list, tuple)) or not all(isinstance(item, str) for item in subtemas):
            raise ValueError("CANONICAL must map strings to lists/tuples of strings")
        catalog.append({"area": area, "macroThemes": [{"dbSubtemas": list(subtemas)}]})
    return catalog


def load_canonical_safely(path: Path) -> dict:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        candidates = []
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "CANONICAL" for target in node.targets):
                candidates.append(node.value)
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == "CANONICAL":
                candidates.append(node.value)
        if len(candidates) != 1 or candidates[0] is None:
            raise ValueError("expected exactly one CANONICAL assignment")
        value = ast.literal_eval(candidates[0])
        return {"status": "verified", "data": _canonical_to_catalog(value), "warnings": []}
    except (OSError, UnicodeError, SyntaxError, ValueError) as exc:
        return {"status": "unverified", "data": [], "warnings": [f"{path}: {exc}"]}


def _scan_balanced_json(source: str, start: int) -> str:
    while start < len(source) and source[start].isspace():
        start += 1
    if start >= len(source) or source[start] not in "[{":
        raise ValueError("plannerData assignment does not start with JSON array/object")
    pairs = {"[": "]", "{": "}"}
    stack: list[str] = []
    quote: str | None = None
    escaped = False
    for index in range(start, len(source)):
        char = source[index]
        if quote is not None:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in ('"', "'"):
            quote = char
        elif char in pairs:
            stack.append(pairs[char])
        elif char in "]}":
            if not stack or char != stack.pop():
                raise ValueError("unbalanced plannerData delimiters")
            if not stack:
                return source[start:index + 1]
    raise ValueError("unterminated plannerData JSON")


def load_planner_ts_safely(path: Path) -> dict:
    try:
        source = path.read_text(encoding="utf-8")
        match = re.search(r"\b(?:export\s+)?const\s+plannerData\s*=", source)
        if not match:
            raise ValueError("plannerData const assignment not found")
        payload = _scan_balanced_json(source, match.end())
        return {"status": "verified", "data": _validate_catalog(json.loads(payload)), "warnings": []}
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        return {"status": "unverified", "data": [], "warnings": [f"{path}: {exc}"]}


def _flatten(catalog: list[dict]) -> tuple[set[str], set[str], dict[str, set[str]]]:
    areas: set[str] = set()
    subtemas: set[str] = set()
    mapping: dict[str, set[str]] = {}
    for area_group in catalog:
        area = area_group["area"]
        areas.add(area)
        for macro in area_group.get("macroThemes", []):
            for subtema in macro.get("dbSubtemas", []):
                subtemas.add(subtema)
                mapping.setdefault(subtema, set()).add(area)
    return areas, subtemas, mapping


def _compare_source(source: dict, db_areas: set[str], db_subtemas: set[str], db_counts: dict[str, int]) -> dict:
    areas, subtemas, mapping = _flatten(source["data"])
    return {
        "status": source["status"],
        "warnings": source["warnings"],
        "catalog_areas_count": len(areas),
        "catalog_subtemas_count": len(subtemas),
        "unmapped_db_areas": sorted(db_areas - areas),
        "unused_catalog_areas": sorted(areas - db_areas),
        "unmapped_db_subtemas": sorted(({"subtema": item, "count": db_counts[item]} for item in db_subtemas - subtemas), key=lambda item: (-item["count"], item["subtema"])),
        "unused_catalog_subtemas": sorted(subtemas - db_subtemas),
        "multi_area_catalog_subtemas": {key: sorted(value) for key, value in sorted(mapping.items()) if len(value) > 1},
    }


def check_taxonomy(db: sqlite3.Connection, scripts_dir: Path) -> dict:
    repo_root = scripts_dir.resolve().parents[2]
    paths = {
        "taxonomy_json": scripts_dir.parent / "data" / "taxonomy.json",
        "canonical_subtemas_py": scripts_dir / "canonical_subtemas.py",
        "plannerData_json": scripts_dir / "plannerData.json",
        "plannerData_ts": repo_root / "app" / "frontend" / "src" / "lib" / "plannerData.ts",
    }
    loaded = {
        "taxonomy_json": _load_json(paths["taxonomy_json"]),
        "canonical_subtemas_py": load_canonical_safely(paths["canonical_subtemas_py"]),
        "plannerData_json": _load_json(paths["plannerData_json"]),
        "plannerData_ts": load_planner_ts_safely(paths["plannerData_ts"]),
    }
    db_rows = rows(db, "SELECT area, subtema, COUNT(*) AS count FROM questions WHERE trim(COALESCE(area, '')) != '' OR trim(COALESCE(subtema, '')) != '' GROUP BY area, subtema ORDER BY area, subtema")
    db_areas = {str(item["area"]).strip() for item in db_rows if str(item["area"] or "").strip()}
    db_subtemas = {str(item["subtema"]).strip() for item in db_rows if str(item["subtema"] or "").strip()}
    db_counts = {subtema: 0 for subtema in db_subtemas}
    db_mapping: dict[str, set[str]] = {}
    for item in db_rows:
        area, subtema = str(item["area"] or "").strip(), str(item["subtema"] or "").strip()
        if subtema:
            db_counts[subtema] += item["count"]
            db_mapping.setdefault(subtema, set()).add(area)
    normalized: dict[str, list[str]] = {}
    for subtema in db_subtemas:
        normalized.setdefault(_normalize(subtema), []).append(subtema)
    warnings = [warning for source in loaded.values() for warning in source["warnings"]]
    return {
        "db_areas": sorted(db_areas),
        "db_subtemas_count": len(db_subtemas),
        "variations_in_db": {key: sorted(value) for key, value in sorted(normalized.items()) if len(value) > 1},
        "multi_area_in_db": {key: sorted(value) for key, value in sorted(db_mapping.items()) if len(value) > 1},
        "sources": {name: {"path": str(paths[name].resolve()), "consumers": {
            "taxonomy_json": ["backend/data/taxonomy.json"],
            "canonical_subtemas_py": ["backend reclassification scripts"],
            "plannerData_json": ["backend/scripts/planner.py"],
            "plannerData_ts": ["frontend PlannerClient.tsx"],
        }[name], **_compare_source(source, db_areas, db_subtemas, db_counts)} for name, source in loaded.items()},
        "warnings": warnings,
    }
