import sys
sys.path.insert(0, 'app/backend')
from api.db import get_db, db_transaction
import sqlite3
from flask import Flask

app = Flask(__name__)
with app.app_context():
    turso_db = get_db()
    local_conn = sqlite3.connect('app/backend/medquest.db')
    local_conn.row_factory = sqlite3.Row
    
    turso_rows = turso_db.execute('SELECT id, subtema FROM questions').fetchall()
    turso_map = {r['id']: r['subtema'] for r in turso_rows}
    
    local_rows = local_conn.execute('SELECT id, subtema FROM questions').fetchall()
    
    updates = []
    for r in local_rows:
        q_id = r['id']
        expected = r['subtema']
        current = turso_map.get(q_id)
        if current != expected:
            updates.append((expected, q_id))
        
    print(f'Found {len(updates)} out of sync updates for Turso...')
    if len(updates) > 0:
        chunk_size = 500
        for i in range(0, len(updates), chunk_size):
            chunk = updates[i:i+chunk_size]
            with db_transaction(turso_db, immediate=True):
                for expected, q_id in chunk:
                    turso_db.execute('UPDATE questions SET subtema = ? WHERE id = ?', (expected, q_id))
            print(f'Sent chunk {i}-{i+chunk_size}')
    print('Done!')
