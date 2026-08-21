import json
import sqlite3


def test_batch():
    ids = [1, 2, 3] # some sample IDs
    db = sqlite3.connect('medquest.db')
    db.row_factory = sqlite3.Row
    CHUNK = 500
    q_map = {}
    alt_map = {}
    img_map = {}
    attempt_map = {}
    wrong_map = {}
    fav_set = set()
    user_id = 1
    force_4_options = True

    for i in range(0, len(ids), CHUNK):
        chunk = ids[i:i + CHUNK]
        ph = ",".join("?" * len(chunk))

        for r in db.execute(f"SELECT * FROM questions WHERE id IN ({ph})", chunk).fetchall():
            q_map[r["id"]] = dict(r)

        for r in db.execute(f"SELECT question_id, letter, text FROM alternatives WHERE question_id IN ({ph}) ORDER BY letter", chunk).fetchall():
            alt_map.setdefault(r["question_id"], []).append({"letter": r["letter"], "text": r["text"]})

        for r in db.execute(f"SELECT question_id, file_path FROM question_images WHERE question_id IN ({ph}) ORDER BY order_index", chunk).fetchall():
            img_map.setdefault(r["question_id"], []).append(r["file_path"])

        chunk_user = list(chunk) + [user_id]
        for r in db.execute(
            f"SELECT question_id, selected_letter, is_correct FROM attempts WHERE question_id IN ({ph}) AND user_id = ? ORDER BY id DESC",
            chunk_user,
        ).fetchall():
            if r["question_id"] not in attempt_map:
                attempt_map[r["question_id"]] = {"selected_letter": r["selected_letter"], "is_correct": bool(r["is_correct"])}

        for r in db.execute(
            f"SELECT question_id, COUNT(*) as n FROM attempts WHERE question_id IN ({ph}) AND is_correct = 0 AND user_id = ? GROUP BY question_id",
            chunk_user,
        ).fetchall():
            wrong_map[r["question_id"]] = r["n"]

        for r in db.execute(f"SELECT question_id FROM favorites WHERE question_id IN ({ph}) AND user_id = ?", chunk_user).fetchall():
            fav_set.add(r["question_id"])

    out = []
    import random
    for qid in ids:
        q = q_map.get(qid)
        if not q:
            continue
            
        alts = alt_map.get(qid, [])
        if force_4_options and len(alts) > 4:
            correct_letter = q.get("correct_letter")
            incorrects = [a for a in alts if a["letter"] != correct_letter]
            if incorrects:
                remove_count = len(alts) - 4
                to_remove = random.sample(incorrects, remove_count)
                to_remove_letters = {a["letter"] for a in to_remove}
                alts = [a for a in alts if a["letter"] not in to_remove_letters]

        out.append({
            "id": q["id"],
            "source_file": q["source_file"],
            "source_number": q["source_number"],
            "year": q["year"],
            "institution_code": q["institution_code"],
            "institution_label": q["institution_label"],
            "topic": q["topic"],
            "area": q["area"],
            "subtema": q["subtema"],
            "stem": q["stem"],
            "is_verified": bool(q.get("is_verified", 0)),
            "last_updated_at": q.get("last_updated_at"),
            "technical_note": q.get("technical_note"),
            "medical_references": q.get("medical_references"),
            "alternatives": alts,
            "images": img_map.get(qid, []),
            "already_answered": attempt_map.get(qid),
            "is_favorite": qid in fav_set,
            "times_wrong": wrong_map.get(qid, 0),
        })

    print(json.dumps({"questions": out}, indent=2)[:500])

test_batch()
