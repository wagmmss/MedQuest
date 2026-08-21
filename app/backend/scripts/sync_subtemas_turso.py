import os
import sqlite3

import requests
from dotenv import load_dotenv

load_dotenv()

TURSO_URL = os.environ.get('TURSO_DATABASE_URL')
TURSO_TOKEN = os.environ.get('TURSO_AUTH_TOKEN')
DB_PATH = 'C:\\dev\\MedQuest\\app\\backend\\medquest.db'

def convert_value(val):
    if val is None: return {'type': 'null'}
    elif isinstance(val, int): return {'type': 'integer', 'value': str(val)}
    elif isinstance(val, float): return {'type': 'float', 'value': val}
    else: return {'type': 'text', 'value': str(val)}

def make_execute_batch(stmts):
    url = f"{TURSO_URL.replace('libsql://', 'https://')}/v2/pipeline"
    headers = {
        'Authorization': f'Bearer {TURSO_TOKEN}',
        'Content-Type': 'application/json'
    }
    requests_payload = [{'type': 'execute', 'stmt': s} for s in stmts]
    requests_payload.append({'type': 'close'})
    try:
        resp = requests.post(url, headers=headers, json={'requests': requests_payload})
        if resp.status_code != 200:
            print("Error HTTP:", resp.status_code, resp.text)
        return resp.status_code == 200
    except Exception as e:
        print("Exception:", e)
        return False

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute('SELECT id, area, subtema FROM questions')
rows = cur.fetchall()

batch = []
updated = 0
for i, row in enumerate(rows):
    batch.append({
        'sql': 'UPDATE questions SET area = ?, subtema = ? WHERE id = ?',
        'args': [convert_value(row['area']), convert_value(row['subtema']), convert_value(row['id'])]
    })
    
    if len(batch) >= 100 or i == len(rows) - 1:
        success = make_execute_batch(batch)
        if success:
            updated += len(batch)
            print(f'Syncing... {updated}/{len(rows)}')
        else:
            print('Batch failed!')
        batch = []

print(f'Done syncing {updated} to Turso!')
