import os
import requests
from dotenv import load_dotenv
import sqlite3

load_dotenv('app/backend/.env')
url = os.environ['TURSO_DATABASE_URL'].replace("libsql://", "https://") + "/v2/pipeline"
token = os.environ['TURSO_AUTH_TOKEN']

local_conn = sqlite3.connect('app/backend/medquest.db')
local_conn.row_factory = sqlite3.Row
local_rows = local_conn.execute("SELECT id, subtema FROM questions").fetchall()
local_map = {r['id']: r['subtema'] for r in local_rows}

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

resp = requests.post(url, headers=headers, json={
    "requests": [{"type": "execute", "stmt": {"sql": "SELECT id, subtema FROM questions"}}]
})
data = resp.json()["results"][0]["response"]["result"]

remote_map = {}
for r in data["rows"]:
    q_id = r[0]["value"]
    subtema = r[1]["value"]
    remote_map[int(q_id)] = subtema

updates = []
for q_id, remote_subtema in remote_map.items():
    local_subtema = local_map.get(q_id)
    if local_subtema and local_subtema != remote_subtema:
        updates.append((local_subtema, q_id))

print(f"Found {len(updates)} updates.")

if updates:
    for i in range(0, len(updates), 500):
        chunk = updates[i:i+500]
        requests_list = []
        
        # Start transaction
        requests_list.append({"type": "execute", "stmt": {"sql": "BEGIN"}})
        
        for new_subtema, q_id in chunk:
            safe_subtema = new_subtema.replace("'", "''")
            requests_list.append({
                "type": "execute",
                "stmt": {
                    "sql": f"UPDATE questions SET subtema = '{safe_subtema}' WHERE id = {q_id}"
                }
            })
            
        # Commit transaction
        requests_list.append({"type": "execute", "stmt": {"sql": "COMMIT"}})
        
        print(f"Sending chunk {i//500 + 1}...")
        resp = requests.post(url, headers=headers, json={"requests": requests_list}, timeout=60)
        if resp.status_code == 200:
            print(f"Chunk {i//500 + 1} SUCCESS")
        else:
            print(f"Chunk {i//500 + 1} FAILED: {resp.text}")

print("Done")
