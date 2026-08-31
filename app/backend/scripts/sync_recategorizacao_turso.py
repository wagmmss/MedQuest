#!/usr/bin/env python3
"""Sincroniza ao Turso apenas as categorias que divergem do banco local.

O modo padrão é somente leitura. ``--apply`` efetiva a atualização e a
reindexação FTS das questões alteradas, depois de comparar os dois bancos.
"""

from __future__ import annotations

import argparse
import os
import re
import sqlite3
import time
from pathlib import Path

import requests


BACKEND = Path(__file__).resolve().parents[1]
LOCAL_DB = BACKEND / "medquest.db"


def load_env(path: Path) -> None:
    """Carrega somente variáveis ausentes, sem depender de python-dotenv."""
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, item = line.split("=", 1)
        key, item = key.strip(), item.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = item


load_env(BACKEND.parents[1] / ".env")
load_env(BACKEND / ".env")
TURSO_URL = os.environ.get("TURSO_DATABASE_URL", "").replace("libsql://", "https://").replace("wss://", "https://")
TURSO_TOKEN = os.environ.get("TURSO_AUTH_TOKEN", "")
if not TURSO_URL or not TURSO_TOKEN:
    # Compatibilidade temporária com a configuração já usada pelos scripts do
    # projeto. Os valores permanecem em memória e nunca são registrados.
    legacy_source = (BACKEND / "scripts" / "sync_incremental_turso.py").read_text(encoding="utf-8")
    legacy_url = re.search(r'TURSO_URL\s*=.*?"(libsql://[^"]+)"', legacy_source)
    legacy_token = re.search(r'TURSO_TOKEN\s*=.*?\bor\s+"([^"]+)"', legacy_source)
    TURSO_URL = TURSO_URL or (legacy_url.group(1).replace("libsql://", "https://") if legacy_url else "")
    TURSO_TOKEN = TURSO_TOKEN or (legacy_token.group(1) if legacy_token else "")


def value(item: object) -> dict[str, object]:
    if item is None:
        return {"type": "null"}
    if isinstance(item, int):
        return {"type": "integer", "value": str(item)}
    return {"type": "text", "value": str(item)}


def execute(sql: str, args: list[dict[str, object]] | None = None) -> dict[str, object]:
    statement: dict[str, object] = {"sql": sql}
    if args:
        statement["args"] = args
    return {"type": "execute", "stmt": statement}


def pipeline(session: requests.Session, requests_list: list[dict[str, object]]) -> dict[str, object]:
    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            response = session.post(
                f"{TURSO_URL}/v3/pipeline",
                headers={"Authorization": f"Bearer {TURSO_TOKEN}", "Content-Type": "application/json"},
                json={"requests": requests_list}, timeout=60,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as error:
            last_error = error
            time.sleep(attempt)
    raise RuntimeError(f"Falha ao comunicar com Turso: {last_error}")


def cell(row: list[dict[str, str]], index: int) -> str | None:
    item = row[index]
    return None if item.get("type") == "null" else item.get("value")


def main() -> int:
    parser = argparse.ArgumentParser(description="Compara e sincroniza categorias locais para Turso.")
    parser.add_argument("--apply", action="store_true", help="Efetiva as atualizações encontradas.")
    args = parser.parse_args()
    if not TURSO_URL or not TURSO_TOKEN:
        raise SystemExit("TURSO_DATABASE_URL e TURSO_AUTH_TOKEN devem estar configurados em app/backend/.env.")

    local = sqlite3.connect(LOCAL_DB)
    local.row_factory = sqlite3.Row
    local_rows = local.execute(
        "SELECT id, area, subtema, subtema_id, subtema_orig, topic FROM questions ORDER BY id"
    ).fetchall()
    local_by_id = {row["id"]: row for row in local_rows}

    session = requests.Session()
    response = pipeline(session, [
        execute("SELECT id, area, subtema, subtema_id, subtema_orig, topic FROM questions ORDER BY id"),
        {"type": "close"},
    ])
    remote_result = response["results"][0]["response"]["result"]["rows"]
    remote_by_id: dict[int, tuple[str | None, ...]] = {}
    for row in remote_result:
        question_id = int(cell(row, 0) or "0")
        remote_by_id[question_id] = tuple(cell(row, index) for index in range(1, 6))

    fields = ("area", "subtema", "subtema_id", "subtema_orig", "topic")
    updates = [
        row for question_id, row in local_by_id.items()
        if question_id in remote_by_id and tuple(row[field] for field in fields) != remote_by_id[question_id]
    ]
    missing = [row for question_id, row in local_by_id.items() if question_id not in remote_by_id]
    print(f"Local: {len(local_by_id)} questões; Turso: {len(remote_by_id)} questões.")
    print(f"Divergências de categoria: {len(updates)}; questões ausentes no Turso: {len(missing)}.")
    if not args.apply:
        local.close()
        print("Dry-run concluído. Use --apply para sincronizar.")
        return 0

    for start in range(0, len(updates), 50):
        chunk = updates[start : start + 50]
        requests_list = [
            execute(
                "UPDATE questions SET area=?, subtema=?, subtema_id=?, subtema_orig=?, topic=? WHERE id=?",
                [value(row[field]) for field in fields] + [value(row["id"])],
            )
            for row in chunk
        ] + [{"type": "close"}]
        pipeline(session, requests_list)
        print(f"Categorias atualizadas: {min(start + len(chunk), len(updates))}/{len(updates)}")

    if missing:
        columns = [column["name"] for column in local.execute("PRAGMA table_info(questions)")]
        sql = f"INSERT OR REPLACE INTO questions ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})"
        for start in range(0, len(missing), 50):
            chunk = missing[start : start + 50]
            requests_list = [
                execute(sql, [value(row[column]) for column in columns]) for row in chunk
            ] + [{"type": "close"}]
            pipeline(session, requests_list)
            print(f"Questões inseridas: {min(start + len(chunk), len(missing))}/{len(missing)}")

    affected_ids = [row["id"] for row in updates] + [row["id"] for row in missing]
    for start in range(0, len(affected_ids), 100):
        chunk = affected_ids[start : start + 100]
        requests_list = [
            execute(
                "INSERT OR REPLACE INTO questions_fts(rowid,stem,explanation) "
                "SELECT q.id,q.stem,e.explanation_text FROM questions q "
                "LEFT JOIN explanations e ON q.id=e.question_id WHERE q.id=?",
                [value(question_id)],
            )
            for question_id in chunk
        ] + [{"type": "close"}]
        pipeline(session, requests_list)
    print(f"Sincronização concluída: {len(affected_ids)} questões atualizadas no Turso.")
    local.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
