"""Governed command runner for supported MedQuest content pipelines.

All unlisted Python files in this directory are legacy by policy. The runner
does not import target scripts, avoiding their historical import-time effects.
It records a local SQLite job run only when the caller passes an explicit DB.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parent
MANIFEST_PATH = SCRIPTS_DIR / "pipelines.json"


def load_manifest(path: Path = MANIFEST_PATH) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("default_classification") != "legacy":
        raise ValueError("All unlisted scripts must remain legacy by default")
    ids = [item.get("id") for item in manifest.get("pipelines", [])]
    if len(ids) != len(set(ids)) or any(not item for item in ids):
        raise ValueError("Pipeline ids must be unique and non-empty")
    for item in manifest["pipelines"]:
        script = SCRIPTS_DIR / item["script"]
        if script.parent != SCRIPTS_DIR or script.suffix != ".py" or not script.is_file():
            raise ValueError(f"Invalid pipeline script: {item['script']}")
    return manifest


def inventory(manifest: dict) -> dict:
    scripts = sorted(path.name for path in SCRIPTS_DIR.glob("*.py") if path.name != "__init__.py")
    supported = {item["script"] for item in manifest["pipelines"]}
    runtime = set(manifest.get("runtime_modules", []))
    return {
        "total_python_scripts": len(scripts),
        "critical": sum(item["classification"] == "critical" for item in manifest["pipelines"]),
        "important": sum(item["classification"] == "important" for item in manifest["pipelines"]),
        "legacy": len(set(scripts) - supported - runtime),
        "runtime": len(runtime),
        "unclassified": sorted((supported | runtime) - set(scripts)),
    }


def _hash_run(pipeline: dict, args: list[str]) -> str:
    script_hash = hashlib.sha256((SCRIPTS_DIR / pipeline["script"]).read_bytes()).hexdigest()
    payload = json.dumps({"pipeline": pipeline["id"], "script_hash": script_hash, "args": args}, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _record_start(db_path: Path, pipeline: dict, input_hash: str, actor: str) -> str:
    run_id = str(uuid.uuid4())
    with sqlite3.connect(db_path) as db:
        db.execute("""
            INSERT INTO job_runs (id, pipeline_id, pipeline_version, status, input_hash, started_at, actor)
            VALUES (?, ?, ?, 'running', ?, ?, ?)
        """, (run_id, pipeline["id"], "1", input_hash, datetime.now(timezone.utc).isoformat(), actor))
    return run_id


def _record_finish(db_path: Path, run_id: str, status: str, started_at: datetime, summary: dict, error_class: str | None = None) -> None:
    finished_at = datetime.now(timezone.utc)
    duration_ms = int((finished_at - started_at).total_seconds() * 1000)
    output_hash = hashlib.sha256(json.dumps(summary, sort_keys=True).encode("utf-8")).hexdigest()
    with sqlite3.connect(db_path) as db:
        db.execute("""
            UPDATE job_runs SET status=?, output_hash=?, finished_at=?, duration_ms=?, summary_json=?, error_class=?
            WHERE id=?
        """, (status, output_hash, finished_at.isoformat(), duration_ms, json.dumps(summary, sort_keys=True), error_class, run_id))


def run_pipeline(pipeline: dict, extra_args: list[str], db_path: Path | None, actor: str) -> int:
    applying = "--apply" in extra_args
    if applying and not pipeline["mutates_data"]:
        raise ValueError(f"{pipeline['id']} is read-only and does not accept --apply")
    if pipeline["id"] == "content-repair" and applying and "--backup-dir" not in extra_args:
        raise ValueError("content-repair --apply requires --backup-dir")

    input_hash = _hash_run(pipeline, extra_args)
    started_at = datetime.now(timezone.utc)
    run_id = _record_start(db_path, pipeline, input_hash, actor) if db_path else None
    command = [sys.executable, str(SCRIPTS_DIR / pipeline["script"]), *extra_args]
    result = subprocess.run(command, cwd=SCRIPTS_DIR.parent, text=True, capture_output=True, check=False)
    summary = {"command": command[1:], "returncode": result.returncode, "stdout_tail": result.stdout[-4000:], "stderr_tail": result.stderr[-4000:]}
    if run_id and db_path:
        status = "succeeded" if result.returncode == 0 else "failed"
        if not applying and result.returncode == 0:
            status = "dry_run"
        _record_finish(db_path, run_id, status, started_at, summary, None if result.returncode == 0 else "PipelineError")
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("check", help="Validate manifest and print generated inventory")
    subparsers.add_parser("list", help="List supported pipelines")
    run = subparsers.add_parser("run", help="Run a supported pipeline without importing it")
    run.add_argument("pipeline_id")
    run.add_argument("--db", type=Path, help="Explicit local SQLite DB for job-run telemetry")
    run.add_argument("--actor", default="local-operator")
    args, forwarded = parser.parse_known_args()
    if args.command in {"check", "list"} and forwarded:
        parser.error("check and list do not accept pipeline arguments")
    manifest = load_manifest()
    if args.command == "check":
        report = inventory(manifest)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 1 if report["unclassified"] else 0
    if args.command == "list":
        print(json.dumps(manifest["pipelines"], indent=2, ensure_ascii=False))
        return 0
    pipeline = next((item for item in manifest["pipelines"] if item["id"] == args.pipeline_id), None)
    if pipeline is None:
        parser.error(f"Unknown or legacy pipeline: {args.pipeline_id}")
    if args.db and not args.db.is_file():
        parser.error("--db must name an existing local SQLite database")
    forwarded = forwarded[1:] if forwarded[:1] == ["--"] else forwarded
    try:
        return run_pipeline(pipeline, forwarded, args.db, args.actor)
    except ValueError as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
