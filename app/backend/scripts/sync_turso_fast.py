import os
from dotenv import load_dotenv
import sqlite3
import libsql

load_dotenv('app/backend/.env')

local_conn = sqlite3.connect('app/backend/medquest.db')
local_conn.row_factory = sqlite3.Row

turso_conn = libsql.connect(
    os.environ['TURSO_DATABASE_URL'], 
    auth_token=os.environ['TURSO_AUTH_TOKEN']
)

local_rows = local_conn.execute("SELECT id, subtema FROM questions").fetchall()
local_map = {row['id']: row['subtema'] for row in local_rows}

remote_rows = turso_conn.execute("SELECT id, subtema FROM questions").fetchall()
remote_map = {row[0]: row[1] for row in remote_rows}

updates = []
for q_id, remote_subtema in remote_map.items():
    if q_id in local_map:
        local_subtema = local_map[q_id]
        if local_subtema != remote_subtema:
            updates.append((local_subtema, q_id))

print(f"Found {len(updates)} questions to update in Turso.")

if updates:
    print("Executing executemany...")
    try:
        turso_conn.executemany("UPDATE questions SET subtema = ? WHERE id = ?", updates)
        turso_conn.commit()
        print("Done executemany!")
    except Exception as e:
        print("executemany failed:", e)
        print("Falling back to batch or something...")
