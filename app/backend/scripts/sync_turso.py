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

# Fetch all local questions
print("Fetching local questions...")
local_rows = local_conn.execute("SELECT id, subtema FROM questions").fetchall()
local_map = {row['id']: row['subtema'] for row in local_rows}

print(f"Loaded {len(local_map)} local questions.")

# Fetch all remote questions
print("Fetching remote questions...")
remote_rows = turso_conn.execute("SELECT id, subtema FROM questions").fetchall()
remote_map = {row[0]: row[1] for row in remote_rows}

print(f"Loaded {len(remote_map)} remote questions.")

# Find differences
updates = []
for q_id, remote_subtema in remote_map.items():
    if q_id in local_map:
        local_subtema = local_map[q_id]
        if local_subtema != remote_subtema:
            updates.append((local_subtema, q_id))

print(f"Found {len(updates)} questions to update in Turso.")

if updates:
    # Print some examples
    print("Examples of updates:")
    for u in updates[:5]:
        print(f"ID {u[1]}: '{remote_map[u[1]]}' -> '{u[0]}'")
    
    print("Applying updates to Turso...")
    for i, (new_subtema, q_id) in enumerate(updates):
        turso_conn.execute("UPDATE questions SET subtema = ? WHERE id = ?", (new_subtema, q_id))
        if i % 100 == 0 and i > 0:
            print(f"Updated {i} / {len(updates)}...")
    
    turso_conn.commit()
    print("Updates applied and committed successfully.")
else:
    print("No updates needed. Turso matches local DB.")
