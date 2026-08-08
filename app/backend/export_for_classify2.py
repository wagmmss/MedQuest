import json
import os
import sqlite3
import sys

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "medquest.db")
OUT_DIR = r"C:\Users\wmors\AppData\Local\Temp\claude\C--Users-wmors-Documents-MedQuest\ae461d9d-064a-41c6-b5b1-e555da5c36e3\scratchpad\classify_chunks2"
os.makedirs(OUT_DIR, exist_ok=True)

SOURCE_FILE = sys.argv[1]
N_CHUNKS = int(sys.argv[2]) if len(sys.argv) > 2 else 3

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
rows = conn.execute(
    "SELECT id, stem, topic, source_file FROM questions WHERE source_file = ? AND area IS NULL ORDER BY id",
    (SOURCE_FILE,),
).fetchall()
conn.close()

data = [
    {"id": r["id"], "stem": r["stem"], "topic_tag": r["topic"] or "", "source_file": r["source_file"]}
    for r in rows
]

chunk_size = -(-len(data) // N_CHUNKS)
chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]

for i, chunk in enumerate(chunks, start=1):
    path = os.path.join(OUT_DIR, f"chunk_{i}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(chunk, f, ensure_ascii=False, indent=0)
    print(f"chunk_{i}.json -> {len(chunk)} questões (ids {chunk[0]['id']}..{chunk[-1]['id']})")

print(f"\nTotal: {len(data)} questões em {len(chunks)} arquivos, em {OUT_DIR}")
