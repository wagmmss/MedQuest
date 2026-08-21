import sqlite3
from typing import Dict, List
from .connection import rows

def check_integrity(db: sqlite3.Connection) -> dict:
    all_questions = rows(db, "SELECT id, missing_alts, stem, source_file, source_number, correct_letter FROM questions")
    all_alts = rows(db, "SELECT id, question_id, letter, text, is_correct FROM alternatives")
    
    q_dict = {q["id"]: q for q in all_questions}
    alts_by_q = {}
    
    empty_alternatives = []
    orphan_alternatives = []
    
    for a in all_alts:
        qid = a["question_id"]
        if qid not in q_dict:
            orphan_alternatives.append(a["id"])
            continue
            
        if not a["text"] or not a["text"].strip():
            empty_alternatives.append({"alt_id": a["id"], "question_id": qid})
            
        if qid not in alts_by_q: alts_by_q[qid] = []
        alts_by_q[qid].append(a)
        
    empty_statement = []
    invalid_correct_letter = []
    answer_without_alt = []
    dup_letters = []
    missing_alts_0_incomplete = []
    missing_alts_1_complete = []
    
    for q in all_questions:
        qid = q["id"]
        if not q["stem"] or not q["stem"].strip():
            empty_statement.append(qid)
            
        alts = alts_by_q.get(qid, [])
        letters = [a["letter"] for a in alts]
        correct_letter = q.get("correct_letter")
        
        if not correct_letter or not str(correct_letter).strip():
            invalid_correct_letter.append({"question_id": qid, "reason": "Correct letter is null or empty"})
        elif correct_letter not in letters:
            answer_without_alt.append({"question_id": qid, "correct_letter": correct_letter, "available": letters})
            
        if len(letters) != len(set(letters)):
            dup_letters.append(qid)
            
        if q["missing_alts"] == 0:
            if len(alts) < 2 or not correct_letter or correct_letter not in letters:
                missing_alts_0_incomplete.append(qid)
        elif q["missing_alts"] == 1:
            if len(alts) >= 4 and correct_letter and correct_letter in letters:
                missing_alts_1_complete.append(qid)
                
    # Source dups
    sources = {}
    dup_sources = []
    for q in all_questions:
        sf = q["source_file"]
        sn = q["source_number"]
        if sf and sn:
            k = f"{sf}::{sn}"
            if k not in sources: sources[k] = []
            sources[k].append(q["id"])
            
    for k, ids in sources.items():
        if len(ids) > 1:
            dup_sources.append({"source": k, "question_ids": sorted(ids)})

    orphan_images = [r["id"] for r in rows(db, "SELECT id FROM question_images WHERE question_id NOT IN (SELECT id FROM questions) ORDER BY id")]
    
    return {
        "critical_failures": {
            "empty_statement": sorted(empty_statement),
            "empty_alternative": sorted(empty_alternatives, key=lambda x: x["alt_id"]),
            "invalid_correct_letter": sorted(invalid_correct_letter, key=lambda x: x["question_id"]),
            "answer_without_alternative": sorted(answer_without_alt, key=lambda x: x["question_id"]),
            "duplicated_letters": sorted(dup_letters),
            "orphan_records": {
                "alternatives": sorted(orphan_alternatives),
                "images": sorted(orphan_images)
            },
            "missing_alts_0_incomplete": sorted(missing_alts_0_incomplete),
            "duplicate_source_file_number": sorted(dup_sources, key=lambda x: x["source"])
        },
        "warnings": {
            "missing_alts_1_complete": sorted(missing_alts_1_complete)
        }
    }
