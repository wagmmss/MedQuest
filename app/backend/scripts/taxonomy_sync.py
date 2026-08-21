"""Compile the canonical taxonomy into deterministic MedQuest consumer artifacts.

``app/backend/data/taxonomy.json`` is the pedagogical source of truth. Existing
subtema IDs are immutable; new IDs are allocated deterministically per area.
The command is check-only by default and writes files only with ``--apply``.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

try:
    from audit.taxonomy import _scan_balanced_json, _validate_catalog
except ModuleNotFoundError:
    from scripts.audit.taxonomy import _scan_balanced_json, _validate_catalog

SCRIPTS_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPTS_DIR.parent
REPO_ROOT = BACKEND_DIR.parents[1]
TAXONOMY_PATH = BACKEND_DIR / "data" / "taxonomy.json"
SUBTEMA_MAP_PATH = BACKEND_DIR / "data" / "subtema_map.json"
PLANNER_JSON_PATH = SCRIPTS_DIR / "plannerData.json"
PLANNER_TS_PATH = REPO_ROOT / "app" / "frontend" / "src" / "lib" / "plannerData.ts"

AREA_PREFIXES = {
    "Medicina Preventiva": "MED",
    "Medicina Preventiva e Social": "MED",
    "Pediatria": "PED",
    "Ginecologia e Obstetrícia": "GIN",
    "Cirurgia": "CIR",
    "Cirurgia Geral": "CIR",
    "Clínica Médica": "CLÍ",
}


def load_taxonomy(path: Path = TAXONOMY_PATH) -> list[dict]:
    return _validate_catalog(json.loads(path.read_text(encoding="utf-8")))


def catalog_subtemas(catalog: list[dict]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for area_group in catalog:
        area = area_group["area"]
        if area not in AREA_PREFIXES:
            raise ValueError(f"Área sem prefixo de ID configurado: {area}")
        for macro in area_group.get("macroThemes", []):
            for subtema in macro.get("dbSubtemas", []):
                result.setdefault(subtema, []).append(area)
    return result


def build_subtema_map(catalog: list[dict], existing: dict[str, str]) -> dict[str, str]:
    subtemas = catalog_subtemas(catalog)
    unknown_existing = sorted(set(existing) - set(subtemas))
    if unknown_existing:
        raise ValueError(f"IDs existentes fora da taxonomia: {unknown_existing}")
    if len(existing.values()) != len(set(existing.values())):
        raise ValueError("subtema_map.json contém IDs duplicados")

    next_number: dict[str, int] = {prefix: 1 for prefix in set(AREA_PREFIXES.values())}
    for identifier in existing.values():
        match = re.fullmatch(r"(.+)-(\d+)", identifier)
        if not match:
            raise ValueError(f"ID de subtema inválido: {identifier}")
        prefix, number = match.group(1), int(match.group(2))
        next_number[prefix] = max(next_number.get(prefix, 1), number + 1)

    compiled = dict(existing)
    for subtema in sorted(set(subtemas) - set(existing)):
        prefix = AREA_PREFIXES[subtemas[subtema][0]]
        compiled[subtema] = f"{prefix}-{next_number[prefix]:03d}"
        next_number[prefix] += 1
    return {key: compiled[key] for key in sorted(compiled)}


def render_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def render_planner_ts(catalog: list[dict], current: str) -> str:
    match = re.search(r"\b(?:export\s+)?const\s+plannerData\s*=", current)
    if not match:
        raise ValueError("plannerData const assignment not found")
    payload = _scan_balanced_json(current, match.end())
    start = current.index(payload, match.end())
    replacement = json.dumps(catalog, ensure_ascii=False, indent=2)
    return current[:start] + replacement + current[start + len(payload):]


def compile_artifacts(
    taxonomy_path: Path = TAXONOMY_PATH,
    map_path: Path = SUBTEMA_MAP_PATH,
    planner_json_path: Path = PLANNER_JSON_PATH,
    planner_ts_path: Path = PLANNER_TS_PATH,
) -> dict[Path, str]:
    catalog = load_taxonomy(taxonomy_path)
    existing = json.loads(map_path.read_text(encoding="utf-8")) if map_path.exists() else {}
    compiled_map = build_subtema_map(catalog, existing)
    return {
        map_path: render_json(compiled_map),
        planner_json_path: render_json(catalog),
        planner_ts_path: render_planner_ts(catalog, planner_ts_path.read_text(encoding="utf-8")),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Write compiled artifacts; default is check-only")
    parser.add_argument("--output", type=Path, help="Write machine-readable compilation summary")
    args = parser.parse_args()
    artifacts = compile_artifacts()
    changed = [str(path.resolve()) for path, content in artifacts.items() if not path.exists() or path.read_text(encoding="utf-8") != content]
    if args.apply:
        for path, content in artifacts.items():
            path.write_text(content, encoding="utf-8")
    summary = {
        "mode": "apply" if args.apply else "check",
        "changed_files": changed,
        "in_sync": not changed,
        "taxonomy_subtemas": len(catalog_subtemas(load_taxonomy())),
        "mapped_subtemas": len(json.loads(artifacts[SUBTEMA_MAP_PATH])),
    }
    payload = json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0 if args.apply or not changed else 1


if __name__ == "__main__":
    raise SystemExit(main())
