import os
import re
import sqlite3

from canonical_subtemas import CANONICAL

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "medquest.db")

def parse_institution(topic, source_file):
    t = (topic + " " + source_file).upper()
    if "SÍRIO" in t or "SIRIO" in t or "HSL" in t:
        return "HSL", "Hospital Sírio-Libanês (HSL)"
    if "EINSTEIN" in t:
        return "EINSTEIN", "Hospital Israelita Albert Einstein"
    if "SANTA CASA" in t or "SCMSP" in t:
        return "SCMSP", "Santa Casa de Misericórdia de São Paulo (SCMSP)"
    if "UNICAMP" in t:
        return "UNICAMP", "UNICAMP - Hospital de Clínicas da Unicamp (FCM-Unicamp)"
    if "UNIFESP" in t:
        return "UNIFESP", "UNIFESP - Hospital Universitário da UNIFESP"
    if "USP" in t:
        if "RP" in t or "RIBEIRÃO" in t or "RIBEIRAO" in t:
            return "USP-RP", "USP - Hospital das Clínicas da Faculdade de Medicina de Ribeirão Preto (HCRP)"
        if "HRAC" in t or "BAURU" in t:
            return "HRAC-USP", "USP - Hospital de Reabilitação de Anomalias Craniofaciais (HRAC), Bauru"
        return "USP-SP", "USP - Hospital das Clínicas da Faculdade de Medicina da USP (HC-FMUSP)"
    return "OUTRO", "Instituição não identificada"

def parse_area(topic, source_file):
    t = (topic + " " + source_file).upper()
    if "CIRURGIA" in t: return "Cirurgia"
    if "PEDIATRIA" in t: return "Pediatria"
    if "GINECO" in t or "OBSTETR" in t: return "Ginecologia e Obstetrícia"
    if "PREVENTIVA" in t or "SOCIAL" in t or "EPIDEMIO" in t: return "Medicina Preventiva e Social"
    if "CLÍNICA" in t or "CLINICA" in t or "CLÍ" in t: return "Clínica Médica"
    
    # Fallbacks based on common terms in stem/topic
    if "TRAUMA" in t or "HÉRNIA" in t or "ABDOME AGUDO" in t: return "Cirurgia"
    if "CRIANÇA" in t or "NEONATAL" in t or "LACTENTE" in t: return "Pediatria"
    if "GESTA" in t or "PARTO" in t or "PUERPÉRIO" in t: return "Ginecologia e Obstetrícia"
    
    return "Cirurgia" # Fallback if totally unknown (rare)

def fuzzy_match_subtema(area, text):
    if not area or area not in CANONICAL:
        return None
    canon_list = CANONICAL[area]
    text_up = text.upper()
    
    best_match = None
    best_score = 0
    
    # Clean up words > 3 chars
    words_raw = re.findall(r'\b[a-zA-Záéíóúâêôãõç]{4,}\b', text_up)
    words = set(words_raw)
    
    for sub in canon_list:
        sub_words = set(re.findall(r'\b[a-zA-Záéíóúâêôãõç]{4,}\b', sub.upper()))
        if not sub_words: continue
        score = len(words.intersection(sub_words))
        if score > best_score:
            best_score = score
            best_match = sub
            
    if best_score > 0:
        return best_match
    return canon_list[0] # Generic fallback

def run():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    cur.execute("SELECT id, topic, stem, source_file, institution_code FROM questions WHERE area IS NULL OR institution_code = 'OUTRO'")
    rows = cur.fetchall()
    
    print(f"Encontradas {len(rows)} questões para processar.")
    
    updated = 0
    for row in rows:
        topic = row['topic'] or ""
        stem = row['stem'] or ""
        source_file = row['source_file'] or ""
        
        inst_code, inst_label = parse_institution(topic, source_file)
        area = parse_area(topic, source_file)
        
        text_to_match = topic + " " + stem[:400]
        subtema = fuzzy_match_subtema(area, text_to_match)
        
        cur.execute('''
            UPDATE questions 
            SET institution_code = ?, institution_label = ?, area = ?, subtema = ?, subtema_orig = ?
            WHERE id = ?
        ''', (inst_code, inst_label, area, subtema, subtema, row['id']))
        updated += 1
        
    conn.commit()
    conn.close()
    print(f"{updated} questões atualizadas com sucesso!")

if __name__ == "__main__":
    run()
