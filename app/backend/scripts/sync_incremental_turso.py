import os
import sqlite3
import time
import requests
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(env_path)

TURSO_URL = os.environ.get("TURSO_DATABASE_URL", "libsql://medquest-wagmss.aws-us-east-1.turso.io").replace("libsql://", "https://").replace("wss://", "https://")
TURSO_TOKEN = os.environ.get("TURSO_AUTH_TOKEN") or "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3ODYyMjYzMjUsImlkIjoiMDE5ZmUzNjItNmUwMS03YTE5LTkyZjctMGRhOTJlZTk5OWQ0Iiwia2lkIjoiTlhsOWVXamdJaXcwVW5vNmhSTGdhSVFsRl9OaVBxSm13eHB6U21hY1hNUSIsInJpZCI6IjJhMjVkMzQ0LWI3ZTctNDA5YS1hMmIzLTVlNWNkMTgxMWE4NCJ9.jOZcgW1n4dCGN1W8SPG-vMFpj734oh0Wn1NDl7lteH6NsD5nqeOXmr1tZm4TEQVhTO-_2aN29LBz1u7o29D1Dw"
LOCAL_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "medquest.db")

PIPELINE_URL = f"{TURSO_URL}/v3/pipeline"
HEADERS = {
    "Authorization": f"Bearer {TURSO_TOKEN}",
    "Content-Type": "application/json",
}

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
    resp = session.post(PIPELINE_URL, headers=HEADERS, json=payload, timeout=60)
    if resp.status_code == 200:
        return resp.json()
    raise Exception(f"HTTP {resp.status_code}: {resp.text[:400]}")

def sync_incremental():
    t0 = time.time()
    print("=== SINCRONIZAÇÃO INCREMENTAL INTELIGENTE (TURSO CLOUD) ===")
    session = requests.Session()
    local = sqlite3.connect(LOCAL_DB)
    local.row_factory = sqlite3.Row
    cur = local.cursor()

    # 1. Obter IDs existentes no Turso
    print("Verificando estado do Turso Cloud...")
    res = execute_pipeline(session, [
        make_execute("SELECT id FROM questions"),
        make_execute("SELECT DISTINCT question_id FROM alternatives"),
        make_execute("SELECT question_id FROM explanations"),
        make_close()
    ])
    
    results = res.get("results", [])
    remote_q_ids = set(int(r[0]["value"]) for r in results[0]["response"]["result"]["rows"] if r)
    remote_alt_qids = set(int(r[0]["value"]) for r in results[1]["response"]["result"]["rows"] if r)
    remote_exp_qids = set(int(r[0]["value"]) for r in results[2]["response"]["result"]["rows"] if r)

    print(f"Turso: {len(remote_q_ids)} questões, {len(remote_alt_qids)} com alternativas, {len(remote_exp_qids)} com explicações.")

    # 2. Identificar questões faltantes
    cur.execute("SELECT * FROM questions")
    all_local_q = cur.fetchall()
    missing_q = [q for q in all_local_q if q['id'] not in remote_q_ids]
    
    if missing_q:
        print(f"Inserindo {len(missing_q)} novas questões...")
        cols = [c['name'] for c in cur.execute("PRAGMA table_info(questions)").fetchall()]
        insert_q_sql = f"INSERT OR REPLACE INTO questions ({', '.join(cols)}) VALUES ({', '.join(['?' for _ in cols])})"
        
        reqs = []
        for q in missing_q:
            args = [convert_value(q[c]) for c in cols]
            reqs.append(make_execute(insert_q_sql, args))
        reqs.append(make_close())
        execute_pipeline(session, reqs)
        print(f"-> {len(missing_q)} questões sincronizadas.")

    # 3. Identificar alternativas faltantes
    all_local_qids = set(q['id'] for q in all_local_q)
    missing_alt_qids = all_local_qids - remote_alt_qids
    
    if missing_alt_qids:
        print(f"Identificadas {len(missing_alt_qids)} questões sem alternativas no Turso.")
        placeholders = ','.join('?' * len(missing_alt_qids))
        cur.execute(f"SELECT * FROM alternatives WHERE question_id IN ({placeholders})", list(missing_alt_qids))
        missing_alts = cur.fetchall()
        
        if missing_alts:
            alt_cols = [c['name'] for c in cur.execute("PRAGMA table_info(alternatives)").fetchall()]
            insert_alt_sql = f"INSERT OR REPLACE INTO alternatives ({', '.join(alt_cols)}) VALUES ({', '.join(['?' for _ in alt_cols])})"
            
            # Enviar em lotes de 200 para velocidade
            batch_size = 200
            for i in range(0, len(missing_alts), batch_size):
                chunk = missing_alts[i:i+batch_size]
                reqs = []
                for a in chunk:
                    args = [convert_value(a[c]) for c in alt_cols]
                    reqs.append(make_execute(insert_alt_sql, args))
                reqs.append(make_close())
                execute_pipeline(session, reqs)
            print(f"-> {len(missing_alts)} alternativas sincronizadas com sucesso.")

    # 4. Identificar explicações faltantes
    missing_exp_qids = all_local_qids - remote_exp_qids
    if missing_exp_qids:
        print(f"Identificadas {len(missing_exp_qids)} questões sem explicação no Turso.")
        placeholders = ','.join('?' * len(missing_exp_qids))
        cur.execute(f"SELECT * FROM explanations WHERE question_id IN ({placeholders})", list(missing_exp_qids))
        missing_exps = cur.fetchall()
        
        if missing_exps:
            exp_cols = [c['name'] for c in cur.execute("PRAGMA table_info(explanations)").fetchall()]
            insert_exp_sql = f"INSERT OR REPLACE INTO explanations ({', '.join(exp_cols)}) VALUES ({', '.join(['?' for _ in exp_cols])})"
            
            batch_size = 100
            for i in range(0, len(missing_exps), batch_size):
                chunk = missing_exps[i:i+batch_size]
                reqs = []
                for e in chunk:
                    args = [convert_value(e[c]) for c in exp_cols]
                    reqs.append(make_execute(insert_exp_sql, args))
                reqs.append(make_close())
                execute_pipeline(session, reqs)
            print(f"-> {len(missing_exps)} explicações sincronizadas com sucesso.")

    # 5. Atualizar FTS para novas questões
    all_new_qids = list(set(q['id'] for q in missing_q) | missing_alt_qids | missing_exp_qids)
    if all_new_qids:
        fts_reqs = []
        for q_id in all_new_qids:
            fts_reqs.append(make_execute("""
                INSERT OR REPLACE INTO questions_fts (rowid, stem, explanation)
                SELECT q.id, q.stem, e.explanation_text
                FROM questions q
                LEFT JOIN explanations e ON q.id = e.question_id
                WHERE q.id = ?
            """, [convert_value(q_id)]))
        fts_reqs.append(make_close())
        try:
            execute_pipeline(session, fts_reqs)
            print("-> Índice FTS atualizado.")
        except Exception:
            pass

    dt = time.time() - t0
    print(f"\n[SUCESSO] Sincronização incremental inteligente concluída em {dt:.2f} segundos!")

if __name__ == "__main__":
    sync_incremental()
