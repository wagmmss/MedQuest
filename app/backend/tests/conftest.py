"""Fixtures de teste: cada teste recebe um banco SQLite temporário próprio (isolado)."""
import os
import sqlite3

import pytest

from api import create_app

# Estes arquivos são diagnósticos manuais que acessam banco/serviços reais no
# momento da importação. Eles permanecem úteis para manutenção, mas não fazem
# parte da suíte hermética executada pelo pytest.
collect_ignore = [
    "test.py",
    "test_ai.py",
    "test_api_root.py",
    "test_db.py",
    "test_expand.py",
    "test_flashcards.py",
    "test_meta.py",
    "test_raw_turso.py",
    "test_turso.py",
    "test_turso2.py",
    "test_turso3.py",
]

SCHEMA_AND_SEED = """
CREATE TABLE questions(
    id INTEGER PRIMARY KEY, source_file TEXT, source_number INTEGER, year INTEGER,
    institution_code TEXT, institution_label TEXT, topic TEXT, stem TEXT,
    correct_letter TEXT, missing_alts INTEGER DEFAULT 0, area TEXT, subtema TEXT,
    editorial_status TEXT, status TEXT DEFAULT 'active');
CREATE TABLE alternatives(id INTEGER PRIMARY KEY, question_id INTEGER, letter TEXT,
    text TEXT, is_correct INTEGER);
CREATE TABLE explanations(question_id INTEGER PRIMARY KEY, explanation_text TEXT, generated_at TEXT);
CREATE TABLE question_images(id INTEGER PRIMARY KEY, question_id INTEGER, file_path TEXT, order_index INTEGER);
CREATE TABLE attempts(id INTEGER PRIMARY KEY, question_id INTEGER, selected_letter TEXT,
    is_correct INTEGER, answered_at TEXT, confidence TEXT, user_id INTEGER DEFAULT 1, time_spent_ms INTEGER);
INSERT INTO questions(id,area,subtema,stem,correct_letter,missing_alts,year,institution_code,institution_label)
  VALUES (1,'Clínica Médica','Hipertensão Arterial Sistêmica','Q1?','B',0,2025,'USP-SP','USP'),
         (2,'Pediatria','Imunização (PNI)','Q2?','A',0,2025,'USP-RP','USP RP'),
         (3,'Pediatria','Vitaminas','Q3 Discursiva?','A',0,2021,'UNICAMP','UNICAMP');
INSERT INTO alternatives(question_id,letter,text,is_correct) VALUES
  (1,'A','a',0),(1,'B','b',1),(2,'A','a',1),(2,'B','b',0),(3,'A','Anote sua hipótese',1);
INSERT INTO explanations VALUES (1,'explicação da 1','now'), (3,'**Gabarito**: DISSERTATIVA\n**Pulo do Gato**: Raquitismo carencial\n**Raciocínio Clínico**: Deficiência de vitamina D','now');
"""


@pytest.fixture()
def client(tmp_path):
    dbfile = tmp_path / "medquest_test.db"
    con = sqlite3.connect(dbfile)
    con.executescript(SCHEMA_AND_SEED)
    con.commit()
    con.close()
    os.environ["MEDQUEST_DB"] = str(dbfile)
    try:
        app = create_app(testing=True)
        yield app.test_client()
    finally:
        os.environ.pop("MEDQUEST_DB", None)
