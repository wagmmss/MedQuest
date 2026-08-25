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

print("=" * 60)
print(" AUDITORIA DE INTEGRIDADE: USP-SP 2026")
print("=" * 60)

# 1. Total questions
c.execute("""
    SELECT count(*) as total,
           min(source_number) as min_num,
           max(source_number) as max_num,
           count(DISTINCT source_number) as unique_nums
    FROM questions
    WHERE institution_code = 'USP-SP' AND year = 2026
""")
stats = c.fetchone()
print(f"Total de questões: {stats['total']}")
print(f"Numeração: {stats['min_num']} até {stats['max_num']} (Únicos: {stats['unique_nums']})")

# 2. Check for duplicate numbers
c.execute("""
    SELECT source_number, count(*) as cnt 
    FROM questions 
    WHERE institution_code = 'USP-SP' AND year = 2026
    GROUP BY source_number
    HAVING count(*) > 1
""")
dups = c.fetchall()
print(f"Duplicatas encontradas: {len(dups)}")

# 3. Check alternatives completeness
c.execute("""
    SELECT q.id, q.source_number, count(a.id) as alt_cnt, sum(a.is_correct) as correct_cnt
    FROM questions q
    LEFT JOIN alternatives a ON q.id = a.question_id
    WHERE q.institution_code = 'USP-SP' AND q.year = 2026
    GROUP BY q.id
""")
alt_stats = c.fetchall()
invalid_alts = [r for r in alt_stats if r['alt_cnt'] < 4 or r['correct_cnt'] < 1]
print(f"Questões com alternativas incompletas/sem gabarito: {len(invalid_alts)}")

# 4. Check explanations completeness
c.execute("""
    SELECT q.id, q.source_number, e.explanation_text
    FROM questions q
    LEFT JOIN explanations e ON q.id = e.question_id
    WHERE q.institution_code = 'USP-SP' AND q.year = 2026
""")
exp_stats = c.fetchall()
missing_exp = [r for r in exp_stats if not r['explanation_text'] or len(r['explanation_text'].strip()) < 50]
golden_exp = [r for r in exp_stats if r['explanation_text'] and 'Pulo do Gato' in r['explanation_text']]
print(f"Questões sem explicação: {len(missing_exp)}")
print(f"Questões no padrão Template Ouro: {len(golden_exp)} / {len(exp_stats)}")

# 5. Check images
c.execute("""
    SELECT count(DISTINCT question_id) as q_with_imgs, count(*) as total_imgs
    FROM question_images qi
    JOIN questions q ON qi.question_id = q.id
    WHERE q.institution_code = 'USP-SP' AND q.year = 2026
""")
img_stats = c.fetchone()
print(f"Questões com imagens vinculadas: {img_stats['q_with_imgs']} (Total de imagens: {img_stats['total_imgs']})")

# 6. Sample question 1 display
print("\n" + "-" * 60)
print("AMOSTRA DA QUESTÃO 1:")
c.execute("""
    SELECT q.id, q.source_number, q.institution_code, q.year, q.topic, q.area, q.correct_letter, q.stem, e.explanation_text
    FROM questions q
    LEFT JOIN explanations e ON q.id = e.question_id
    WHERE q.institution_code = 'USP-SP' AND q.year = 2026 AND q.source_number = 1
""")
q1 = c.fetchone()
if q1:
    print(f"ID: {q1['id']} | Número: {q1['source_number']} | Área: {q1['area']} | Tema: {q1['topic']}")
    print(f"Gabarito: {q1['correct_letter']}")
    print(f"Enunciado: {q1['stem'][:150]}...")
    print("\nAlternativas:")
    c.execute("SELECT letter, text, is_correct FROM alternatives WHERE question_id = ? ORDER BY letter", (q1['id'],))
    for a in c.fetchall():
        mark = "[CORRETA]" if a['is_correct'] else ""
        print(f"  ({a['letter']}) {a['text']} {mark}")
    print(f"\nExplicação (Preview 300 chars):\n{q1['explanation_text'][:300]}...")

# 7. Sample question 63 display (Dual Gabarito)
print("\n" + "-" * 60)
print("AMOSTRA DA QUESTÃO 63 (GABARITO DUPLO B e C):")
c.execute("""
    SELECT q.id, q.source_number, q.institution_code, q.year, q.topic, q.area, q.correct_letter, q.stem, e.explanation_text
    FROM questions q
    LEFT JOIN explanations e ON q.id = e.question_id
    WHERE q.institution_code = 'USP-SP' AND q.year = 2026 AND q.source_number = 63
""")
q63 = c.fetchone()
if q63:
    print(f"ID: {q63['id']} | Número: {q63['source_number']} | Área: {q63['area']} | Tema: {q63['topic']}")
    print(f"Gabarito: {q63['correct_letter']}")
    c.execute("SELECT letter, text, is_correct FROM alternatives WHERE question_id = ? ORDER BY letter", (q63['id'],))
    for a in c.fetchall():
        mark = "[CORRETA]" if a['is_correct'] else ""
        print(f"  ({a['letter']}) {a['text']} {mark}")

conn.close()
