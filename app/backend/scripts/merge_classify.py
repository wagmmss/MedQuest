import glob
import json
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "medquest.db")
CHUNK_DIR = r"C:\Users\wmors\AppData\Local\Temp\claude\C--Users-wmors-Documents-MedQuest\ae461d9d-064a-41c6-b5b1-e555da5c36e3\scratchpad\classify_chunks"

VALID_AREAS = {
    "Cirurgia", "Clínica Médica", "Ginecologia e Obstetrícia",
    "Pediatria", "Medicina Preventiva e Social",
}

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

total_ids = set(r[0] for r in cur.execute("SELECT id FROM questions").fetchall())

seen_ids = set()
n_updated = 0
n_bad_area = 0
bad_area_values = set()

result_files = sorted(glob.glob(os.path.join(CHUNK_DIR, "result_*.json")))
print(f"Encontrados {len(result_files)} arquivos de resultado")

for path in result_files:
    try:
        with open(path, encoding="utf-8") as f:
            rows = json.load(f)
        for r in rows:
            qid = r["id"]
            area = r.get("area", "")
            subtema = r.get("subtema", "")
            if area not in VALID_AREAS:
                n_bad_area += 1
                bad_area_values.add(area)
                continue
            cur.execute("UPDATE questions SET area = ?, subtema = ? WHERE id = ?", (area, subtema, qid))
            n_updated += 1
            seen_ids.add(qid)
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"ERRO ao processar {path}: {e} (progresso deste arquivo descartado, anteriores já commitados)")

missing = total_ids - seen_ids
print(f"Atualizadas: {n_updated}")
print(f"Áreas inválidas encontradas: {n_bad_area} (valores: {bad_area_values})")
print(f"Questões sem classificação (não apareceram em nenhum result_*.json): {len(missing)}")
if missing:
    print("IDs faltantes (até 30):", sorted(missing)[:30])

# resumo por área
print("\n--- Distribuição por área ---")
for row in cur.execute("SELECT area, COUNT(*) FROM questions GROUP BY area ORDER BY 2 DESC"):
    print(row)

conn.close()
