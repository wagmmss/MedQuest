import argparse
import sys
import json
from pathlib import Path
from datetime import datetime, timezone

from audit.connection import get_readonly_connection
from audit.integrity import check_integrity
from audit.duplication import check_duplication
from audit.explanations import check_explanations
from audit.taxonomy import check_taxonomy
from audit.coverage import check_coverage
from audit.encoding import check_encoding

def build_markdown(data: dict) -> str:
    md = [
        "# MedQuest Content & Taxonomy Audit (Sprint C1.1)",
        f"**Generated At:** {data['generated_at']}",
        f"**Database Size:** {data['database']['size_bytes']} bytes",
        "",
        "## 1. Summary",
        f"- **Total Questions:** {data['summary']['total_questions']}",
        f"- **Usable (missing_alts=0):** {data['summary']['usable_questions']}",
        f"- **No Area:** {data['summary']['no_area']}",
        f"- **No Subtema:** {data['summary']['no_subtema']}",
        "",
        "## 2. Critical Failures (Integrity)",
        "> [!WARNING]",
        "> These issues will cause `--strict` mode to fail."
    ]

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

    md.extend([
        "## 3. Warnings",
        f"- **missing_alts=1 but Complete:** {len(data['warnings']['missing_alts_1_complete'])} (Possible pedagogical deactivation)",
        ""
    ])

    md.extend([
        "## 4. Human Review Queue (Explanations)",
        f"- **High Priority (Empty/Placeholder):** {len(data['human_review_queue']['high_priority'])}",
        f"- **Medium Priority (Too short):** {len(data['human_review_queue']['medium_priority'])}",
        f"- **Low Priority (Heuristic):** {len(data['human_review_queue']['low_priority'])}",
        ""
    ])

    md.extend([
        "## 5. Duplication",
        f"- **Literal Exact Groups:** {data['duplication']['literal_exact']['groups_count']} (Affects {data['duplication']['literal_exact']['affected_questions_count']} Qs)",
        f"- **Normalized Exact Groups:** {data['duplication']['normalized_exact']['groups_count']} (Affects {data['duplication']['normalized_exact']['affected_questions_count']} Qs)",
        ""
    ])

    md.extend([
        "## 6. Taxonomy Divergence",
        f"**DB State:** {data['taxonomy']['sqlite_db']['total_areas']} Areas, {data['taxonomy']['sqlite_db']['total_subtemas']} Subtemas",
        ""
    ])

    cat = data['taxonomy']['catalogs']
    md.append("| Catalog | Status | Missing Areas | Missing Subtemas | Affected Qs |")
    md.append("|---|---|---|---|---|")
    for name in ["taxonomy_json", "canonical_subtemas_py", "plannerData_json", "plannerData_ts"]:
        v = cat[name]
        status = v["status"]
        if status == "unverified":
            md.append(f"| {name} | {status} | - | - | - |")
        else:
            md.append(f"| {name} | {status} | {len(v['missing_areas_in_catalog'])} | {len(v['missing_subtemas_in_catalog'])} | {v['affected_questions_by_missing_subtemas']} |")

    md.extend(["", "### Source Consumers"])
    for source, consumer in data['taxonomy']['source_consumers'].items():
        md.append(f"- **{source}**: {consumer}")

    md.extend([
        "",
        "## 7. Sprint C2 Proposals",
        "- **Technical Corrections (Automated)**: Address critical integrity failures systematically (e.g. purging actual orphans, fixing broken structure flags).",
        "- **Taxonomy Standardization**: Decide on a single source of truth and normalize the database strings, migrating affected questions.",
        "- **Medical Review**: Have humans or assisted workflows review the explanation queue. (Do not rely blindly on LLMs for final clinical truth)."
    ])

    return "\n".join(md)

def main():
    parser = argparse.ArgumentParser(description="MedQuest Sprint C1.1 Audit")
    parser.add_argument("--db", default="medquest.db", help="Path to database")
    parser.add_argument("--output", help="JSON output file")
    parser.add_argument("--md", help="Markdown output file")
    parser.add_argument("--strict", action="store_true", help="Exit 1 if critical failures found")
    parser.add_argument("--short-limit", type=int, default=50, dest="short_explanation_limit")
    parser.add_argument("--low-coverage-limit", type=int, default=20)
    parser.add_argument("--max-details", type=int, default=0, help="Max items per distribution to print")
    args = parser.parse_args()

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
    main()
