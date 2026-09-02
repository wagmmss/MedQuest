"""Fail when executable source contains credential-shaped literals."""
from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCES = (REPO_ROOT / "app", REPO_ROOT / ".github")
PATTERNS = (
    re.compile(r"eyJ[a-zA-Z0-9_-]{12,}\.[a-zA-Z0-9_-]{12,}\.[a-zA-Z0-9_-]{12,}"),
    re.compile(r"(?i)(?:turso_token|turso_auth_token|vapid_private_key|flask_api_proxy_secret)\s*=\s*[\"'][^\"']{16,}[\"']"),
)
SUFFIXES = {".py", ".ts", ".tsx", ".js", ".mjs", ".yml", ".yaml"}


def find_matches() -> list[str]:
    matches: list[str] = []
    for source in SOURCES:
        if not source.exists():
            continue
        for path in source.rglob("*"):
            if not path.is_file() or path.suffix not in SUFFIXES:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            if any(pattern.search(text) for pattern in PATTERNS):
                matches.append(str(path.relative_to(REPO_ROOT)))
    return sorted(matches)


if __name__ == "__main__":
    findings = find_matches()
    if findings:
        print("Credential-shaped literals found:")
        print("\n".join(findings))
        raise SystemExit(1)
    print("No credential-shaped literals found.")
