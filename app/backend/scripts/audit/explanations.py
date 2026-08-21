"""Explanation quality heuristics and a mutually exclusive review queue."""
from __future__ import annotations

import re
import sqlite3

from .connection import rows


def check_explanations(db: sqlite3.Connection, short_limit: int = 50) -> dict:
    columns = {str(row[1]) for row in db.execute("PRAGMA table_info(explanations)")}
    if not {"question_id", "explanation_text"}.issubset(columns):
        return {"usable_without_explanation": [], "human_review_queue": {"high_priority": [], "medium_priority": [], "low_priority": [], "all": []}, "reason_index": {}, "schema_warnings": ["explanations table or required columns are absent"]}
    optional = [column for column in ("generated_at", "reviewed_at") if column in columns]
    data = rows(db, "SELECT q.id AS question_id, e.explanation_text" + (", " + ", ".join(f"e.{name}" for name in optional) if optional else "") + " FROM questions q LEFT JOIN explanations e ON e.question_id=q.id WHERE q.missing_alts=0 ORDER BY q.id")
    queue: dict[int, dict] = {}

    priorities = {"low": 1, "medium": 2, "high": 3}
    def add(question_id: int, priority: str, reason: str) -> None:
        item = queue.setdefault(question_id, {"question_id": question_id, "priority": priority, "reasons": []})
        if priorities[priority] > priorities[item["priority"]]:
            item["priority"] = priority
        if reason not in item["reasons"]:
            item["reasons"].append(reason)

    for item in data:
        qid, raw = item["question_id"], item["explanation_text"]
        text = str(raw or "").strip()
        if not text:
            add(qid, "high", "empty_or_missing")
            continue
        if re.search(r"\b(?:todo|fixme|placeholder)\b", text, re.IGNORECASE):
            add(qid, "high", "residual_marker")
        if text.endswith(("...", "…")):
            add(qid, "high", "potentially_truncated")
        if len(text) < short_limit:
            add(qid, "medium", "too_short")
        if not re.search(r"\b(?:alternativa|letra|opção|correta|resposta)\b", text, re.IGNORECASE):
            add(qid, "low", "no_alternative_mention_heuristic")

    all_items = []
    for qid in sorted(queue):
        queue[qid]["reasons"].sort()
        all_items.append(queue[qid])
    buckets = {f"{priority}_priority": [{"question_id": item["question_id"], "reasons": item["reasons"]} for item in all_items if item["priority"] == priority] for priority in ("high", "medium", "low")}
    reason_index = {reason: [item["question_id"] for item in all_items if reason in item["reasons"]] for reason in ("empty_or_missing", "residual_marker", "potentially_truncated", "too_short", "no_alternative_mention_heuristic")}
    buckets["all"] = all_items
    return {
        "usable_without_explanation": reason_index["empty_or_missing"],
        "human_review_queue": buckets,
        "reason_index": reason_index,
        "schema_warnings": [f"optional explanations column absent: {name}" for name in ("generated_at", "reviewed_at") if name not in columns],
    }
