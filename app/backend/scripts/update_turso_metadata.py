import sqlite3
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

TURSO_URL = os.environ.get("TURSO_DATABASE_URL")
TURSO_TOKEN = os.environ.get("TURSO_AUTH_TOKEN")

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "medquest.db")

def convert_value(val):
    if val is None: return {"type": "null"}
    elif isinstance(val, int): return {"type": "integer", "value": str(val)}
    elif isinstance(val, float): return {"type": "float", "value": val}
    else: return {"type": "text", "value": str(val)}

def make_execute_batch(stmts):
    url = f"{TURSO_URL.replace('libsql://', 'https://')}/v2/pipeline"
    headers = {
        "Authorization": f"Bearer {TURSO_TOKEN}",
        "Content-Type": "application/json"
    }
    
    requests_payload = []
    for stmt in stmts:
        requests_payload.append({
            "type": "execute",
            "stmt": stmt
        })
    requests_payload.append({"type": "close"})
    
    data = {"requests": requests_payload}
    
    try:
        resp = requests.post(url, headers=headers, json=data)
        if resp.status_code != 200:
            print(f"Erro Turso HTTP {resp.status_code}: {resp.text}")
            return False
        return True
    except Exception as e:
        print(f"Erro request: {e}")
        return False

def run():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # We only need to update the area and subtema for the new questions
    cur.execute("""
        SELECT id, area, subtema
        FROM questions 
        WHERE source_file IN (
            'SUS-SP.pdf', 
            'SÍRIO EINSTEIN E SCMSP 2020 A 2023', 
            'SÍRIO EINSTEIN E SCMSP 2024 A 2026', 
            'UNIFESP E UNICAMP 2020 A 2022', 
            'UNIFESP E UNICAMP 2023 A 2026', 
            'USP 2020 a 2023', 
            'USP 2024 a 2026'
        )
    """)
    rows = cur.fetchall()
    
    print(f"Atualizando {len(rows)} questões no Turso...")
    
    batch = []
    updated = 0
    
    for i, row in enumerate(rows):
        batch.append({
            "sql": "UPDATE questions SET area = ?, subtema = ?, subtema_orig = ? WHERE id = ?",
            "args": [convert_value(row['area']), convert_value(row['subtema']), convert_value(row['subtema']), convert_value(row['id'])]
        })
        
        if len(batch) >= 20 or i == len(rows) - 1:
            success = make_execute_batch(batch)
            if success:
                updated += len(batch)
                print(f"Progresso: {updated}/{len(rows)}")
            else:
                print("Falha no lote.")
            batch = []

    print(f"Concluído. {updated} atualizadas no Turso.")

if __name__ == "__main__":
    run()
