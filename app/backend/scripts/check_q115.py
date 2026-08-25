import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "medquest.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
c = conn.cursor()

c.execute("""
    SELECT q.id, q.source_number, q.correct_letter, q.stem, e.explanation_text
    FROM questions q
    JOIN explanations e ON q.id = e.question_id
    WHERE q.institution_code = 'USP-SP' AND q.year = 2021 AND q.source_number = 115
""")
r = c.fetchone()
print(f"Questao 115: Gabarito={r['correct_letter']}")
print(f"Enunciado: {r['stem'][:120]}...")
print(f"Explicacao:\n{r['explanation_text'][:300]}")
conn.close()
