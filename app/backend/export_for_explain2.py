import json
import os
import sqlite3
import sys

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "medquest.db")
OUT_DIR = r"C:\Users\wmors\AppData\Local\Temp\claude\C--Users-wmors-Documents-MedQuest\ae461d9d-064a-41c6-b5b1-e555da5c36e3\scratchpad\explain_chunks2"
os.makedirs(OUT_DIR, exist_ok=True)

SOURCE_FILE = sys.argv[1]
CHUNK_SIZE = int(sys.argv[2]) if len(sys.argv) > 2 else 70
PREFIX = sys.argv[3] if len(sys.argv) > 3 else "uni"

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
questions = conn.execute(
    """SELECT id, stem, correct_letter, area, subtema FROM questions
       WHERE source_file = ? AND missing_alts = 0 AND correct_letter IS NOT NULL
       AND id NOT IN (SELECT question_id FROM explanations WHERE explanation_text IS NOT NULL)
       ORDER BY id""",
    (SOURCE_FILE,),
).fetchall()

data = []
for q in questions:
    alts = conn.execute(
        "SELECT letter, text FROM alternatives WHERE question_id = ? ORDER BY letter", (q["id"],)
    ).fetchall()
    data.append({
        "id": q["id"],
        "area": q["area"],
        "subtema": q["subtema"],
        "stem": q["stem"],
        "alternatives": [{"letter": a["letter"], "text": a["text"]} for a in alts],
        "correct_letter": q["correct_letter"],
    })
conn.close()

chunks = [data[i:i + CHUNK_SIZE] for i in range(0, len(data), CHUNK_SIZE)]

for i, chunk in enumerate(chunks, start=1):
    path = os.path.join(OUT_DIR, f"{PREFIX}_chunk_{i}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(chunk, f, ensure_ascii=False, indent=0)
    print(f"{PREFIX}_chunk_{i}.json -> {len(chunk)} questões (ids {chunk[0]['id']}..{chunk[-1]['id']})")

print(f"\nTotal: {len(data)} questões pendentes de explicação, em {len(chunks)} arquivos")
