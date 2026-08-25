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
print(" AUDITORIA CONSOLIDADA: UNICAMP (2020 a 2026)")
print("=" * 80)

c.execute("""
    SELECT year, source_file, COUNT(*) as cnt,
           MIN(source_number) as min_num, MAX(source_number) as max_num,
           COUNT(DISTINCT source_number) as uniq_nums
    FROM questions
    WHERE institution_code = 'UNICAMP'
    GROUP BY year, source_file
    ORDER BY year DESC
""")
rows = c.fetchall()

print(f"{'ANO':<6} | {'COUNT':<6} | {'NUMS':<12} | {'SOURCE_FILE'}")
print("-" * 80)
for r in rows:
    nums_str = f"{r['min_num']}..{r['max_num']} ({r['uniq_nums']})"
    print(f"{r['year']:<6} | {r['cnt']:<6} | {nums_str:<12} | {r['source_file']}")

# Check total images and explanations
c.execute("""
    SELECT count(e.question_id) as total_exps,
           sum(CASE WHEN e.explanation_text LIKE '%Pulo do Gato%' THEN 1 ELSE 0 END) as golden_cnt
    FROM questions q
    JOIN explanations e ON q.id = e.question_id
    WHERE q.institution_code = 'UNICAMP'
""")
exp_stats = c.fetchone()
print("-" * 80)
print(f"Total de comentários UNICAMP: {exp_stats['total_exps']}")
print(f"Total no padrão Template Ouro: {exp_stats['golden_cnt']} / {exp_stats['total_exps']}")

c.execute("""
    SELECT count(DISTINCT q.id) as q_with_img, count(qi.id) as total_imgs
    FROM questions q
    JOIN question_images qi ON q.id = qi.question_id
    WHERE q.institution_code = 'UNICAMP'
""")
img_stats = c.fetchone()
print(f"Questões com imagens vinculadas: {img_stats['q_with_img']} (Total de imagens: {img_stats['total_imgs']})")

conn.close()
