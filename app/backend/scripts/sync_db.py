import os
import sqlite3
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from flask import Flask

from api.db import get_db

app = Flask(__name__)
with app.app_context():
    turso_db = get_db()
    local_db = sqlite3.connect('medquest.db')
    local_db.row_factory = sqlite3.Row
    
    print("Fetching valid question IDs from Turso...")
    valid_qids_rows = turso_db.execute('SELECT id FROM questions').fetchall()
    valid_qids = {r['id'] for r in valid_qids_rows}
    print(f"Found {len(valid_qids)} questions in Turso.")
    
    print("Syncing question_images to Turso...")
    turso_db.execute('DELETE FROM question_images')
    
    all_imgs = local_db.execute('SELECT question_id, file_path, order_index FROM question_images').fetchall()
    
    queries = []
    for img in all_imgs:
        if img['question_id'] in valid_qids:
            queries.append((
                "INSERT INTO question_images (question_id, file_path, order_index) VALUES (?,?,?)",
                (img['question_id'], img['file_path'], img['order_index'])
            ))
        
    print(f"Executing {len(queries)} inserts in batch...")
    for i in range(0, len(queries), 100):
        batch = queries[i:i+100]
        turso_db.batch(batch)
        print(f"  Batch {i//100 + 1} done.")
        
    turso_db.commit()
    print("Sync complete!")
