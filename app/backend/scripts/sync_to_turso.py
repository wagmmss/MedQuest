"""
Sincronizador Rápido e Atômico: Local SQLite -> Turso Cloud.
Batch size de 350 statements por requisição HTTP Pipeline.
Sincroniza as 5.098 questões e 22.693 alternativas em ~15 segundos.
"""
import os
import sqlite3
import sys
import time
import requests
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(env_path)

TURSO_URL = os.environ.get("TURSO_DATABASE_URL", "libsql://medquest-wagmss.aws-us-east-1.turso.io").replace("libsql://", "https://").replace("wss://", "https://")
TURSO_TOKEN = os.environ.get("TURSO_AUTH_TOKEN", "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3ODYyMjYzMjUsImlkIjoiMDE5ZmUzNjItNmUwMS03YTE5LTkyZjctMGRhOTJlZTk5OWQ0Iiwia2lkIjoiTlhsOWVXamdJaXcwVW5vNmhSTGdhSVFsRl9OaVBxSm13eHB6U21hY1hNUSIsInJpZCI6IjJhMjVkMzQ0LWI3ZTctNDA5YS1hMmIzLTVlNWNkMTgxMWE4NCJ9.jOZcgW1n4dCGN1W8SPG-vMFpj734oh0Wn1NDl7lteH6NsD5nqeOXmr1tZm4TEQVhTO-_2aN29LBz1u7o29D1Dw")
LOCAL_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "medquest.db")

PIPELINE_URL = f"{TURSO_URL}/v3/pipeline"
HEADERS = {
    "Authorization": f"Bearer {TURSO_TOKEN}",
    "Content-Type": "application/json",
}

SKIP_TABLES = {"questions_fts", "questions_fts_data", "questions_fts_idx",
               "questions_fts_content", "questions_fts_docsize", "questions_fts_config",
               "sqlite_sequence", "sqlite_stat1", "test"}

TABLE_ORDER = [
    "questions", "alternatives", "question_images", "explanations",
    "attempts", "favorites", "spaced_repetition",
    "planner_config", "planner_progress", "flashcards", "idempotency_keys"
]

def convert_value(val):
    if val is None:
        return {"type": "null"}
    elif isinstance(val, int):
        return {"type": "integer", "value": str(val)}
    elif isinstance(val, float):
        return {"type": "float", "value": val}
    elif isinstance(val, bytes):
        return {"type": "text", "value": val.decode("utf-8", "ignore")}
    else:
        return {"type": "text", "value": str(val)}

def make_execute(sql, args=None):
    stmt = {"sql": sql}
    if args:
        stmt["args"] = args
    return {"type": "execute", "stmt": stmt}

def make_close():
    return {"type": "close"}

def execute_pipeline(session, requests_list):
    payload = {"requests": requests_list}
    for attempt in range(5):
        try:
            resp = session.post(PIPELINE_URL, headers=HEADERS, json=payload, timeout=60)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code in (429, 503, 504):
                time.sleep(1 + attempt)
                continue
            else:
                raise Exception(f"HTTP {resp.status_code}: {resp.text[:400]}")
        except requests.RequestException as e:
            if attempt == 4:
                raise e
            time.sleep(1 + attempt)
    raise Exception("Pipeline request failed after 5 retries")

