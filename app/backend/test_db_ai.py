import os
import sys
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.DEBUG)

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
sys.path.insert(0, os.path.dirname(__file__))

from api.db import get_db
import sqlite3
from api.ai import ask_preceptor_ai

db = sqlite3.connect("medquest.db")
db.row_factory = sqlite3.Row

question_id = 5
q = db.execute("""
    SELECT q.id, q.stem, q.area, q.subtema, q.topic,
           e.explanation_text
    FROM questions q
    LEFT JOIN explanations e ON q.id = e.question_id
    WHERE q.id = ?
""", (question_id,)).fetchone()

alts = db.execute("""
    SELECT letter, text, is_correct
    FROM alternatives
    WHERE question_id = ?
    ORDER BY letter
""", (question_id,)).fetchall()

alts_list = [{"letter": a["letter"], "text": a["text"], "is_correct": bool(a["is_correct"])} for a in alts]
correct_alt = next((a for a in alts_list if a["is_correct"]), None)
correct_letter = correct_alt["letter"] if correct_alt else ""
correct_text = correct_alt["text"] if correct_alt else ""

try:
    res = ask_preceptor_ai(
        stem=q["stem"],
        alternatives=alts_list,
        correct_letter=correct_letter,
        correct_text=correct_text,
        user_letter="",
        user_question="O que é ritmo juncional?",
        explanation=q["explanation_text"] or "",
        area=q["area"] or "",
        subtema=q["subtema"] or q["topic"] or ""
    )
    import json
    print(json.dumps(res, ensure_ascii=False, indent=2))
except Exception as e:
    print("FAILED:", e)
