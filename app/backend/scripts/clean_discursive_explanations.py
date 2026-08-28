"""
Script para higienização determinística de comentários de questões dissertativas.
Remove placeholders genéricos (Letra A, DISSERTATIVA / RESPOSTA CURTA, etc.)
e seções de alternativas/distratores indevidas em questões abertas.
"""

import os
import re
import sys
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "medquest.db"


def is_discursive_question(conn: sqlite3.Connection, qid: int) -> bool:
    alts = conn.execute(
        "SELECT letter, text FROM alternatives WHERE question_id = ? ORDER BY letter",
        (qid,)
    ).fetchall()
    if len(alts) <= 1:
        return True
    for a in alts:
        txt = (a["text"] or "").casefold()
        if any(p in txt for p in ["questão dissertativa", "anote sua", "padrao de resposta", "padrão de resposta"]):
            return True
    return False


def clean_discursive_text(exp: str) -> str:
    if not exp:
        return ""
    
    t = exp.strip()
    
    # 1. Strip trailing dummy sections
    t = re.sub(r"\n+\s*\*\*Por que a Letra[\s\S]*$", "", t, flags=re.I).strip()
    t = re.sub(r"\n+\s*\*\*Análise dos Distratores[\s\S]*$", "", t, flags=re.I).strip()
    t = re.sub(r"\n+\s*A alternativa A \(Anote sua principal hipótese[\s\S]*$", "", t, flags=re.I).strip()
    t = re.sub(r"\n+\s*-\s*Revise os critérios que diferenciam as alternativas[\s\S]*$", "", t, flags=re.I).strip()
    
    # 2. Clean generic Gabarito placeholder if present at the top
    t = re.sub(r"^\s*\*\*Gabarito(?:\s+Oficial)?\*\*:\s*(?:DISSERTATIVA|DISCURSIVA)[^\n]*\n+", "", t, flags=re.I).strip()
    t = re.sub(r"^\s*\*\*Gabarito(?:\s+Oficial)?\*\*:\s*Letra\s+A\b[^\n]*\n+", "", t, flags=re.I).strip()
    
    return t


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Limpa seções indevidas de questões dissertativas.")
    parser.add_argument("--apply", action="store_true", help="Aplica as modificações no banco de dados.")
    args = parser.parse_args()

    if not DB_PATH.exists():
        print(f"Erro: Banco de dados não encontrado em {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()
    questions = cursor.execute("""
        SELECT q.id, q.source_file, q.stem, q.correct_letter, e.explanation_text
        FROM questions q
        JOIN explanations e ON e.question_id = q.id
        ORDER BY q.id
    """).fetchall()

    discursive_updates = []
    for q in questions:
        qid = q["id"]
        if is_discursive_question(conn, qid):
            orig = q["explanation_text"] or ""
            cleaned = clean_discursive_text(orig)
            if cleaned != orig:
                discursive_updates.append((cleaned, qid))

    print(f"Total de questões analisadas: {len(questions)}")
    print(f"Questões dissertativas com comentários a atualizar: {len(discursive_updates)}")

    if not args.apply:
        print("\n[DRY RUN] Nenhuma alteração gravada. Use --apply para persistir no banco.")
        return

    # Backup
    backup_path = DB_PATH.with_name(f"{DB_PATH.name}.before-clean-discursive-{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(DB_PATH, backup_path)
    print(f"\n[BACKUP] Criado em: {backup_path}")

    now_iso = datetime.now().isoformat()
    with conn:
        for new_text, qid in discursive_updates:
            conn.execute(
                "UPDATE explanations SET explanation_text = ?, reviewed_at = ? WHERE question_id = ?",
                (new_text, now_iso, qid)
            )

    print(f"[SUCESSO] {len(discursive_updates)} comentários de questões dissertativas atualizados com sucesso!")


if __name__ == "__main__":
    main()
