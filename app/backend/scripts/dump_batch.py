"""
Exporta lotes de questões não auditadas em JSON com contexto clínico completo.
Uso:
  python dump_batch.py --area "Ginecologia e Obstetrícia" --limit 50 --offset 0
"""

import argparse
import json
import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="app/backend/medquest.db")
    parser.add_argument("--area", default=None)
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row

    query = """
        SELECT q.id, q.stem, q.topic, q.subtema_orig, q.area, q.subtema, e.explanation_text
        FROM questions q
        LEFT JOIN explanations e ON q.id = e.question_id
        WHERE q.id NOT IN (SELECT question_id FROM reclassification_audit)
    """
    params = []
    if args.area:
        query += " AND q.area = ?"
        params.append(args.area)
    query += " ORDER BY q.id LIMIT ? OFFSET ?"
    params.extend([args.limit, args.offset])

    rows = conn.execute(query, params).fetchall()
    data = []
    for r in rows:
        qid = r["id"]
        alts = conn.execute("SELECT letter, text, is_correct FROM alternatives WHERE question_id = ? ORDER BY letter", (qid,)).fetchall()
        alts_formatted = "\n".join([f"  {a['letter']}) {a['text']}" + (" [GABARITO]" if a['is_correct'] else "") for a in alts])
        data.append({
            "id": qid,
            "current_area": r["area"],
            "current_subtema": r["subtema"],
            "topic": r["topic"] or "",
            "stem": r["stem"],
            "alternatives": alts_formatted,
            "explanation": (r["explanation_text"] or "")[:400]
        })

    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(json_str)
        print(f"Exportadas {len(data)} questões para {args.out}")
    else:
        print(json_str)

if __name__ == "__main__":
    main()
