import os
import sqlite3
import time
import requests
import sys
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')

env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(env_path)

TURSO_URL = os.environ.get("TURSO_DATABASE_URL", "").replace("libsql://", "https://").replace("wss://", "https://")
TURSO_TOKEN = os.environ.get("TURSO_AUTH_TOKEN", "")
if not TURSO_URL or not TURSO_TOKEN:
    raise SystemExit("TURSO_DATABASE_URL e TURSO_AUTH_TOKEN são obrigatórios.")
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

def fast_incremental_sync():
    t0 = time.time()
    print("=== SINCRONIZAÇÃO INCREMENTAL RÁPIDA ===", flush=True)
    session = requests.Session()
    local = sqlite3.connect(LOCAL_DB)
    local.row_factory = sqlite3.Row
    cur = local.cursor()

    # 1. Obter os IDs de alternativas e explicações que já estão no Turso
    print("Consultando IDs remotos...", flush=True)
    res = execute_pipeline(session, [
        make_execute("SELECT id FROM alternatives"),
        make_execute("SELECT question_id FROM explanations"),
        make_close()
    ])
    
    remote_alt_ids = set(int(r[0]["value"]) for r in res["results"][0]["response"]["result"]["rows"] if r)
    remote_exp_ids = set(int(r[0]["value"]) for r in res["results"][1]["response"]["result"]["rows"] if r)
    print(f"Turso possui {len(remote_alt_ids)} alternativas e {len(remote_exp_ids)} explicações.", flush=True)

    # 2. Sincronizar alternativas faltantes
    cur.execute("SELECT * FROM alternatives")
    all_local_alts = cur.fetchall()
    missing_alts = [a for a in all_local_alts if a['id'] not in remote_alt_ids]
    
    if missing_alts:
        print(f"Enviando {len(missing_alts)} alternativas faltantes...", flush=True)
        alt_cols = [c['name'] for c in cur.execute("PRAGMA table_info(alternatives)").fetchall()]
        insert_alt_sql = f"INSERT INTO alternatives ({', '.join(alt_cols)}) VALUES ({', '.join(['?' for _ in alt_cols])})"
        
        batch_size = 250
        for i in range(0, len(missing_alts), batch_size):
            chunk = missing_alts[i:i+batch_size]
            reqs = []
            for a in chunk:
                args = [convert_value(a[c]) for c in alt_cols]
                reqs.append(make_execute(insert_alt_sql, args))
            reqs.append(make_close())
            execute_pipeline(session, reqs)
        print(f"-> {len(missing_alts)} alternativas sincronizadas com sucesso!", flush=True)

    # 3. Sincronizar explicações faltantes
    cur.execute("SELECT * FROM explanations")
    all_local_exps = cur.fetchall()
    missing_exps = [e for e in all_local_exps if e['question_id'] not in remote_exp_ids]
    
    if missing_exps:
        print(f"Enviando {len(missing_exps)} explicações faltantes...", flush=True)
        exp_cols = [c['name'] for c in cur.execute("PRAGMA table_info(explanations)").fetchall()]
        insert_exp_sql = f"INSERT INTO explanations ({', '.join(exp_cols)}) VALUES ({', '.join(['?' for _ in exp_cols])})"
        
        batch_size = 100
        for i in range(0, len(missing_exps), batch_size):
            chunk = missing_exps[i:i+batch_size]
            reqs = []
            for e in chunk:
                args = [convert_value(e[c]) for c in exp_cols]
                reqs.append(make_execute(insert_exp_sql, args))
            reqs.append(make_close())
            execute_pipeline(session, reqs)
        print(f"-> {len(missing_exps)} explicações sincronizadas com sucesso!", flush=True)

    dt = time.time() - t0
    print(f"\n[SUCESSO] Sincronização concluída em {dt:.2f} segundos!", flush=True)

if __name__ == "__main__":
    fast_incremental_sync()
