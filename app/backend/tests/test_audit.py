import sqlite3
import pytest
import subprocess
import sys
import json
import os
from pathlib import Path

@pytest.fixture
def clean_db(tmp_path):
    db_path = tmp_path / "test.db"
    db = sqlite3.connect(db_path)
    db.executescript("""
        CREATE TABLE questions (
            id INTEGER PRIMARY KEY,
            missing_alts INTEGER DEFAULT 0,
            stem TEXT,
            correct_letter TEXT,
            area TEXT,
            subtema TEXT,
            institution_code TEXT,
            year INTEGER,
            source_file TEXT,
            source_number TEXT
        );
        CREATE TABLE alternatives (
            id INTEGER PRIMARY KEY,
            question_id INTEGER,
            letter TEXT,
            text TEXT,
            is_correct INTEGER DEFAULT 0
        );
        CREATE TABLE explanations (
            question_id INTEGER PRIMARY KEY,
            explanation_text TEXT
        );
        CREATE TABLE question_images (
            id INTEGER PRIMARY KEY,
            question_id INTEGER
        );
    """)
    # Add dummy data
    db.execute("INSERT INTO questions (id, missing_alts, stem, correct_letter, area, subtema, institution_code, year) VALUES (1, 0, 'Stem 1', 'A', 'Cardio', 'ECG', 'USP', 2023)")
    db.execute("INSERT INTO alternatives (id, question_id, letter, text, is_correct) VALUES (1, 1, 'A', 'Alt A', 1)")
    db.execute("INSERT INTO alternatives (id, question_id, letter, text, is_correct) VALUES (2, 1, 'B', 'Alt B', 0)")
    db.execute("INSERT INTO explanations (question_id, explanation_text) VALUES (1, 'This is a valid explanation mentioning alternative A')")
    db.commit()
    db.close()
    return db_path

def test_connection_readonly(clean_db):
    from scripts.audit.connection import get_readonly_connection
    db, _ = get_readonly_connection(str(clean_db))
    
    # 2. PRAGMA query_only is active / 3. INSERT rejected / 4. UPDATE rejected
    with pytest.raises(sqlite3.OperationalError):
        db.execute("INSERT INTO questions (id, stem) VALUES (999, 'Test')")
    with pytest.raises(sqlite3.OperationalError):
        db.execute("UPDATE questions SET stem = 'Test2' WHERE id = 1")
        
    db.close()

def test_connection_not_found():
    from scripts.audit.connection import get_readonly_connection
    with pytest.raises(FileNotFoundError):
        get_readonly_connection("does_not_exist.db")

def test_integrity_critical_failures(clean_db):
    db = sqlite3.connect(clean_db)
    # Empty statement (2)
    db.execute("INSERT INTO questions (id, stem) VALUES (2, '   ')")
    # Empty alternative (3)
    db.execute("INSERT INTO questions (id, stem, missing_alts) VALUES (3, 'Valid', 0)")
    db.execute("INSERT INTO alternatives (question_id, letter, text, is_correct) VALUES (3, 'A', '  ', 1)")
    # NULL correct letter (4)
    db.execute("INSERT INTO questions (id, stem, missing_alts, correct_letter) VALUES (4, 'Valid', 0, NULL)")
    db.execute("INSERT INTO alternatives (question_id, letter, text, is_correct) VALUES (4, 'A', 'Valid alt', 1)")
    # Duplicate letters (5)
    db.execute("INSERT INTO questions (id, stem, missing_alts, correct_letter) VALUES (5, 'Valid', 0, 'A')")
    db.execute("INSERT INTO alternatives (question_id, letter, text, is_correct) VALUES (5, 'A', 'Alt 1', 1)")
    db.execute("INSERT INTO alternatives (question_id, letter, text, is_correct) VALUES (5, 'A', 'Alt 2', 0)")
    # Answer without alt (6)
    db.execute("INSERT INTO questions (id, stem, missing_alts, correct_letter) VALUES (6, 'Valid', 0, 'Y')")
    db.execute("INSERT INTO alternatives (question_id, letter, text, is_correct) VALUES (6, 'A', 'Alt', 0)")
    db.execute("INSERT INTO alternatives (question_id, letter, text, is_correct) VALUES (6, 'Z', 'Alt 2', 1)") 
    # Orphan
    db.execute("INSERT INTO alternatives (id, question_id, text) VALUES (99, 999, 'Orphan')")
    # Missing alts 0 incomplete
    db.execute("INSERT INTO questions (id, stem, missing_alts) VALUES (7, 'Valid', 0)")
    db.execute("INSERT INTO alternatives (question_id, letter, text, is_correct) VALUES (7, 'A', 'Alt 1', 0)")
    
    db.commit()
    db.close()
    
    from scripts.audit.connection import get_readonly_connection
    from scripts.audit.integrity import check_integrity
    ro_db, _ = get_readonly_connection(str(clean_db))
    res = check_integrity(ro_db)
    cf = res["critical_failures"]
    assert 2 in cf["empty_statement"]
    assert any(a["question_id"] == 3 for a in cf["empty_alternative"])
    assert any(a["question_id"] == 4 for a in cf["invalid_correct_letter"])
    assert 5 in cf["duplicated_letters"]
    assert any(a["question_id"] == 6 for a in cf["answer_without_alternative"])
    assert 99 in cf["orphan_records"]["alternatives"]
    assert 7 in cf["missing_alts_0_incomplete"]
    
