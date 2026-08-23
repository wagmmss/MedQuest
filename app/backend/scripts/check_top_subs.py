import sqlite3
import json

from test_global_classifier import classify_question

conn = sqlite3.connect("app/backend/medquest.db")
conn.row_factory = sqlite3.Row

questions = conn.execute("SELECT id, area, subtema, topic, stem FROM questions").fetchall()

by_area_subs = {}
for q in questions:
    a, s = classify_question(q)
    by_area_subs.setdefault(a, {})
    by_area_subs[a][s] = by_area_subs[a].get(s, 0) + 1

for area, subs in by_area_subs.items():
    print(f"\nArea: {area} ({len(subs)} populated subtemas, {sum(subs.values())} total questions):")
    for s, count in sorted(subs.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  - {s}: {count} questions")
