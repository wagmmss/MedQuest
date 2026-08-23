import sqlite3
import json

with open("canonical_taxonomy_170.json", "r", encoding="utf-8") as f:
    canon = json.load(f)

conn = sqlite3.connect("app/backend/medquest.db")
c = conn.cursor()

c.execute("SELECT DISTINCT subtema FROM questions WHERE area = 'Clínica Médica'")
subtemas = [r[0] for r in c.fetchall()]

invalid = [s for s in subtemas if s not in canon["Clínica Médica"]]
print(f"Total subtemas distintos em Clínica Médica: {len(subtemas)}")
if invalid:
    print("SUBTEMAS INVÁLIDOS ENCONTRADOS:")
    for inv in invalid:
        print("-", inv)
else:
    print("TODOS os subtemas de Clínica Médica estão 100% em conformidade com a taxonomia canônica de 170 temas!")
