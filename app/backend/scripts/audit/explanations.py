import sqlite3
import re
from .connection import rows

def check_explanations(db: sqlite3.Connection, short_limit: int = 50) -> dict:
    cols = [r[1] for r in db.execute("PRAGMA table_info(explanations)").fetchall()]
    has_generated = "generated_at" in cols
    has_reviewed = "reviewed_at" in cols
    
    query = """
        SELECT q.id as qid, e.explanation_text
        FROM questions q
        LEFT JOIN explanations e ON e.question_id = q.id
        WHERE q.missing_alts = 0
        ORDER BY q.id
    """
    data = rows(db, query)
    
    # Mutually exclusive queue
    queue = {}
    
    def add_to_queue(qid, priority, reason):
        if qid not in queue:
            queue[qid] = {"priority": priority, "reasons": [reason]}
        else:
            curr_pri = queue[qid]["priority"]
            if priority == "high" and curr_pri != "high":
                queue[qid]["priority"] = "high"
            elif priority == "medium" and curr_pri == "low":
                queue[qid]["priority"] = "medium"
            queue[qid]["reasons"].append(reason)
            
    # Placeholders unequivocal
    placeholder_pattern = re.compile(r'\b(todo|fixme|placeholder)\b', re.IGNORECASE)
    
    for row in data:
        qid = row["qid"]
        text = row["explanation_text"]
        
        if text is None or not str(text).strip():
            add_to_queue(qid, "high", "Explanation is empty or null")
            continue
            
        text_str = str(text).strip()
        
        if placeholder_pattern.search(text_str):
            add_to_queue(qid, "high", "Contains explicit placeholder (TODO/FIXME/PLACEHOLDER)")
            
        if len(text_str) < short_limit:
            add_to_queue(qid, "medium", f"Too short (< {short_limit} chars)")
            
        # Heuristic: does it mention alternative or letter?
        if not re.search(r'\b(alternativa|letra|opção|correta|resposta)\b', text_str, re.IGNORECASE):
            add_to_queue(qid, "low", "Does not mention alternative/letter (Heuristic)")
            
    # Format queue for output
    high = []
    medium = []
    low = []
    
    for qid, info in sorted(queue.items()):
        item = {"question_id": qid, "reasons": sorted(info["reasons"])}
        if info["priority"] == "high": high.append(item)
        elif info["priority"] == "medium": medium.append(item)
        else: low.append(item)
        
    return {
        "human_review_queue": {
            "high_priority": high,
            "medium_priority": medium,
            "low_priority": low
        }
    }
