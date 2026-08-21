"""
Fast migration: SQLite local -> Turso cloud via HTTP Pipeline API.
Uses requests directly with Turso's HTTP pipeline endpoint for maximum speed.
Sends batches of statements in a single HTTP request.
"""
import sqlite3
import os
import sys
import json
import requests

TURSO_URL = os.environ["TURSO_DATABASE_URL"].replace("libsql://", "https://").replace("wss://", "https://")
TURSO_TOKEN = os.environ["TURSO_AUTH_TOKEN"]
LOCAL_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "medquest.db")

SKIP_TABLES = {"questions_fts", "questions_fts_data", "questions_fts_idx",
               "questions_fts_content", "questions_fts_docsize", "questions_fts_config"}

# Order matters: parent tables first, then children
TABLE_ORDER = [
    "questions", "alternatives", "question_images", "explanations",
    "attempts", "favorites", "spaced_repetition",
    "planner_config", "planner_progress", "flashcards",
]

PIPELINE_URL = f"{TURSO_URL}/v3/pipeline"
HEADERS = {
    "Authorization": f"Bearer {TURSO_TOKEN}",
    "Content-Type": "application/json",
}

def convert_value(val):
    """Convert Python value to Turso pipeline API value format."""
    if val is None:
        return {"type": "null"}
    elif isinstance(val, int):
        return {"type": "integer", "value": str(val)}
    elif isinstance(val, float):
        return {"type": "float", "value": val}
    elif isinstance(val, bytes):
        return {"type": "text", "value": val.decode('utf-8', 'ignore')}
    else:
        return {"type": "text", "value": str(val)}

def execute_pipeline(requests_list):
    """Send a pipeline request to Turso."""
    payload = {"requests": requests_list}
    resp = requests.post(PIPELINE_URL, headers=HEADERS, json=payload, timeout=30)
    if resp.status_code != 200:
        raise Exception(f"HTTP {resp.status_code}: {resp.text[:500]}")
    return resp.json()

def make_execute_request(sql, args=None):
    """Create a pipeline execute request."""
    stmt = {"sql": sql}
    if args:
        stmt["args"] = args
    return {"type": "execute", "stmt": stmt}

def make_close_request():
    return {"type": "close"}

def migrate():
    print(f"Conectando ao banco local: {LOCAL_DB}", flush=True)
    local = sqlite3.connect(LOCAL_DB)

    # Get all tables
    cursor = local.cursor()
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
    tables = cursor.fetchall()

    table_map = {t[0]: t[1] for t in tables}
    all_names = [t[0] for t in tables]
    print(f"Tabelas encontradas: {all_names}", flush=True)

    # Disable foreign keys
    try:
        execute_pipeline([
            make_execute_request("PRAGMA foreign_keys=OFF"),
            make_close_request(),
        ])
        print("Foreign keys desabilitadas", flush=True)
    except Exception as e:
        print(f"Aviso FK pragma: {e}", flush=True)

    # Order tables: use TABLE_ORDER first, then any remaining
    ordered = [t for t in TABLE_ORDER if t in table_map]
    ordered += [t for t in all_names if t not in ordered and t not in SKIP_TABLES]

    for name in ordered:
        sql = table_map.get(name)
        if not sql or name in SKIP_TABLES:
            print(f"\n  Pulando {name}", flush=True)
            continue

        print(f"\n{'='*50}", flush=True)
        print(f"Tabela: {name}", flush=True)

        # Drop and recreate via pipeline
        try:
            result = execute_pipeline([
                make_execute_request(f"DROP TABLE IF EXISTS {name}"),
                make_execute_request(sql),
                make_close_request(),
            ])
            print(f"  Tabela criada OK", flush=True)
        except Exception as e:
            print(f"  ERRO ao criar tabela: {e}", flush=True)
            continue

        # Get data
        rows = cursor.execute(f"SELECT * FROM {name}").fetchall()
        if not rows:
            print(f"  Tabela vazia", flush=True)
            continue

        # Get column names
        col_info = cursor.execute(f"PRAGMA table_info({name})").fetchall()
        cols = [c[1] for c in col_info]
        placeholders = ", ".join(["?" for _ in cols])
        insert_sql = f"INSERT INTO {name} ({', '.join(cols)}) VALUES ({placeholders})"

        total = len(rows)
        print(f"  {total} linhas para migrar...", flush=True)

        # Send in batches of 20 statements per pipeline request
        batch_size = 20
        success = 0
        errors = 0

        for batch_start in range(0, total, batch_size):
            batch_end = min(batch_start + batch_size, total)
            batch_rows = rows[batch_start:batch_end]

            pipeline_requests = []
            for row in batch_rows:
                args = [convert_value(v) for v in row]
                pipeline_requests.append(make_execute_request(insert_sql, args))

            pipeline_requests.append(make_close_request())

            try:
                result = execute_pipeline(pipeline_requests)
                # Check for errors in results
                batch_ok = 0
                batch_err = 0
                for r in result.get("results", []):
                    if r.get("type") == "ok":
                        batch_ok += 1
                    elif r.get("type") == "error":
                        batch_err += 1
                        if errors < 3:
                            print(f"  Erro: {r.get('error', {}).get('message', 'unknown')}", flush=True)
                success += batch_ok
                errors += batch_err
            except Exception as e:
                errors += len(batch_rows)
                if errors <= 3:
                    print(f"  Erro no batch {batch_start}: {e}", flush=True)

            # Progress
            done = min(batch_end, total)
            if done % 500 < batch_size or done == total:
                pct = (done / total) * 100
                print(f"  {done}/{total} ({pct:.0f}%) - OK: {success}, Erros: {errors}", flush=True)

        print(f"  Concluido: {success}/{total} ({errors} erros)", flush=True)

    # Verify
    print(f"\n{'='*50}", flush=True)
    print("Verificacao final:", flush=True)
    for table_name in ["questions", "alternatives", "explanations", "attempts",
                        "favorites", "spaced_repetition", "planner_config", "planner_progress"]:
        try:
            result = execute_pipeline([
                make_execute_request(f"SELECT COUNT(*) as n FROM {table_name}"),
                make_close_request(),
            ])
            count = result["results"][0]["response"]["result"]["rows"][0][0]["value"]
            print(f"  {table_name}: {count} linhas", flush=True)
        except Exception as e:
            print(f"  {table_name}: ERRO - {e}", flush=True)

    local.close()
    print("\nMigracao concluida!", flush=True)

if __name__ == "__main__":
    migrate()
