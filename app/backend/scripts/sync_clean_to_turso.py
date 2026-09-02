"""
Sincronizador Universal e Robusto: Local SQLite (medquest.db) -> Turso Cloud Database.
Utiliza apenas a biblioteca padrão (urllib.request, json, sqlite3) sem dependências externas.
Wipe limpo e reenvio de todas as tabelas em batch pipelined.
"""

import os
import sys
import json
import time
import sqlite3
import urllib.request
import urllib.error

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

TURSO_URL = os.environ.get("TURSO_DATABASE_URL", "").replace("libsql://", "https://").replace("wss://", "https://")
TURSO_TOKEN = os.environ.get("TURSO_AUTH_TOKEN", "")
if not TURSO_URL or not TURSO_TOKEN:
    raise SystemExit("TURSO_DATABASE_URL e TURSO_AUTH_TOKEN são obrigatórios.")
LOCAL_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "medquest.db")

PIPELINE_URL = f"{TURSO_URL}/v2/pipeline"
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

def execute_pipeline(requests_list):
    payload = json.dumps({"requests": requests_list}).encode("utf-8")
    for attempt in range(6):
        try:
            req = urllib.request.Request(PIPELINE_URL, data=payload, headers=HEADERS, method="POST")
            with urllib.request.urlopen(req, timeout=90) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (429, 503, 504):
                time.sleep(2 + attempt * 2)
                continue
            err_body = e.read().decode("utf-8", errors="ignore")
            raise Exception(f"HTTP {e.code}: {err_body[:400]}")
        except Exception as e:
            if attempt == 5:
                raise e
            time.sleep(2 + attempt * 2)
    raise Exception("Pipeline request failed after max retries")

def sync():
    t0 = time.time()
    print("=" * 80)
    print("🚀 INICIANDO SINCRONIZAÇÃO COMPLETA LOCAL -> TURSO CLOUD")
    print(f"Origem Local: {LOCAL_DB}")
    print(f"Destino Turso: {TURSO_URL}")
    print("=" * 80)

    local = sqlite3.connect(LOCAL_DB)
    cur = local.cursor()

    cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
    tables = cur.fetchall()
    table_map = {t[0]: t[1] for t in tables}
    all_names = [t[0] for t in tables]

    # Desabilitar Foreign Keys durante upload
    try:
        execute_pipeline([make_execute("PRAGMA foreign_keys=OFF"), make_close()])
    except Exception as e:
        print("Aviso FK:", e)

    ordered = [t for t in TABLE_ORDER if t in table_map]
    ordered += [t for t in all_names if t not in ordered and t not in SKIP_TABLES]

    for name in ordered:
        sql = table_map.get(name)
        if not sql or name in SKIP_TABLES:
            continue

        print(f"\n📦 Sincronizando Tabela: {name}")
        # Recriar tabela no Turso
        execute_pipeline([
            make_execute(f"DROP TABLE IF EXISTS {name}"),
            make_execute(sql),
            make_close()
        ])

        rows = cur.execute(f"SELECT * FROM {name}").fetchall()
        total = len(rows)
        if total == 0:
            print("   -> Tabela vazia (0 registros).")
            continue

        col_info = cur.execute(f"PRAGMA table_info({name})").fetchall()
        cols = [c[1] for c in col_info]
        placeholders = ", ".join(["?" for _ in cols])
        insert_sql = f"INSERT INTO {name} ({', '.join(cols)}) VALUES ({placeholders})"

        batch_size = 250
        uploaded = 0

        for batch_start in range(0, total, batch_size):
            batch_end = min(batch_start + batch_size, total)
            batch_rows = rows[batch_start:batch_end]

            reqs = []
            for r in batch_rows:
                args = [convert_value(v) for v in r]
                reqs.append(make_execute(insert_sql, args))
            reqs.append(make_close())

            execute_pipeline(reqs)
            uploaded += len(batch_rows)
            print(f"   -> Progresso: {uploaded}/{total} registros inseridos ({uploaded/total*100:.1f}%)", end="\r")

        print(f"\n   ✅ {name}: {total} registros enviados com sucesso!")

    # Recriar FTS se aplicável
    try:
        print("\n🔍 Recriando índices FTS...")
        execute_pipeline([
            make_execute("DROP TABLE IF EXISTS questions_fts"),
            make_execute("CREATE VIRTUAL TABLE IF NOT EXISTS questions_fts USING fts5(topic, stem, area, subtema, content='questions', content_rowid='id')"),
            make_execute("INSERT INTO questions_fts(rowid, topic, stem, area, subtema) SELECT id, topic, stem, area, subtema FROM questions"),
            make_execute("PRAGMA foreign_keys=ON"),
            make_close()
        ])
        print("   ✅ Índices FTS recriados com sucesso!")
    except Exception as e:
        print("   Aviso FTS:", e)

    local.close()
    elapsed = time.time() - t0
    print("\n" + "=" * 80)
    print(f"🎉 SINCRONIZAÇÃO COM A NUVEM CONCLUÍDA EM {elapsed:.1f} SEGUNDOS!")
    print("=" * 80)

if __name__ == "__main__":
    sync()
