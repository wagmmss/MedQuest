"""Testes unitários para classificação e separação de instituições (HSL, Einstein, SCMSP, etc.)."""
import pytest
from scripts.extract import classify_institution

def test_classify_institution_tags():
    # HSL
    code, label = classify_institution("SP - Hospital Sírio-Libanês - HSL Residência (Acesso Direto)")
    assert code == "HSL"
    assert "Sírio-Libanês" in label

    # EINSTEIN
    code, label = classify_institution("SP - Hospital Israelita Albert Einstein - HIAE Residência Médica")
    assert code == "EINSTEIN"
    assert "Albert Einstein" in label

    # SCMSP
    code, label = classify_institution("SP - Santa Casa de Misericórdia de São Paulo - SCMSP")
    assert code == "SCMSP"
    assert "Santa Casa" in label

    # SUS-SP
    code, label = classify_institution("SP - Sistema Único de Saúde - SUS SP Acesso Direto (R1)")
    assert code == "SUS-SP"

    # UNICAMP
    code, label = classify_institution("Universidade Estadual de Campinas - Unicamp FCM")
    assert code == "UNICAMP"

    # UNIFESP
    code, label = classify_institution("Universidade Federal de São Paulo - UNIFESP")
    assert code == "UNIFESP"

    # USP-RP
    code, label = classify_institution("Hospital das Clínicas de Ribeirão Preto da USP HCRP")
    assert code == "USP-RP"

    # HRAC-USP
    code, label = classify_institution("Hospital de Reabilitação de Anomalias Craniofaciais - HRAC USP")
    assert code == "HRAC-USP"


def test_meta_endpoint_includes_all_institutions(client):
    # Insere dados de teste com HSL, EINSTEIN e SCMSP
    import sqlite3
    import os
    db_path = os.environ["MEDQUEST_DB"]
    con = sqlite3.connect(db_path)
    con.execute("""
        INSERT INTO questions(id, area, subtema, stem, correct_letter, missing_alts, year, institution_code, institution_label)
        VALUES 
        (10, 'Cirurgia', 'Trauma', 'Q10', 'A', 0, 2024, 'HSL', 'Hospital Sírio-Libanês (HSL)'),
        (11, 'Cirurgia', 'Trauma', 'Q11', 'B', 0, 2024, 'EINSTEIN', 'Hospital Israelita Albert Einstein (HIAE)'),
        (12, 'Cirurgia', 'Trauma', 'Q12', 'C', 0, 2024, 'SCMSP', 'Santa Casa de Misericórdia de São Paulo (SCMSP)')
    """)
    con.commit()
    con.close()

    res = client.get("/api/meta")
    assert res.status_code == 200
    inst_codes = {i["institution_code"] for i in res.json["institutions"]}
    assert "HSL" in inst_codes
    assert "EINSTEIN" in inst_codes
    assert "SCMSP" in inst_codes
