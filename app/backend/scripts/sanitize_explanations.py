import os
import sqlite3
import re
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "medquest.db")

META_PATTERNS = [
    r"\s*A explicação é 100% verídica.*$",
    r"\s*A explicação é 100% verídica, baseada em diretrizes.*$",
    r"\s*A explicação é 100% verídica, conforme as melhores práticas.*$",
    r"\s*A explicação é 100% verídica e sustenta logicamente o gabarito oficial.*$",
    r"\s*Não há imprecisões médicas ou alucinações.*$",
    r"\s*A explicação acima é 100% verídica.*$",
    r"\s*Reflete com precisão a situação clínica apresentada.*$"
]

TYPO_REPLACEMENTS = [
    (r"\bthrombocitopenia\b", "trombocitopenia"),
    (r"\bThrombocitopenia\b", "Trombocitopenia"),
    (r"\bDIC\b", "CIVD"),
    (r"\bicterícia obstructiva\b", "icterícia obstrutiva"),
    (r"\bIcterícia obstructiva\b", "Icterícia obstrutiva"),
    (r"\besfinterotomia papiliana\b", "esfinterotomia papilar"),
    (r"\binserção do agulha\b", "inserção da agulha"),
    (r"\bcontra‑indicado\b", "contraindicado"),
    (r"\bcontra‑indicação\b", "contraindicação"),
    (r"\bpré‑operatório\b", "pré-operatório"),
    (r"\bpós‑operatório\b", "pós-operatório"),
    (r"\bpós‑operatória\b", "pós-operatória"),
    (r"\bpós‑operatórias\b", "pós-operatórias"),
    (r"\bErada ao sugerir\b", "Errada ao sugerir"),
]

HEADER_STANDARDIZATIONS = [
    (r"\*\*Pulo_do_Gato\*\*:", "**Pulo do Gato**:"),
    (r"\*\*PuloGato\*\*:", "**Pulo do Gato**:"),
    (r"\*\*O pulo do gato\*\*:", "**Pulo do Gato**:"),
    (r"Pulo do gato:", "**Pulo do Gato**:"),
    (r"Pulo do Gato:", "**Pulo do Gato**:"),
    (r"\*\*Resposta\*\*:", "**Gabarito**:"),
    (r"Gabarito:", "**Gabarito**:"),
    (r"\*\*Alternativa Correcta\b", "**Alternativa Correta"),
    (r"Alternativa Correta \(", "**Alternativa Correta** ("),
    (r"Alternativas Incorretas:", "**Alternativas Incorretas**:"),
]

def sanitize_text(text: str) -> str:
    if not text:
        return ""
    
    # 1. Fix literal \n escaping
    if "\\n" in text:
        text = text.replace("\\n", "\n")
        
    # 2. Fix corrupted placeholders or full instructions blocks
    if text.strip().lower() in ("user safety: safe", "safe") or "não contiene informações clínicas relevantes" in text.lower():
        return ""
        
    # Strip prompt instruction blocks at top if any
    text = re.sub(r"^(?:User Safety:[^\n]*\n+)?(?:INSTRUÇ[ÕO]ES:[^\n]*\n+(?:\d+\.[^\n]*\n+)*\n*)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^User Safety:\s*safe\s*", "", text, flags=re.IGNORECASE)
        
    # 3. Strip meta validation phrases
    for pat in META_PATTERNS:
        text = re.sub(pat, "", text, flags=re.IGNORECASE | re.MULTILINE)
        
    # 4. Standardize headers
    for pat, rep in HEADER_STANDARDIZATIONS:
        text = re.sub(pat, rep, text)
        
    # 5. Fix known typos & anglicisms
    for pat, rep in TYPO_REPLACEMENTS:
        text = re.sub(pat, rep, text)
        
    # 6. Clean up trailing/leading whitespace and duplicate empty lines
    text = re.sub(r"\n{3,}", "\n\n", text.strip())
    
    return text

def run_sanitization():
    print(f"Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT question_id, explanation_text FROM explanations WHERE explanation_text IS NOT NULL")
    rows = cursor.fetchall()
    
    print(f"Total explanations to process: {len(rows)}")
    
    updated_count = 0
    cleared_corrupted = 0
    
    for qid, original_text in rows:
        cleaned = sanitize_text(original_text)
        if cleaned != original_text:
            if not cleaned:
                cleared_corrupted += 1
                cursor.execute("UPDATE explanations SET explanation_text = NULL WHERE question_id = ?", (qid,))
            else:
                updated_count += 1
                cursor.execute("UPDATE explanations SET explanation_text = ? WHERE question_id = ?", (cleaned, qid))
                
    conn.commit()
    conn.close()
    
    print(f"\nSanitization Complete:")
    print(f"- Explanations sanitized and updated: {updated_count}")
    print(f"- Corrupted placeholders cleared for re-generation: {cleared_corrupted}")

if __name__ == "__main__":
    run_sanitization()
