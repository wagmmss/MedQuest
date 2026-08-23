import sys
sys.path.insert(0, 'app/backend')
from api.db import get_db, db_transaction
from flask import Flask
import sqlite3
import json

app = Flask(__name__)

with open('app/backend/data/subtema_map.json', 'r', encoding='utf-8') as f:
    smap = json.load(f)

with app.app_context():
    turso_db = get_db()
    local_conn = sqlite3.connect('app/backend/medquest.db')
    local_conn.row_factory = sqlite3.Row
    
    # 1. Fix local DB
    print("Fixing local DB...")
    cur = local_conn.cursor()
    for subtema, s_id in smap.items():
        cur.execute("UPDATE questions SET subtema_id = ? WHERE subtema = ?", (s_id, subtema))
    local_conn.commit()
    
    # 2. Fix Turso
    print("Fixing Turso DB...")
    remote_rows = turso_db.execute("SELECT id, subtema, subtema_id FROM questions").fetchall()
    
    batch_stmts = []
    for r in remote_rows:
        q_id, subtema, current_id = r['id'], r['subtema'], r['subtema_id']
        expected_id = smap.get(subtema)
        if expected_id and current_id != expected_id:
            batch_stmts.append(("UPDATE questions SET subtema_id = ? WHERE id = ?", (expected_id, q_id)))
            
    if batch_stmts:
        print(f"Updating {len(batch_stmts)} records in Turso...")
        if hasattr(turso_db, "batch"):
            turso_db.batch(batch_stmts)
        print("Done!")
    else:
        print("Turso subtema_ids already up to date.")
