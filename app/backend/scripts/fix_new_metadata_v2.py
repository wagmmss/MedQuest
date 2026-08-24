import os
import re
import sqlite3

from canonical_subtemas import CANONICAL

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "medquest.db")

def parse_institution(topic, source_file, current_code=None, current_label=None):
    if current_code and current_code != 'OUTRO':
        return current_code, current_label
    t = topic.upper()
    if "SÍRIO" in t or "SIRIO" in t or "HSL" in t:
        return "HSL", "Hospital Sírio-Libanês (HSL)"
    if "EINSTEIN" in t:
        return "EINSTEIN", "Hospital Israelita Albert Einstein (HIAE)"
    if "SANTA CASA" in t or "SCMSP" in t:
        return "SCMSP", "Santa Casa de Misericórdia de São Paulo (SCMSP)"
    if "UNICAMP" in t:
        return "UNICAMP", "UNICAMP - Hospital de Clínicas da Unicamp (FCM-Unicamp)"
    if "UNIFESP" in t:
        return "UNIFESP", "UNIFESP - Hospital Universitário da UNIFESP"
    if "SUS" in t:
        return "SUS-SP", "SUS-SP - Seleção Unificada para Residência Médica do Estado de São Paulo"
    if "USP" in t:
        if "RP" in t or "RIBEIRÃO" in t or "RIBEIRAO" in t:
            return "USP-RP", "USP - Hospital das Clínicas da Faculdade de Medicina de Ribeirão Preto (HCRP)"
        if "HRAC" in t or "BAURU" in t:
            return "HRAC-USP", "USP - Hospital de Reabilitação de Anomalias Craniofaciais (HRAC), Bauru"
        return "USP-SP", "USP - Hospital das Clínicas da Faculdade de Medicina da USP (HC-FMUSP)"
    return current_code or "OUTRO", current_label or "Instituição não identificada"

def fuzzy_match_global(text):
    text_up = text.upper()
    
    best_area = "Clínica Médica"
    best_match = CANONICAL["Clínica Médica"][0]
    best_score = 0
    
    words_raw = re.findall(r'\b[a-zA-Záéíóúâêôãõç]{4,}\b', text_up)
    words = set(words_raw)
    
    for area, canon_list in CANONICAL.items():
        # Add area name to words to boost matches if area name is in text
        area_words = set(re.findall(r'\b[a-zA-Záéíóúâêôãõç]{4,}\b', area.upper()))
        
        for sub in canon_list:
            sub_words = set(re.findall(r'\b[a-zA-Záéíóúâêôãõç]{4,}\b', sub.upper()))
            if not sub_words: continue
            
            # Score is intersection of words. If area word is in text, boost score slightly
            score = len(words.intersection(sub_words))
            score += len(words.intersection(area_words)) * 0.5
            
            if score > best_score:
                best_score = score
                best_match = sub
                best_area = area
                
    return best_area, best_match

def run():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Target ONLY the new questions (we can identify them because their source_file is the new ones)
    cur.execute("""
        SELECT id, topic, stem, source_file 
        FROM questions 
        WHERE source_file IN (
            'SUS-SP.pdf', 
            'SÍRIO EINSTEIN E SCMSP 2020 A 2023', 
            'SÍRIO EINSTEIN E SCMSP 2024 A 2026', 
            'UNIFESP E UNICAMP 2020 A 2022', 
            'UNIFESP E UNICAMP 2023 A 2026', 
            'USP 2020 a 2023', 
            'USP 2024 a 2026'
        )
    """)
    rows = cur.fetchall()
    
    print(f"Encontradas {len(rows)} questões novas para reclassificar.")
    
    updated = 0
    for row in rows:
        topic = row['topic'] or ""
        stem = row['stem'] or ""
        source_file = row['source_file'] or ""
        
        inst_code, inst_label = parse_institution(topic, source_file)
        
        text_to_match = topic + " " + stem[:600]
        area, subtema = fuzzy_match_global(text_to_match)
        
        cur.execute('''
            UPDATE questions 
            SET institution_code = ?, institution_label = ?, area = ?, subtema = ?, subtema_orig = ?
            WHERE id = ?
        ''', (inst_code, inst_label, area, subtema, subtema, row['id']))
        updated += 1
        
    conn.commit()
    conn.close()
    print(f"{updated} questões reclassificadas com sucesso!")

if __name__ == "__main__":
    run()