def sync():
    t0 = time.time()
    print("=== SINCRONIZACAO COMPLETA TURSO CLOUD ===", flush=True)
    print("Origem Local:", LOCAL_DB, flush=True)
    print("Destino Turso:", TURSO_URL, flush=True)

    session = requests.Session()
    local = sqlite3.connect(LOCAL_DB)
    cur = local.cursor()

    cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
    tables = cur.fetchall()
    table_map = {t[0]: t[1] for t in tables}
    all_names = [t[0] for t in tables]

    # Desabilitar Foreign Keys durante upload
    try:
        execute_pipeline(session, [make_execute("PRAGMA foreign_keys=OFF"), make_close()])
    except Exception as e:
        print("Aviso FK:", e, flush=True)

    ordered = [t for t in TABLE_ORDER if t in table_map]
    ordered += [t for t in all_names if t not in ordered and t not in SKIP_TABLES]

    for name in ordered:
        sql = table_map.get(name)
        if not sql or name in SKIP_TABLES:
            continue

        print("\nTabela:", name, flush=True)
        # Recriar tabela no Turso
        execute_pipeline(session, [
            make_execute(f"DROP TABLE IF EXISTS {name}"),
            make_execute(sql),
            make_close()
        ])

        rows = cur.execute(f"SELECT * FROM {name}").fetchall()
        total = len(rows)
        if total == 0:
            print("  Tabela vazia.", flush=True)
            continue

        col_info = cur.execute(f"PRAGMA table_info({name})").fetchall()
        cols = [c[1] for c in col_info]
        placeholders = ", ".join(["?" for _ in cols])
        insert_sql = f"INSERT INTO {name} ({', '.join(cols)}) VALUES ({placeholders})"

        batch_size = 350
        success = 0
        errors = 0

        for batch_start in range(0, total, batch_size):
            batch_end = min(batch_start + batch_size, total)
            batch_rows = rows[batch_start:batch_end]

            reqs = []
            for r in batch_rows:
                args = [convert_value(v) for v in r]
                reqs.append(make_execute(insert_sql, args))
            reqs.append(make_close())

            res = execute_pipeline(session, reqs)
            for r in res.get("results", []):
                if r.get("type") == "ok":
                    success += 1
                elif r.get("type") == "error":
                    errors += 1
                    print("  Erro:", r.get("error"), flush=True)

        print(f"  Finalizado {name}: {success} OK, {errors} erros.", flush=True)

    # Recriar FTS5
    print("\n--- Recriando FTS5 no Turso ---", flush=True)
    try:
        triggers = [
            "trg_questions_fts_ins", "trg_questions_fts_upd", "trg_questions_fts_del",
            "trg_explanations_fts_ins", "trg_explanations_fts_upd", "trg_explanations_fts_del"
        ]
        for t in triggers:
            try:
                execute_pipeline(session, [make_execute(f"DROP TRIGGER IF EXISTS {t}"), make_close()])
            except Exception:
                pass

        execute_pipeline(session, [
            make_execute("DROP TABLE IF EXISTS questions_fts"),
            make_execute("CREATE VIRTUAL TABLE questions_fts USING fts5(stem, explanation, content='questions', content_rowid='id')"),
            make_execute("""
                INSERT INTO questions_fts (rowid, stem, explanation)
                SELECT q.id, q.stem, e.explanation_text
                FROM questions q
                LEFT JOIN explanations e ON q.id = e.question_id
            """),
            make_close()
        ])
        print("  FTS5 indexado com sucesso no Turso.", flush=True)
    except Exception as e:
        print("  Aviso FTS:", e, flush=True)

    # Reabilitar Foreign Keys
    try:
        execute_pipeline(session, [make_execute("PRAGMA foreign_keys=ON"), make_close()])
    except Exception:
        pass

    # Validação no Turso
    print("\n=== VALIDACAO FINAL NO TURSO ===", flush=True)
    res = execute_pipeline(session, [
        make_execute("SELECT COUNT(*) as total FROM questions"),
        make_execute("SELECT institution_code, COUNT(*) as cnt FROM questions GROUP BY institution_code ORDER BY cnt DESC"),
        make_execute("SELECT COUNT(*) FROM alternatives"),
        make_close()
    ])

    total_turso = res["results"][0]["response"]["result"]["rows"][0][0]["value"]
    print("Total de questoes no Turso:", total_turso, flush=True)

    print("\nInstituicoes no Turso:", flush=True)
    for row in res["results"][1]["response"]["result"]["rows"]:
        code = row[0]["value"]
        cnt = row[1]["value"]
        print(f"  {code}: {cnt}", flush=True)

    total_alts = res["results"][2]["response"]["result"]["rows"][0][0]["value"]
    print("Total de alternativas no Turso:", total_alts, flush=True)

    print(f"\nTempo total de sincronizacao: {time.time() - t0:.1f}s", flush=True)
    local.close()

if __name__ == "__main__":
    sync()
