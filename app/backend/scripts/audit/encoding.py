import sqlite3
import re
from .connection import rows

def check_encoding(db: sqlite3.Connection) -> dict:
    # Patterns
    fffd_pattern = re.compile(r'\ufffd')
    # Mojibake heuristics (e.g. Ã£, Ã©, etc)
    mojibake_pattern = re.compile(r'Ã[§|£|¡|©|³|µ|§|º|ª]')
    nbsp_pattern = re.compile(r'\u00a0')
    zero_width_pattern = re.compile(r'[\u200b\u200c\u200d\uFEFF]')
    control_pattern = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')
    
    questions = rows(db, "SELECT id, stem, area, subtema FROM questions")
    alternatives = rows(db, "SELECT id, question_id, text FROM alternatives")
    explanations = rows(db, "SELECT question_id, explanation_text FROM explanations")
    
    cats = {
        "replacement_character_u_fffd": [],
        "probable_mojibake": [],
        "non_breaking_space": [],
        "zero_width_character": [],
        "control_character": []
    }
    
    def _scan(text, source_id, field_name):
        if not text: return
        t = str(text)
        
        if fffd_pattern.search(t):
            cats["replacement_character_u_fffd"].append({"id": source_id, "field": field_name, "match": "U+FFFD"})
        
        m_mojibake = mojibake_pattern.search(t)
        if m_mojibake:
            cats["probable_mojibake"].append({"id": source_id, "field": field_name, "match": m_mojibake.group(0)})
            
        if nbsp_pattern.search(t):
            cats["non_breaking_space"].append({"id": source_id, "field": field_name, "match": "NBSP"})
            
        m_zw = zero_width_pattern.search(t)
        if m_zw:
            cats["zero_width_character"].append({"id": source_id, "field": field_name, "match": "ZW"})
            
        m_ctrl = control_pattern.search(t)
        if m_ctrl:
            cats["control_character"].append({"id": source_id, "field": field_name, "match": "CTRL"})

    for q in questions:
        _scan(q["stem"], q["id"], "stem")
        _scan(q["area"], q["id"], "area")
        _scan(q["subtema"], q["id"], "subtema")
        
    for a in alternatives:
        _scan(a["text"], a["question_id"], f"alternative_{a['id']}")
        
    for e in explanations:
        _scan(e["explanation_text"], e["question_id"], "explanation")
        
    return {
        "note": "These characters are physically stored in the SQLite database, independent of terminal rendering.",
        "replacement_character_u_fffd": sorted(cats["replacement_character_u_fffd"], key=lambda x: (x["id"], x["field"])),
        "probable_mojibake": sorted(cats["probable_mojibake"], key=lambda x: (x["id"], x["field"])),
        "non_breaking_space": sorted(cats["non_breaking_space"], key=lambda x: (x["id"], x["field"])),
        "zero_width_character": sorted(cats["zero_width_character"], key=lambda x: (x["id"], x["field"])),
        "control_character": sorted(cats["control_character"], key=lambda x: (x["id"], x["field"]))
    }
