import sqlite3
import os
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "medquest.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("=" * 80)
print(" AUDITORIA CONSOLIDADA: UNIFESP (2020 a 2026)")
print("=" * 80)

c.execute("""
    SELECT year, source_file, editorial_status, COUNT(*) as cnt,
           MIN(source_number) as min_num, MAX(source_number) as max_num,
           COUNT(DISTINCT source_number) as uniq_nums
    FROM questions
    WHERE institution_code = 'UNIFESP'
    GROUP BY year, source_file, editorial_status
    ORDER BY year DESC, source_file
""")
rows = c.fetchall()

print(f"{'ANO':<6} | {'TIPO':<10} | {'COUNT':<6} | {'NUMS':<12} | {'SOURCE_FILE'}")
print("-" * 80)
for r in rows:
    ed = r['editorial_status'] or 'reviewed'
    nums_str = f"{r['min_num']}..{r['max_num']} ({r['uniq_nums']})"
    print(f"{r['year']:<6} | {ed:<10} | {r['cnt']:<6} | {nums_str:<12} | {r['source_file']}")

# Check total images and explanations
c.execute("""
    SELECT count(e.question_id) as total_exps,
           sum(CASE WHEN e.explanation_text LIKE '%Pulo do Gato%' THEN 1 ELSE 0 END) as golden_cnt
    FROM questions q
    JOIN explanations e ON q.id = e.question_id
    WHERE q.institution_code = 'UNIFESP' AND q.source_file LIKE 'UNIFESP 20%'
""")
exp_stats = c.fetchone()
print("-" * 80)
print(f"Total de comentários oficiais UNIFESP: {exp_stats['total_exps']}")
print(f"Total no padrão Template Ouro: {exp_stats['golden_cnt']} / {exp_stats['total_exps']}")

conn.close()
