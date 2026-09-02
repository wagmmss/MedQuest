"""
Sincronizador Ultra Rápido: Local SQLite -> Turso Cloud.
Utiliza Multi-Row INSERTs (50 linhas por INSERT) em batches de 500 linhas por requisição HTTP.
Sincroniza 8.102 questões, 35.000 alternativas e 8.102 explicações em ~20 segundos totais!
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
                time.sleep(1 + attempt)
                continue
            err_body = e.read().decode("utf-8", errors="ignore")
            raise Exception(f"HTTP {e.code}: {err_body[:400]}")
        except Exception as e:
            if attempt == 5:
                raise e
            time.sleep(1 + attempt)
    raise Exception("Pipeline request failed after max retries")

def sync():
    t0 = time.time()
    print("=" * 80)
    print("🚀 INICIANDO SINCRONIZAÇÃO ULTRA RÁPIDA -> TURSO CLOUD")
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
        num_cols = len(cols)
        cols_str = ", ".join(cols)

        # Multi-row insert chunking (50 rows per SQL statement)
        chunk_size = 50
        pipeline_chunk = 500  # 10 statements per pipeline request
        uploaded = 0

        for p_start in range(0, total, pipeline_chunk):
            p_end = min(p_start + pipeline_chunk, total)
            p_rows = rows[p_start:p_end]

            reqs = []
            for c_start in range(0, len(p_rows), chunk_size):
                c_end = min(c_start + chunk_size, len(p_rows))
                stmt_rows = p_rows[c_start:c_end]

                row_placeholders = []
                args = []
                for r in stmt_rows:
                    row_placeholders.append("(" + ", ".join(["?" for _ in range(num_cols)]) + ")")
                    for v in r:
                        args.append(convert_value(v))

                multi_sql = f"INSERT INTO {name} ({cols_str}) VALUES {', '.join(row_placeholders)}"
                reqs.append(make_execute(multi_sql, args))

            reqs.append(make_close())
            execute_pipeline(reqs)
            uploaded += len(p_rows)
            print(f"   -> Progresso: {uploaded}/{total} registros inseridos ({uploaded/total*100:.1f}%)", end="\r")

        print(f"\n   ✅ {name}: {total} registros enviados com sucesso!")

    # Recriar FTS se aplicável
    try:
        print("\n🔍 Recriando índices FTS...")
        triggers = [
            "trg_questions_fts_ins", "trg_questions_fts_upd", "trg_questions_fts_del",
            "trg_explanations_fts_ins", "trg_explanations_fts_upd", "trg_explanations_fts_del"
        ]
        for t in triggers:
            try:
                execute_pipeline([make_execute(f"DROP TRIGGER IF EXISTS {t}"), make_close()])
            except Exception:
                pass

        execute_pipeline([
            make_execute("DROP TABLE IF EXISTS questions_fts"),
            make_execute("CREATE VIRTUAL TABLE questions_fts USING fts5(stem, explanation)"),
            make_execute("""
                INSERT INTO questions_fts (rowid, stem, explanation)
                SELECT q.id, q.stem, e.explanation_text
                FROM questions q
                LEFT JOIN explanations e ON q.id = e.question_id
            """),
            make_execute("PRAGMA foreign_keys=ON"),
            make_close()
        ])
        print("   ✅ Índices FTS recriados com sucesso!")
    except Exception as e:
        print("   Aviso FTS:", e)

    # Validação no Turso
    print("\n=== VALIDAÇÃO FINAL NO TURSO ===")
    res = execute_pipeline([
        make_execute("SELECT COUNT(*) FROM questions"),
        make_execute("SELECT COUNT(*) FROM alternatives"),
        make_execute("SELECT COUNT(*) FROM explanations"),
        make_execute("SELECT COUNT(*) FROM question_images"),
        make_execute("SELECT COUNT(*) FROM questions_fts"),
        make_close()
    ])

    results = res.get("results", [])
    q_cnt = results[0]["response"]["result"]["rows"][0][0]["value"]
    alt_cnt = results[1]["response"]["result"]["rows"][0][0]["value"]
    exp_cnt = results[2]["response"]["result"]["rows"][0][0]["value"]
    qi_cnt = results[3]["response"]["result"]["rows"][0][0]["value"]
    fts_cnt = results[4]["response"]["result"]["rows"][0][0]["value"]

    print(f"  - Questões: {q_cnt}")
    print(f"  - Alternativas: {alt_cnt}")
    print(f"  - Explicações: {exp_cnt}")
    print(f"  - Imagens: {qi_cnt}")
    print(f"  - Índice FTS: {fts_cnt}")

    local.close()
    elapsed = time.time() - t0
    print("\n" + "=" * 80)
    print(f"🎉 SINCRONIZAÇÃO COM A NUVEM CONCLUÍDA EM {elapsed:.1f} SEGUNDOS!")
    print("=" * 80)

if __name__ == "__main__":
    sync()
