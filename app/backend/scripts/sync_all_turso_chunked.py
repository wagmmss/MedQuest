import sys
sys.path.insert(0, 'app/backend')

from api.db import get_db
from flask import Flask
import sqlite3

app = Flask(__name__)

def chunk_list(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

with app.app_context():
    turso_db = get_db()
    
    local_conn = sqlite3.connect('app/backend/medquest.db')
    local_conn.row_factory = sqlite3.Row
    local_rows = local_conn.execute("SELECT id, subtema FROM questions").fetchall()
    local_map = {r['id']: r['subtema'] for r in local_rows}
    
    remote_rows = turso_db.execute("SELECT id, subtema FROM questions").fetchall()
    remote_map = {r['id']: r['subtema'] for r in remote_rows}
    
    updates = []
    for q_id, remote_subtema in remote_map.items():
        local_subtema = local_map.get(q_id)
        if local_subtema and local_subtema != remote_subtema:
            updates.append((local_subtema, q_id))
    
    print(f"Found {len(updates)} questions to fix in Turso.")
    
    if updates:
        print("Using chunked batch API...")
        batch_stmts = []
        for new_subtema, q_id in updates:
            batch_stmts.append(("UPDATE questions SET subtema = ? WHERE id = ?", (new_subtema, q_id)))
        
        chunks = list(chunk_list(batch_stmts, 100))
        for i, chunk in enumerate(chunks):
            turso_db.batch(chunk)
            print(f"Batch {i+1}/{len(chunks)} executed successfully.")
        
        print("All chunks executed successfully!")
