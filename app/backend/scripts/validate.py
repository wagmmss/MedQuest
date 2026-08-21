"""Read-only MedQuest content and taxonomy audit (Sprint C1.1)."""
from __future__ import annotations

import argparse
import sys
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from datetime import datetime, timezone

try:  # Script execution: python scripts/validate.py
    from audit.connection import get_readonly_connection
    from audit.coverage import check_coverage
    from audit.duplication import check_duplication
    from audit.encoding import check_encoding
    from audit.explanations import check_explanations
    from audit.integrity import check_integrity
    from audit.taxonomy import check_taxonomy
except ModuleNotFoundError:  # Package import: from scripts.validate import ...
    from scripts.audit.connection import get_readonly_connection
    from scripts.audit.coverage import check_coverage
    from scripts.audit.duplication import check_duplication
    from scripts.audit.encoding import check_encoding
    from scripts.audit.explanations import check_explanations
    from scripts.audit.integrity import check_integrity
    from scripts.audit.taxonomy import check_taxonomy

DEFAULT_DB = Path(__file__).resolve().parents[1] / "medquest.db"
SCRIPTS_DIR = Path(__file__).resolve().parent

    cf = data["critical_failures"]
    md.extend([
        f"- **Empty Statements:** {len(cf['empty_statement'])}",
        f"- **Empty Alternatives:** {len(cf['empty_alternative'])}",
        f"- **Invalid Correct Letters:** {len(cf['invalid_correct_letter'])}",
        f"- **Answers w/o Alternative:** {len(cf['answer_without_alternative'])}",
        f"- **Questions with Duplicated Alt Letters:** {len(cf['duplicated_letters'])}",
        f"- **Orphan Alternatives:** {len(cf['orphan_records']['alternatives'])}",
        f"- **Orphan Images:** {len(cf['orphan_records']['images'])}",
        f"- **missing_alts=0 but Incomplete:** {len(cf['missing_alts_0_incomplete'])}",
        f"- **Duplicated Source File+Number:** {len(cf['duplicate_source_file_number'])}",
        ""
    ])

def _nonempty_leaf_count(value: object) -> int:
    if isinstance(value, list):
        return len(value)
    if isinstance(value, dict):
        return sum(_nonempty_leaf_count(item) for item in value.values())
    return 0

    md.extend([
        "## 4. Human Review Queue (Explanations)",
        f"- **High Priority (Empty/Placeholder):** {len(data['human_review_queue']['high_priority'])}",
        f"- **Medium Priority (Too short):** {len(data['human_review_queue']['medium_priority'])}",
        f"- **Low Priority (Heuristic):** {len(data['human_review_queue']['low_priority'])}",
        ""
    ])

def audit_database(
    db_path: Path,
    *,
    short_explanation_limit: int = 50,
    low_coverage_limit: int = 20,
    max_details: int = 0,
    strict_mode: bool = False,
    generated_at: str | None = None,
    scripts_dir: Path = SCRIPTS_DIR,
) -> dict:
    db = get_readonly_connection(db_path)
    try:
        integrity = check_integrity(db)
        duplication = check_duplication(db)
        explanations = check_explanations(db, short_explanation_limit)
        taxonomy = check_taxonomy(db, scripts_dir)
        coverage = check_coverage(db, scripts_dir, low_coverage_limit, max_details)
        encoding = check_encoding(db)
        pragma = {
            "query_only": int(db.execute("PRAGMA query_only").fetchone()[0]),
            "integrity_check": str(db.execute("PRAGMA integrity_check").fetchone()[0]),
        }
    finally:
        db.close()

    critical = integrity["critical_failures"]
    critical_count = _nonempty_leaf_count(critical)
    warning_messages = list(taxonomy["warnings"]) + list(explanations["schema_warnings"])
    warning_messages.append(duplication["probable_duplicate"]["warning"])
    if integrity["warnings"]["missing_alts_1_complete"]:
        warning_messages.append("Some missing_alts=1 questions are structurally complete; this is a warning only.")
    if integrity["warnings"]["is_correct_mismatches"]:
        warning_messages.append("Some alternatives.is_correct flags disagree with questions.correct_letter.")

    queue = explanations["human_review_queue"]
    return {
        "schema_version": "1.1.0",
        "generated_at": generated_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "database": str(db_path.resolve()),
        "config": {
            "short_explanation_limit": short_explanation_limit,
            "low_coverage_limit": low_coverage_limit,
            "max_details": max_details,
            "strict_mode": strict_mode,
        },
        "summary": {
            "questions": integrity["total"],
            "usable_questions": integrity["usable"],
            "critical_failure_records": critical_count,
            "human_review_questions": len(queue["all"]),
            "taxonomy_unverified_sources": sum(source["status"] != "verified" for source in taxonomy["sources"].values()),
        },
        "warnings": sorted(set(warning_messages)),
        "read_only_verification": pragma,
        "integrity": integrity,
        "critical_failures": critical,
        "duplication": duplication,
        "taxonomy": taxonomy,
        "coverage": coverage,
        "encoding": encoding,
        "explanations": explanations,
        "human_review_queue": queue,
    }


