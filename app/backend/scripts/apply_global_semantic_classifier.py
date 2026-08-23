import sqlite3
from test_global_classifier import classify_question

conn = sqlite3.connect("app/backend/medquest.db")
conn.row_factory = sqlite3.Row

questions = conn.execute("SELECT id, area, subtema, topic, stem FROM questions").fetchall()
print(f"Applying semantic classification to all {len(questions)} questions in medquest.db...")

updates = []
for q in questions:
    target_area, target_sub = classify_question(q)
    updates.append((target_area, target_sub, q["id"]))

conn.executemany("UPDATE questions SET area = ?, subtema = ? WHERE id = ?", updates)
conn.commit()

print(f"Successfully updated all {len(updates)} questions in medquest.db!")

# Verify no nulls remain
null_count = conn.execute("SELECT COUNT(*) FROM questions WHERE area IS NULL OR subtema IS NULL").fetchone()[0]
print(f"Remaining null questions: {null_count}")
