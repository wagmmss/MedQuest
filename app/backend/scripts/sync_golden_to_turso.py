"""
Sincroniza a tabela de explanations locais para o banco remoto Turso via HTTP Pipeline v2 em chunks de alta velocidade.
"""

import os
import sqlite3
import json
import urllib.request
import urllib.error

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "medquest.db")
ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")

def load_env_vars():
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip("'\""))

load_env_vars()

TURSO_URL = os.environ.get("TURSO_DATABASE_URL", "").replace("libsql://", "https://") + "/v2/pipeline"
TURSO_TOKEN = os.environ.get("TURSO_AUTH_TOKEN", "")

def sync_explanations(chunk_size: int = 200):
    if not TURSO_TOKEN or not TURSO_URL:
        print("[ERRO] TURSO_DATABASE_URL ou TURSO_AUTH_TOKEN não configurados.")
        return

    print(f"Conectando ao banco local: {DB_PATH}")
    local_conn = sqlite3.connect(DB_PATH)
    local_conn.row_factory = sqlite3.Row
    local_rows = local_conn.execute("SELECT question_id, explanation_text, generated_at, reviewed_at FROM explanations WHERE explanation_text IS NOT NULL").fetchall()
    
    print(f"Explanations locais com conteúdo: {len(local_rows)}")
    
    headers = {
        "Authorization": f"Bearer {TURSO_TOKEN}",
        "Content-Type": "application/json"
    }

    # Fetch remote explanations map
    print("Consultando estado remoto no Turso...")
    req_body = {
        "requests": [{"type": "execute", "stmt": {"sql": "SELECT question_id, length(explanation_text) FROM explanations WHERE explanation_text IS NOT NULL"}}]
    }
    
    req = urllib.request.Request(TURSO_URL, data=json.dumps(req_body).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))["results"][0]["response"]["result"]
            remote_len_map = {}
            for r in data.get("rows", []):
                qid = int(r[0]["value"])
                length = int(r[1]["value"]) if r[1]["value"] is not None else 0
                remote_len_map[qid] = length
    except Exception as e:
        print(f"[AVISO] Não foi possível obter mapa remoto ({e}). Enviando em modo upsert completo.")
        remote_len_map = {}

    to_sync = []
    for r in local_rows:
        qid = r["question_id"]
        text = r["explanation_text"]
        gen = r["generated_at"] or ""
        rev = r["reviewed_at"] or ""
        
        # Sync if missing remotely or length differs
        if remote_len_map.get(qid) != len(text):
            to_sync.append((qid, text, gen, rev))
            
    print(f"Total de explicações a sincronizar: {len(to_sync)}")
    if not to_sync:
        print("Banco remoto já está 100% sincronizado com o local.")
        return

    for i in range(0, len(to_sync), chunk_size):
        chunk = to_sync[i:i + chunk_size]
        requests_list = [{"type": "execute", "stmt": {"sql": "BEGIN"}}]
        
        for qid, text, gen, rev in chunk:
            safe_text = text.replace("'", "''")
            safe_gen = gen.replace("'", "''")
            safe_rev = rev.replace("'", "''")
            
            sql = f"INSERT INTO explanations (question_id, explanation_text, generated_at, reviewed_at) VALUES ({qid}, '{safe_text}', '{safe_gen}', '{safe_rev}') ON CONFLICT(question_id) DO UPDATE SET explanation_text = excluded.explanation_text, reviewed_at = excluded.reviewed_at"
            requests_list.append({
                "type": "execute",
                "stmt": {"sql": sql}
            })
            
        requests_list.append({"type": "execute", "stmt": {"sql": "COMMIT"}})
        
        chunk_num = (i // chunk_size) + 1
        total_chunks = (len(to_sync) + chunk_size - 1) // chunk_size
        print(f"Enviando chunk {chunk_num}/{total_chunks} ({len(chunk)} itens)...")
        
        chunk_req = urllib.request.Request(TURSO_URL, data=json.dumps({"requests": requests_list}).encode("utf-8"), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(chunk_req, timeout=90) as cresp:
                if cresp.status == 200:
                    print(f"  -> Chunk {chunk_num} OK")
        except Exception as e:
            print(f"  -> Falha no chunk {chunk_num}: {e}")

    print("\nSincronização com Turso finalizada com sucesso!")

if __name__ == "__main__":
    sync_explanations()
