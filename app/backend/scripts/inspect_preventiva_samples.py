import sqlite3
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('app/backend/medquest.db')
conn.row_factory = sqlite3.Row

for qid in [8604, 8593, 8665, 8658, 8602, 8654]:
    r = conn.execute("""
        SELECT q.id, q.stem, q.topic, q.subtema_orig, q.area, q.subtema, e.explanation_text 
        FROM questions q 
        LEFT JOIN explanations e ON q.id = e.question_id 
        WHERE q.id = ?
    """, (qid,)).fetchone()
    print("=" * 60)
    print(f"ID: {r['id']} | TOPIC: '{r['topic']}' | SUBTEMA_ORIG: '{r['subtema_orig']}' | CURRENT SUB: '{r['subtema']}'")
    print(f"STEM: {r['stem']}")
    alts = conn.execute("SELECT letter, text, is_correct FROM alternatives WHERE question_id = ? ORDER BY letter", (qid,)).fetchall()
    for a in alts:
        print(f"  {a['letter']}) {a['text']}{' [CORRETA]' if a['is_correct'] else ''}")
    print(f"EXP: {r['explanation_text']}")
    print()