def generate_markdown(result: dict) -> str:
    summary = result["summary"]
    integrity = result["integrity"]
    critical = result["critical_failures"]
    duplication = result["duplication"]
    coverage = result["coverage"]
    taxonomy = result["taxonomy"]
    lines = [
        "# Relatório Baseline de Conteúdo e Taxonomia (Sprint C1.1)",
        "",
        f"**Data de geração:** {result['generated_at']}",
        f"**Banco:** {result['database']}",
        f"**Schema do relatório:** {result['schema_version']}",
        "",
        "## Resumo executivo",
        "",
        f"- Questões: {summary['questions']}",
        f"- Questões utilizáveis (`missing_alts=0`): {summary['usable_questions']}",
        f"- Registros em falhas críticas: {summary['critical_failure_records']}",
        f"- Questões na fila humana: {summary['human_review_questions']}",
        f"- Fontes taxonômicas não verificadas: {summary['taxonomy_unverified_sources']}",
        f"- SQLite: `query_only={result['read_only_verification']['query_only']}`, `integrity_check={result['read_only_verification']['integrity_check']}`",
        "",
        "## Integridade",
        "",
        f"- Enunciados vazios: {len(critical['empty_statements'])}",
        f"- Alternativas vazias: {len(critical['empty_alternatives'])}",
        f"- Gabaritos ausentes/inválidos: {len(critical['invalid_correct_letters'])}",
        f"- Gabaritos sem alternativa correspondente: {len(critical['answer_without_alternative'])}",
        f"- Questões com letras duplicadas: {len(critical['duplicate_alternative_letters'])}",
        f"- `missing_alts=0` estruturalmente incompletas: {len(critical['missing_alts_0_incomplete'])}",
        f"- `missing_alts=1` completas (warning): {len(integrity['warnings']['missing_alts_1_complete'])}",
        f"- Orphans: alternatives={len(critical['orphans']['alternatives'])}, explanations={len(critical['orphans']['explanations'])}, images={len(critical['orphans']['question_images'])}",
        f"- Origens duplicadas: {len(critical['duplicate_source_file_number'])}",
        "",
        "## Duplicação",
        "",
        f"- Literal exact: {duplication['literal_exact']['groups_count']} grupos / {duplication['literal_exact']['affected_questions_count']} questões",
        f"- Normalized exact: {duplication['normalized_exact']['groups_count']} grupos / {duplication['normalized_exact']['affected_questions_count']} questões",
        f"- Probable duplicate: {duplication['probable_duplicate']['status']} — {duplication['probable_duplicate']['warning']}",
        "",
        "## Taxonomia",
        "",
        f"- Subtemas no banco: {taxonomy['db_subtemas_count']}",
    ]
    for name, source in taxonomy["sources"].items():
        lines.append(f"- `{name}`: {source['status']}; DB não mapeados={len(source['unmapped_db_subtemas'])}; catálogo sem questões={len(source['unused_catalog_subtemas'])}")
    lines.extend(["", "## Cobertura", "", "As oito distribuições incluem metadados explícitos de truncamento:"])
    for name, distribution in coverage["distributions"].items():
        lines.append(f"- `{name}`: total={distribution['total_items']}, retornados={distribution['returned_items']}, truncated={str(distribution['truncated']).lower()}")
    gaps = coverage["gaps"]
    lines.extend([
        "",
        f"- Subtemas com <5 questões: {len(gaps['under_5_questions'])}",
        f"- Subtemas com <10 questões: {len(gaps['under_10_questions'])}",
        f"- Subtemas com <20 questões: {len(gaps['under_20_questions'])}",
        "",
        "## Warnings",
        "",
    ])
    lines.extend(f"- {warning}" for warning in result["warnings"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="SQLite database path")
    parser.add_argument("--output", type=Path, help="Write JSON report")
    parser.add_argument("--md", type=Path, help="Write Markdown report")
    parser.add_argument("--short-explanation-limit", type=int, default=50)
    parser.add_argument("--low-coverage-limit", type=int, default=20)
    parser.add_argument("--max-details", type=int, default=0, help="Maximum rows per coverage distribution; 0 means unlimited")
    parser.add_argument("--strict", action="store_true", help="Exit 1 when critical failures exist")
    args = parser.parse_args()
    if args.max_details < 0:
        parser.error("--max-details must be >= 0")
    try:
        result = audit_database(
            args.db,
            short_explanation_limit=args.short_explanation_limit,
            low_coverage_limit=args.low_coverage_limit,
            max_details=args.max_details,
            strict_mode=args.strict,
        )
    except (FileNotFoundError, ValueError, OSError) as exc:
        parser.error(str(exc))

    payload = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    if args.md:
        args.md.parent.mkdir(parents=True, exist_ok=True)
        args.md.write_text(generate_markdown(result), encoding="utf-8")
    if args.strict and result["summary"]["critical_failure_records"]:
        print("ERRO: Falhas críticas encontradas na integridade da base.", file=sys.stderr)
        return 1
    return 0

    scripts_dir = Path(__file__).resolve().parent

    db, size = get_readonly_connection(args.db)

    # 1. Summary
    tq = db.execute("SELECT count(*) FROM questions").fetchone()[0]
    uq = db.execute("SELECT count(*) FROM questions WHERE missing_alts = 0").fetchone()[0]
    na = db.execute("SELECT count(*) FROM questions WHERE missing_alts = 0 AND (area IS NULL OR trim(area) = '')").fetchone()[0]
    ns = db.execute("SELECT count(*) FROM questions WHERE missing_alts = 0 AND (subtema IS NULL OR trim(subtema) = '')").fetchone()[0]

    # Modules
    integrity_data = check_integrity(db)
    duplication_data = check_duplication(db)
    explanations_data = check_explanations(db, args.short_explanation_limit)
    taxonomy_data = check_taxonomy(db, scripts_dir)
    coverage_data = check_coverage(db, scripts_dir, args.low_coverage_limit, args.max_details)
    encoding_data = check_encoding(db)

    db.close()

    full_data = {
        "schema_version": "1.1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "database": {
            "path": str(Path(args.db).resolve()),
            "size_bytes": size
        },
        "config": {
            "short_explanation_limit": args.short_explanation_limit,
            "low_coverage_limit": args.low_coverage_limit,
            "max_details": args.max_details,
            "strict_mode": args.strict
        },
        "summary": {
            "total_questions": tq,
            "usable_questions": uq,
            "no_area": na,
            "no_subtema": ns
        },
        "integrity": integrity_data, # For backward compat or raw data if needed, but we hoist critical_failures
        "critical_failures": integrity_data["critical_failures"],
        "warnings": integrity_data["warnings"],
        "human_review_queue": explanations_data["human_review_queue"],
        "duplication": duplication_data,
        "explanations": explanations_data,
        "taxonomy": taxonomy_data,
        "coverage": coverage_data,
        "encoding": encoding_data
    }

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(full_data, f, indent=2, ensure_ascii=False)

    if args.md:
        with open(args.md, "w", encoding="utf-8") as f:
            f.write(build_markdown(full_data))

    if args.strict:
        cf = full_data["critical_failures"]
        has_critical = any(len(v) > 0 if isinstance(v, list) else (len(v['alternatives']) > 0 or len(v['images']) > 0) for k, v in cf.items())
        if has_critical:
            print("ERROR: Critical failures found in strict mode.")
            sys.exit(1)

if __name__ == "__main__":
    raise SystemExit(main())
