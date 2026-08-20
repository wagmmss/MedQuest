import glob
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "medquest.db")
CHUNK_DIR = r"C:\Users\wmors\AppData\Local\Temp\claude\C--Users-wmors-Documents-MedQuest\ae461d9d-064a-41c6-b5b1-e555da5c36e3\scratchpad\explain_chunks"

pattern = sys.argv[1] if len(sys.argv) > 1 else "result_*.json"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

valid_ids = set(r[0] for r in cur.execute("SELECT id FROM questions WHERE missing_alts = 0").fetchall())

now = datetime.now(timezone.utc).isoformat()
n_updated = 0
n_skipped_invalid_id = 0
n_empty = 0

result_files = sorted(glob.glob(os.path.join(CHUNK_DIR, pattern)))
print(f"Encontrados {len(result_files)} arquivos: {[os.path.basename(p) for p in result_files]}")

for path in result_files:
    try:
        with open(path, encoding="utf-8") as f:
            rows = json.load(f)
        for r in rows:
            qid = r.get("id")
            exp = (r.get("explanation") or "").strip()
            if qid not in valid_ids:
                n_skipped_invalid_id += 1
                continue
            if not exp:
                n_empty += 1
                continue
            cur.execute(
                """INSERT INTO explanations (question_id, explanation_text, generated_at)
                   VALUES (?, ?, ?)
                   ON CONFLICT(question_id) DO UPDATE SET
                     explanation_text = excluded.explanation_text,
                     generated_at = excluded.generated_at""",
                (qid, exp, now),
            )
            n_updated += 1
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"ERRO ao processar {path}: {e} (progresso deste arquivo descartado, anteriores já commitados)")

total_with_exp = cur.execute(
    "SELECT COUNT(*) FROM explanations WHERE explanation_text IS NOT NULL"
).fetchone()[0]

print(f"Explicações gravadas/atualizadas: {n_updated}")
print(f"Ids inválidos ignorados: {n_skipped_invalid_id}")
print(f"Explicações vazias ignoradas: {n_empty}")
print(f"Total de questões com explicação no banco agora: {total_with_exp}")

conn.close()
