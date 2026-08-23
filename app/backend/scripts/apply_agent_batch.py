"""
Aplica classificações geradas por IA/Subagente diretamente no medquest.db.
"""

import json
import sqlite3
import sys
import unicodedata
import re
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# Carregar taxonomia oficial
TAX_PATH = Path("app/backend/data/taxonomy.json")
with open(TAX_PATH, "r", encoding="utf-8") as f:
    RAW_TAX = json.load(f)

CANONICAL_TAX = {}
for a in RAW_TAX:
    CANONICAL_TAX[a["area"]] = [m["theme"] for m in a["macroThemes"]]

VALID_AREAS = list(CANONICAL_TAX.keys())

def normalize_str(s: str) -> str:
    s = unicodedata.normalize("NFD", str(s or ""))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s).strip().lower()

def match_canonical_subtema(target_area: str, subtema_raw: str) -> str:
    if target_area not in CANONICAL_TAX:
        for valid_a in VALID_AREAS:
            if normalize_str(valid_a) == normalize_str(target_area):
                target_area = valid_a
                break
        else:
            return subtema_raw
    available = CANONICAL_TAX[target_area]
    if subtema_raw in available:
        return subtema_raw
    norm_target = normalize_str(subtema_raw)
    for s in available:
        if normalize_str(s) == norm_target:
            return s
    for s in available:
        if norm_target in normalize_str(s) or normalize_str(s) in norm_target:
            return s
    return available[0]

def apply_classifications(json_input: str, db_path="app/backend/medquest.db", model_name="antigravity/gemini-3.7"):
    data = json.loads(json_input)
    if isinstance(data, dict):
        data = data.get("results") or data.get("classifications") or []
    
    conn = sqlite3.connect(db_path, timeout=60.0)
    conn.row_factory = sqlite3.Row
    
    # Garantir tabela de auditoria
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reclassification_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            old_area TEXT,
            old_subtema TEXT,
            new_area TEXT NOT NULL,
            new_subtema TEXT NOT NULL,
            confidence REAL,
            rationale TEXT,
            model_used TEXT,
            applied INTEGER DEFAULT 0,
            classified_at TEXT NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_qid ON reclassification_audit(question_id)")
    
    now_iso = datetime.now(timezone.utc).isoformat()
    applied_count = 0
    
    with conn:
        for item in data:
            qid = item["id"]
            q = conn.execute("SELECT area, subtema FROM questions WHERE id = ?", (qid,)).fetchone()
            if not q:
                continue
            old_area = q["area"]
            old_subtema = q["subtema"]
            
            raw_area = item.get("target_area", old_area)
            target_area = raw_area if raw_area in VALID_AREAS else old_area
            raw_sub = item.get("target_subtema", old_subtema)
            target_subtema = match_canonical_subtema(target_area, raw_sub)
            confidence = float(item.get("confidence", 1.0))
            rationale = str(item.get("rationale", "")).strip()
            
            # Registrar auditoria
            conn.execute("""
                INSERT INTO reclassification_audit 
                (question_id, old_area, old_subtema, new_area, new_subtema, confidence, rationale, model_used, applied, classified_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
            """, (qid, old_area, old_subtema, target_area, target_subtema, confidence, rationale, model_name, now_iso))
            
            # Atualizar questão
            conn.execute("""
                UPDATE questions 
                SET area = ?, 
                    subtema = ?,
                    subtema_orig = CASE WHEN subtema_orig IS NULL OR subtema_orig = '' THEN subtema ELSE subtema_orig END
                WHERE id = ?
            """, (target_area, target_subtema, qid))
            
            applied_count += 1
            
    print(f"Sucesso: {applied_count} questões atualizadas e auditadas no banco.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].endswith(".json"):
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            apply_classifications(f.read())
    else:
        # Lê do stdin
        apply_classifications(sys.stdin.read())
