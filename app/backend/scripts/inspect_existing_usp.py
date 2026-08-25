import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "medquest.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
c = conn.cursor()

c.execute("""
    SELECT id, source_file, source_number, institution_code, institution_label, year, 
           substr(stem, 1, 80) as stem_preview, correct_letter
    FROM questions
    WHERE institution_code = 'USP-SP' AND year = 2026
    ORDER BY source_number, id
""")
rows = c.fetchall()

print(f"Total questoes USP-SP 2026 no banco: {len(rows)}")

source_files = set(r["source_file"] for r in rows)
print("Source files:", source_files)

# Check numbers and duplicates
by_num = {}
for r in rows:
    num = r["source_number"]
    by_num.setdefault(num, []).append(r)

print(f"Numeros distintos: {len(by_num)}")
duplicates = {num: qs for num, qs in by_num.items() if len(qs) > 1}
print(f"Numeros duplicados: {len(duplicates)}")
for num in sorted(duplicates.keys())[:10]:
    ids = [q['id'] for q in duplicates[num]]
    labels = [q['institution_label'] for q in duplicates[num]]
    print(f"  Questao {num}: IDs {ids} | Labels: {labels}")

# Check if any user attempts or favorites exist for these question IDs
all_usp_ids = [r["id"] for r in rows]
placeholders = ",".join("?" * len(all_usp_ids))

c.execute(f"SELECT COUNT(*) FROM attempts WHERE question_id IN ({placeholders})", all_usp_ids)
attempts_count = c.fetchone()[0]

c.execute(f"SELECT COUNT(*) FROM favorites WHERE question_id IN ({placeholders})", all_usp_ids)
favs_count = c.fetchone()[0]

c.execute(f"SELECT COUNT(*) FROM flashcards WHERE question_id IN ({placeholders})", all_usp_ids)
flashcards_count = c.fetchone()[0]

print(f"\nUso atual pelo usuario dessas questoes antigas USP-SP 2026:")
print(f"  Attempts: {attempts_count}")
print(f"  Favorites: {favs_count}")
print(f"  Flashcards: {flashcards_count}")

conn.close()