def test_explanations_queue(clean_db):
    db = sqlite3.connect(clean_db)
    # High priority: Placeholder
    db.execute("INSERT INTO questions (id, stem, missing_alts) VALUES (2, 'Q', 0)")
    db.execute("INSERT INTO explanations (question_id, explanation_text) VALUES (2, 'This is a TODO item')")
    # Legitimate "erro" (should not be high)
    db.execute("INSERT INTO questions (id, stem, missing_alts) VALUES (3, 'Q', 0)")
    db.execute("INSERT INTO explanations (question_id, explanation_text) VALUES (3, 'O erro padrão é baixo. Letra A.')")
    # Medium: short
    db.execute("INSERT INTO questions (id, stem, missing_alts) VALUES (4, 'Q', 0)")
    db.execute("INSERT INTO explanations (question_id, explanation_text) VALUES (4, 'Short exp')")
    db.commit()
    db.close()
    
    from scripts.audit.connection import get_readonly_connection
    from scripts.audit.explanations import check_explanations
    ro_db, _ = get_readonly_connection(str(clean_db))
    # It safely runs without generated_at and reviewed_at
    res = check_explanations(ro_db)
    queue = res["human_review_queue"]
    
    assert any(q["question_id"] == 2 for q in queue["high_priority"])
    assert not any(q["question_id"] == 3 for q in queue["high_priority"])
    assert any(q["question_id"] == 4 for q in queue["medium_priority"])

def test_duplication_categories(clean_db):
    db = sqlite3.connect(clean_db)
    db.execute("INSERT INTO questions (id, stem, institution_code, year) VALUES (2, 'Duplicate stem', 'USP', 2023)")
    db.execute("INSERT INTO questions (id, stem, institution_code, year) VALUES (3, 'Duplicate stem', 'USP', 2023)") # Same inst/year
    
    db.execute("INSERT INTO questions (id, stem, institution_code, year) VALUES (4, 'Duplicate stem 2', 'USP', 2023)")
    db.execute("INSERT INTO questions (id, stem, institution_code, year) VALUES (5, 'Duplicate stem 2', 'USP', 2024)") # Same inst, diff year
    
    db.execute("INSERT INTO questions (id, stem, institution_code, year) VALUES (6, 'Duplicate stem 3', 'USP', 2023)")
    db.execute("INSERT INTO questions (id, stem, institution_code, year) VALUES (7, 'Duplicate stem 3', 'UFRJ', 2023)") # Cross inst
    
    db.execute("INSERT INTO questions (id, stem, institution_code, year) VALUES (8, 'Normalized?', 'USP', 2023)")
    db.execute("INSERT INTO questions (id, stem, institution_code, year) VALUES (9, 'Normalized!', 'USP', 2023)") # Normalized exact
    
    db.commit()
    db.close()
    
    from scripts.audit.connection import get_readonly_connection
    from scripts.audit.duplication import check_duplication
    ro_db, _ = get_readonly_connection(str(clean_db))
    res = check_duplication(ro_db)
    
    assert res["literal_exact"]["same_institution_year"][0]["count"] == 2
    assert res["literal_exact"]["same_institution_different_year"][0]["count"] == 2
    assert res["literal_exact"]["cross_institution"][0]["count"] == 2
    assert res["normalized_exact"]["same_institution_year"][0]["count"] == 2

def test_encoding(clean_db):
    db = sqlite3.connect(clean_db)
    db.execute("INSERT INTO questions (id, stem, area, subtema) VALUES (2, 'Bad \ufffd', 'Bad\u00a0Area', 'OK')")
    db.execute("INSERT INTO questions (id, stem, area, subtema) VALUES (3, 'Mojibake Ã£', 'OK', 'OK')")
    db.commit()
    db.close()
    
    from scripts.audit.connection import get_readonly_connection
    from scripts.audit.encoding import check_encoding
    ro_db, _ = get_readonly_connection(str(clean_db))
    res = check_encoding(ro_db)
    
    assert any(x["id"] == 2 for x in res["replacement_character_u_fffd"])
    assert any(x["id"] == 2 and x["field"] == 'area' for x in res["non_breaking_space"])
    assert any(x["id"] == 3 for x in res["probable_mojibake"])

def test_strict_mode(clean_db):
    # Base is clean in clean_db
    script = Path(__file__).parent.parent / "scripts" / "validate.py"
    res = subprocess.run([sys.executable, str(script), "--db", str(clean_db), "--strict"])
    assert res.returncode == 0
    
    # Break base
    db = sqlite3.connect(clean_db)
    db.execute("INSERT INTO questions (id, stem) VALUES (99, '   ')")
    db.commit()
    db.close()
    
    res2 = subprocess.run([sys.executable, str(script), "--db", str(clean_db), "--strict"])
    assert res2.returncode == 1

def test_determinism(clean_db, tmp_path):
    # Add varying data
    db = sqlite3.connect(clean_db)
    for i in range(2, 20):
        db.execute(f"INSERT INTO questions (id, stem, area, subtema) VALUES ({i}, 'Q {i}', 'A1', 'S1')")
    db.commit()
    db.close()
    
    script = Path(__file__).parent.parent / "scripts" / "validate.py"
    
    out1 = tmp_path / "out1.json"
    subprocess.run([sys.executable, str(script), "--db", str(clean_db), "--output", str(out1)])
    
    out2 = tmp_path / "out2.json"
    subprocess.run([sys.executable, str(script), "--db", str(clean_db), "--output", str(out2)])
    
    with open(out1, encoding='utf-8') as f: d1 = json.load(f)
    with open(out2, encoding='utf-8') as f: d2 = json.load(f)
        
    del d1["generated_at"]
    del d2["generated_at"]
    del d1["database"]["path"]
    del d2["database"]["path"]
    
    assert d1 == d2
