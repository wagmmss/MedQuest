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

def audit_exam(inst_code, year):
    print("=" * 60)
    print(f" AUDITORIA DE INTEGRIDADE: {inst_code} {year}")
    print("=" * 60)

    # 1. Total questions
    c.execute("""
        SELECT count(*) as total,
               min(source_number) as min_num,
               max(source_number) as max_num,
               count(DISTINCT source_number) as unique_nums
        FROM questions
        WHERE institution_code = ? AND year = ? AND source_file = ?
    """, (inst_code, year, f"{inst_code} {year}"))
    stats = c.fetchone()
    print(f"Total de questões oficiais: {stats['total']}")
    print(f"Numeração: {stats['min_num']} até {stats['max_num']} (Únicos: {stats['unique_nums']})")

    # 2. Check for duplicate numbers
    c.execute("""
        SELECT source_number, count(*) as cnt 
        FROM questions 
        WHERE institution_code = ? AND year = ? AND source_file = ?
        GROUP BY source_number
        HAVING count(*) > 1
    """, (inst_code, year, f"{inst_code} {year}"))
    dups = c.fetchall()
    print(f"Duplicatas encontradas: {len(dups)}")

    # 3. Check alternatives completeness
    c.execute("""
        SELECT q.id, q.source_number, count(a.id) as alt_cnt, sum(a.is_correct) as correct_cnt
        FROM questions q
        LEFT JOIN alternatives a ON q.id = a.question_id
        WHERE q.institution_code = ? AND q.year = ? AND q.source_file = ?
        GROUP BY q.id
    """, (inst_code, year, f"{inst_code} {year}"))
    alt_stats = c.fetchall()
    invalid_alts = [r for r in alt_stats if r['alt_cnt'] < 4 or r['correct_cnt'] < 1]
    print(f"Questões com alternativas incompletas/sem gabarito: {len(invalid_alts)}")

    # 4. Check explanations completeness
    c.execute("""
        SELECT q.id, q.source_number, e.explanation_text
        FROM questions q
        LEFT JOIN explanations e ON q.id = e.question_id
        WHERE q.institution_code = ? AND q.year = ? AND q.source_file = ?
    """, (inst_code, year, f"{inst_code} {year}"))
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
        WHERE q.institution_code = ? AND q.year = ? AND q.source_file = ?
    """, (inst_code, year, f"{inst_code} {year}"))
    img_stats = c.fetchone()
    print(f"Questões com imagens vinculadas: {img_stats['q_with_imgs']} (Total de imagens: {img_stats['total_imgs']})")

    # 6. Sample question 1 display
    print("\n" + "-" * 60)
    print(f"AMOSTRA DA QUESTÃO 1 ({inst_code} {year}):")
    c.execute("""
        SELECT q.id, q.source_number, q.institution_code, q.year, q.topic, q.area, q.correct_letter, q.stem, e.explanation_text
        FROM questions q
        LEFT JOIN explanations e ON q.id = e.question_id
        WHERE q.institution_code = ? AND q.year = ? AND q.source_number = 1 AND q.source_file = ?
    """, (inst_code, year, f"{inst_code} {year}"))
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

audit_exam("UNICAMP", 2026)
conn.close()
