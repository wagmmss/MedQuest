import os
import sqlite3
import time
import requests
from dotenv import load_dotenv

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

def execute_pipeline(session, requests_list, max_retries=3, timeout=60):
    payload = {"requests": requests_list}
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = session.post(PIPELINE_URL, headers=HEADERS, json=payload, timeout=timeout)
            if resp.status_code == 200:
                data = resp.json()
                for r in data.get("results", []):
                    if r.get("type") == "error":
                        err_msg = r.get("error", {}).get("message", str(r.get("error")))
                        print(f"  [AVISO] Erro na query do lote: {err_msg}", flush=True)
                return data
            elif resp.status_code in (429, 500, 502, 503, 504):
                time.sleep(1.5 * attempt)
                continue
            else:
                raise Exception(f"HTTP {resp.status_code}: {resp.text[:400]}")
        except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
            last_err = e
            if attempt < max_retries:
                time.sleep(2 * attempt)
            else:
                raise Exception(f"Pipeline request falhou após {max_retries} tentativas: {e}") from e
    if last_err:
        raise last_err

def sync_incremental():
    t0 = time.time()
    print("=== SINCRONIZAÇÃO INCREMENTAL INTELIGENTE (TURSO CLOUD) ===", flush=True)
    session = requests.Session()
    local = sqlite3.connect(LOCAL_DB)
    local.row_factory = sqlite3.Row
    cur = local.cursor()

    # 1. Obter IDs existentes no Turso
    print("Verificando estado do Turso Cloud...", flush=True)
    res = execute_pipeline(session, [
        make_execute("SELECT id FROM questions"),
        make_execute("SELECT DISTINCT question_id FROM alternatives"),
        make_execute("SELECT question_id FROM explanations"),
        make_execute("SELECT DISTINCT question_id FROM question_images"),
        make_close()
    ])
    
    results = res.get("results", [])
    remote_q_ids = set(int(r[0]["value"]) for r in results[0]["response"]["result"]["rows"] if r)
    remote_alt_qids = set(int(r[0]["value"]) for r in results[1]["response"]["result"]["rows"] if r)
    remote_exp_qids = set(int(r[0]["value"]) for r in results[2]["response"]["result"]["rows"] if r)
    remote_img_qids = set(int(r[0]["value"]) for r in results[3]["response"]["result"]["rows"] if r) if len(results) > 3 else set()

    print(f"Turso: {len(remote_q_ids)} questões, {len(remote_alt_qids)} com alternativas, {len(remote_exp_qids)} com explicações.", flush=True)

    # 2. Identificar questões faltantes
    cur.execute("SELECT * FROM questions")
    all_local_q = cur.fetchall()
    missing_q = [q for q in all_local_q if q['id'] not in remote_q_ids]
    
    if missing_q:
        total_missing_q = len(missing_q)
        print(f"Inserindo {total_missing_q} novas questões em lotes...", flush=True)
        cols = [c['name'] for c in cur.execute("PRAGMA table_info(questions)").fetchall()]
        insert_q_sql = f"INSERT OR REPLACE INTO questions ({', '.join(cols)}) VALUES ({', '.join(['?' for _ in cols])})"
        
        batch_size = 50
        for i in range(0, total_missing_q, batch_size):
            chunk = missing_q[i:i+batch_size]
            reqs = []
            for q in chunk:
                args = [convert_value(q[c]) for c in cols]
                reqs.append(make_execute(insert_q_sql, args))
            reqs.append(make_close())
            execute_pipeline(session, reqs)
            print(f"  -> Questões: {min(i + batch_size, total_missing_q)}/{total_missing_q} enviadas...", flush=True)
        print(f"-> {total_missing_q} questões sincronizadas com sucesso.", flush=True)

    # 3. Identificar alternativas faltantes
    all_local_qids = set(q['id'] for q in all_local_q)
    missing_alt_qids = all_local_qids - remote_alt_qids
    
    if missing_alt_qids:
        print(f"Identificadas {len(missing_alt_qids)} questões sem alternativas no Turso.", flush=True)
        cur.execute("SELECT * FROM alternatives")
        all_local_alts = cur.fetchall()
        missing_alts = [a for a in all_local_alts if a['question_id'] in missing_alt_qids]
        
        if missing_alts:
            total_missing_alts = len(missing_alts)
            print(f"Inserindo {total_missing_alts} alternativas em lotes...", flush=True)
            alt_cols = [c['name'] for c in cur.execute("PRAGMA table_info(alternatives)").fetchall()]
            insert_alt_sql = f"INSERT OR REPLACE INTO alternatives ({', '.join(alt_cols)}) VALUES ({', '.join(['?' for _ in alt_cols])})"
            
            batch_size = 150
            for i in range(0, total_missing_alts, batch_size):
                chunk = missing_alts[i:i+batch_size]
                reqs = []
                for a in chunk:
                    args = [convert_value(a[c]) for c in alt_cols]
                    reqs.append(make_execute(insert_alt_sql, args))
                reqs.append(make_close())
                execute_pipeline(session, reqs)
                print(f"  -> Alternativas: {min(i + batch_size, total_missing_alts)}/{total_missing_alts} enviadas...", flush=True)
            print(f"-> {total_missing_alts} alternativas sincronizadas com sucesso.", flush=True)

    # 4. Identificar explicações faltantes
    missing_exp_qids = all_local_qids - remote_exp_qids
    if missing_exp_qids:
        print(f"Identificadas {len(missing_exp_qids)} questões sem explicação no Turso.", flush=True)
        cur.execute("SELECT * FROM explanations")
        all_local_exps = cur.fetchall()
        missing_exps = [e for e in all_local_exps if e['question_id'] in missing_exp_qids]
        
        if missing_exps:
            total_missing_exps = len(missing_exps)
            print(f"Inserindo {total_missing_exps} explicações em lotes...", flush=True)
            exp_cols = [c['name'] for c in cur.execute("PRAGMA table_info(explanations)").fetchall()]
            insert_exp_sql = f"INSERT OR REPLACE INTO explanations ({', '.join(exp_cols)}) VALUES ({', '.join(['?' for _ in exp_cols])})"
            
            batch_size = 50
            for i in range(0, total_missing_exps, batch_size):
                chunk = missing_exps[i:i+batch_size]
                reqs = []
                for e in chunk:
                    args = [convert_value(e[c]) for c in exp_cols]
                    reqs.append(make_execute(insert_exp_sql, args))
                reqs.append(make_close())
                execute_pipeline(session, reqs)
                print(f"  -> Explicações: {min(i + batch_size, total_missing_exps)}/{total_missing_exps} enviadas...", flush=True)
            print(f"-> {total_missing_exps} explicações sincronizadas com sucesso.", flush=True)

    # 4.5 Identificar imagens faltantes
    missing_img_qids = all_local_qids - remote_img_qids
    if missing_img_qids:
        cur.execute("SELECT * FROM question_images")
        all_local_imgs = cur.fetchall()
        missing_imgs = [img for img in all_local_imgs if img['question_id'] in missing_img_qids]
        if missing_imgs:
            total_missing_imgs = len(missing_imgs)
            print(f"Identificadas {total_missing_imgs} imagens para sincronizar no Turso...", flush=True)
            img_cols = [c['name'] for c in cur.execute("PRAGMA table_info(question_images)").fetchall()]
            insert_img_sql = f"INSERT OR REPLACE INTO question_images ({', '.join(img_cols)}) VALUES ({', '.join(['?' for _ in img_cols])})"
            
            batch_size = 50
            for i in range(0, total_missing_imgs, batch_size):
                chunk = missing_imgs[i:i+batch_size]
                reqs = []
                for img in chunk:
                    args = [convert_value(img[c]) for c in img_cols]
                    reqs.append(make_execute(insert_img_sql, args))
                reqs.append(make_close())
                execute_pipeline(session, reqs)
            print(f"-> {total_missing_imgs} imagens sincronizadas com sucesso.", flush=True)

    # 5. Atualizar FTS para novas questões em lotes
    all_new_qids = list(set(q['id'] for q in missing_q) | missing_alt_qids | missing_exp_qids)
    if all_new_qids:
        total_fts = len(all_new_qids)
        print(f"Atualizando índice FTS para {total_fts} questões em lotes...", flush=True)
        fts_sql = """
            INSERT OR REPLACE INTO questions_fts (rowid, stem, explanation)
            SELECT q.id, q.stem, e.explanation_text
            FROM questions q
            LEFT JOIN explanations e ON q.id = e.question_id
            WHERE q.id = ?
        """
        batch_size = 100
        for i in range(0, total_fts, batch_size):
            chunk = all_new_qids[i:i+batch_size]
            fts_reqs = []
            for q_id in chunk:
                fts_reqs.append(make_execute(fts_sql, [convert_value(q_id)]))
            fts_reqs.append(make_close())
            try:
                execute_pipeline(session, fts_reqs)
            except Exception as e:
                print(f"  [AVISO] FTS lote {i//batch_size + 1}: {e}", flush=True)
        print(f"-> Índice FTS atualizado para {total_fts} questões.", flush=True)

    dt = time.time() - t0
    print(f"\n[SUCESSO] Sincronização incremental inteligente concluída em {dt:.2f} segundos!", flush=True)

if __name__ == "__main__":
    sync_incremental()
