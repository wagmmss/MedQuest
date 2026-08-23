import sqlite3
import re

conn = sqlite3.connect("app/backend/medquest.db")
conn.row_factory = sqlite3.Row

rows = conn.execute("""
    SELECT id, stem, topic, subtema 
    FROM questions 
    WHERE area = 'Pediatria' AND (
        stem LIKE '%membrana hialina%' OR stem LIKE '%taquipneia transit%' OR stem LIKE '%desconforto respiratório%' 
        OR stem LIKE '%aspiração meconial%' OR stem LIKE '%surfactante%'
        OR stem LIKE '%hipoglicemia%' OR stem LIKE '%mãe diabética%'
    )
""").fetchall()

print(f"Found {len(rows)} candidate questions for neonatal respiratory/metabolic:")
resp_ids = []
metab_ids = []
for r in rows:
    stem = r["stem"].lower()
    if any(w in stem for w in ["membrana hialina", "taquipneia transit", "desconforto respiratório", "aspiração meconial", "surfactante"]):
        resp_ids.append(r["id"])
    elif any(w in stem for w in ["hipoglicemia", "mãe diabética"]):
        metab_ids.append(r["id"])

print(f"Respiratory count: {len(resp_ids)}")
print(f"Metabolic count: {len(metab_ids)}")

if resp_ids:
    conn.execute(f"UPDATE questions SET subtema = 'Período Neonatal: Doenças Respiratórias' WHERE id IN ({','.join(map(str, resp_ids))})")
if metab_ids:
    conn.execute(f"UPDATE questions SET subtema = 'Período Neonatal: Doenças do Metabolismo' WHERE id IN ({','.join(map(str, metab_ids))})")

conn.commit()
print("Updated subtemas in medquest.db!")
