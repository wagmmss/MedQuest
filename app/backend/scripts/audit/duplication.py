"""Deterministic duplicate-stem analysis."""
from __future__ import annotations

import hashlib
import re
import sqlite3
import unicodedata
from collections import defaultdict

from .connection import rows

INVISIBLE = re.compile(r"[\u200b\u200c\u200d\u2060\ufeff]")


def _literal_text(text: str) -> str:
    """Remove only invisible format characters and normalize line endings."""
    return INVISIBLE.sub("", text.replace("\r\n", "\n").replace("\r", "\n"))


def _normalized_text(text: str) -> str:
    value = unicodedata.normalize("NFKC", _literal_text(text)).casefold()
    value = "".join(" " if unicodedata.category(char).startswith("P") else char for char in value)
    return re.sub(r"\s+", " ", value).strip()


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _context_name(group: list[dict]) -> str:
    if any(item["institution"] in (None, "") or item["year"] is None for item in group):
        return "unknown_or_mixed_context"
    institutions = {item["institution"] for item in group}
    years = {item["year"] for item in group}
    if len(institutions) == 1 and len(years) == 1:
        return "same_institution_same_year"
    if len(institutions) == 1:
        return "same_institution_different_years"
    return "different_institutions"


def _build_category(groups: dict[str, list[dict]], excluded_ids: set[int] | None = None) -> tuple[dict, set[int]]:
    excluded_ids = excluded_ids or set()
    contexts = {name: [] for name in ("same_institution_same_year", "same_institution_different_years", "different_institutions", "unknown_or_mixed_context")}
    affected: set[int] = set()
    for digest in sorted(groups):
        members = sorted((item for item in groups[digest] if item["id"] not in excluded_ids), key=lambda item: item["id"])
        if len(members) < 2:
            continue
        public_members = [{"id": item["id"], "institution": item["institution"], "year": item["year"]} for item in members]
        contexts[_context_name(public_members)].append({"sha256": digest, "count": len(public_members), "questions": public_members})
        affected.update(item["id"] for item in members)
    return {"groups_count": sum(len(items) for items in contexts.values()), "affected_questions_count": len(affected), "contexts": contexts}, affected


def check_duplication(db: sqlite3.Connection) -> dict:
    questions = rows(db, "SELECT id, institution_code AS institution, year, stem FROM questions ORDER BY id")
    literal_groups: dict[str, list[dict]] = defaultdict(list)
    normalized_groups: dict[str, list[dict]] = defaultdict(list)
    for question in questions:
        stem = str(question["stem"] or "")
        if not stem:
            continue
        literal_groups[_sha256(_literal_text(stem))].append(question)
        normalized = _normalized_text(stem)
        if normalized:
            normalized_groups[_sha256(normalized)].append(question)
    literal, literal_ids = _build_category(literal_groups)
    normalized, _ = _build_category(normalized_groups, literal_ids)
    return {
        "literal_exact": literal,
        "normalized_exact": normalized,
        "probable_duplicate": {"status": "not_executed", "groups_count": 0, "affected_questions_count": 0, "warning": "Fuzzy/embedding matching was not executed because it is unsafe for automatic classification."},
        "normalization": {
            "literal_exact": "Removes zero-width format characters and normalizes CR/LF only.",
            "normalized_exact": "Additionally applies NFKC, case folding, punctuation removal and whitespace collapsing.",
        },
    }
