import sqlite3
import os
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "medquest.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
c = conn.cursor()

TARGET_INSTITUTIONS = [
    ("USP-SP", "USP - São Paulo (HC-FMUSP)"),
    ("USP-RP", "USP - Ribeirão Preto (HCRP)"),
    ("UNIFESP", "UNIFESP (Escola Paulista de Medicina)"),
    ("UNICAMP", "UNICAMP (Campinas)"),
    ("SUS-SP", "SUS-SP (Seleção Unificada SP)"),
    ("SCMSP", "Santa Casa de São Paulo"),
    ("HSL", "Hospital Sírio-Libanês"),
    ("EINSTEIN", "Hospital Israelita Albert Einstein"),
    ("ENARE", "ENARE (Nacional)"),
]

YEARS = [2026, 2025, 2024, 2023, 2022, 2021, 2020]

print("=" * 95)
print(f"{'INSTITUIÇÃO':<12} | {'ANO':<5} | {'STATUS':<20} | {'QUESTÕES':<9} | {'TIPO/FONTE'}")
print("=" * 95)

summary_missing = []

for code, name in TARGET_INSTITUTIONS:
    for yr in YEARS:
        c.execute("""
            SELECT source_file, editorial_status, COUNT(*) as cnt
            FROM questions
            WHERE institution_code = ? AND year = ?
            GROUP BY source_file, editorial_status
        """, (code, yr))
        rows = c.fetchall()
        
        if not rows:
            print(f"{code:<12} | {yr:<5} | {'❌ FALTANDO':<20} | {'0':<9} | Não cadastrado")
            summary_missing.append((code, yr, "Não cadastrado (0 questões)"))
        else:
            is_har_official = any(r['source_file'] == f"{code} {yr}" for r in rows)
            has_autoral = any(r['editorial_status'] == 'autoral' for r in rows)
            total_qs = sum(r['cnt'] for r in rows)
            sources = ", ".join(set(r['source_file'] for r in rows))
            
            if is_har_official:
                autoral_str = " (+ Autoral)" if has_autoral else ""
                print(f"{code:<12} | {yr:<5} | {'✅ OFICIAL HAR':<20} | {total_qs:<9} | {sources}{autoral_str}")
            else:
                print(f"{code:<12} | {yr:<5} | {'⚠️ LEGADO (PDF)':<20} | {total_qs:<9} | {sources}")
                summary_missing.append((code, yr, f"Legado PDF ({total_qs} q - precisa de HAR)"))

print("=" * 95)
conn.close()
