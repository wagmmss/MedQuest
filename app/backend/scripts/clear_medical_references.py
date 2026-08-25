"""Remove referências médicas armazenadas nas questões existentes.

O campo é mantido no esquema por compatibilidade com importações e respostas
históricas da API, mas seu conteúdo é apagado de forma idempotente.
"""

from __future__ import annotations

import argparse
import os
import re
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path


DB_PATH = Path(os.environ.get("MEDQUEST_DB", Path(__file__).parents[1] / "medquest.db"))

# Referências foram incluídas tanto na coluna própria quanto, em versões mais
# antigas, no meio de ``explanations.explanation_text``. O corte deve parar no
# próximo bloco pedagógico, em vez de apagar todo o restante da explicação.
REFERENCE_SECTION = re.compile(
    r"(?:^|\n)[ \t]*(?:[-*+][ \t]+)?(?:#{1,6}[ \t]+)?(?:<br\s*/?>\s*)?(?:\*\*)?\s*"
    r"(?:refer[eê]ncias?(?:\s+bibliogr[aá]ficas?)?|bibliografia|fontes?)"
    r"\s*:?[ \t]*(?:\*\*)?[\s\S]*?"
    r"(?=\n[ \t]*(?:#{1,6}[ \t]+)?(?:\*\*)?\s*"
    r"(?:pulo do gato|racioc[ií]nio cl[ií]nico|fundamentação teórica|discussão do caso|"
    r"comentário do caso|padrão de resposta|resolução detalhada|alternativa correta|"
    r"por que a letra|análise dos distratores|distratores|alternativas incorretas|gabarito)\b|\Z)",
    re.IGNORECASE,
)


def without_reference_section(text: str) -> str:
    cleaned = REFERENCE_SECTION.sub("", text)
    # Do not leave literal HTML line breaks or blank lines at the end.
    return re.sub(r"(?:\s|<br\s*/?>)+$", "", cleaned, flags=re.IGNORECASE)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Apenas informa quantos textos seriam alterados.")
    parser.add_argument("--audit", action="store_true", help="Mostra as linhas remanescentes que mencionam referências.")
    parser.add_argument(
        "--restore-from",
        type=Path,
        nargs="+",
        help="Restaura explicações dos backups informados antes de remover somente as referências.",
    )
    args = parser.parse_args()

    with sqlite3.connect(DB_PATH) as connection:
        restored = 0
        if args.restore_from:
            source_texts: dict[int, str] = {}
            for index, backup_path in enumerate(args.restore_from):
                if not backup_path.is_file():
                    raise FileNotFoundError(f"Backup não encontrado: {backup_path}")
                alias = f"backup_{index}"
                connection.execute(f"ATTACH DATABASE ? AS {alias}", (str(backup_path),))
                for question_id, text in connection.execute(f"SELECT question_id, explanation_text FROM {alias}.explanations"):
                    # Entre versões do mesmo comentário, a mais longa preserva
                    # os blocos que uma limpeza anterior pode ter truncado.
                    if text and len(text) > len(source_texts.get(question_id, "")):
                        source_texts[question_id] = text
            current_ids = {row[0] for row in connection.execute("SELECT question_id FROM explanations")}
            restore_rows = [(text, question_id) for question_id, text in source_texts.items() if question_id in current_ids]
            restored = len(restore_rows)
            if args.dry_run:
                print(f"Explicações que seriam restauradas: {restored}.")
                return
            snapshot = DB_PATH.with_name(f"{DB_PATH.name}.before-reference-recovery-{datetime.now():%Y%m%d_%H%M%S}")
            shutil.copy2(DB_PATH, snapshot)
            connection.executemany("UPDATE explanations SET explanation_text = ? WHERE question_id = ?", restore_rows)
            # Keep the attached backup open until this connection is closed;
            # SQLite cannot detach it while the restore transaction is active.
        reference_cursor = connection.execute(
            "UPDATE questions SET medical_references = NULL "
            "WHERE medical_references IS NOT NULL AND TRIM(medical_references) != ''"
        )
        rows = connection.execute(
            "SELECT question_id, explanation_text FROM explanations "
            "WHERE explanation_text IS NOT NULL AND LOWER(explanation_text) "
            "LIKE '%refer%ncia%'"
        ).fetchall()
        updates = [
            (without_reference_section(text), question_id)
            for question_id, text in rows
            if without_reference_section(text) != text
        ]

        if args.audit:
            remaining = connection.execute(
                "SELECT question_id, explanation_text FROM explanations "
                "WHERE LOWER(explanation_text) LIKE '%refer%' OR LOWER(explanation_text) LIKE '%bibliogr%'"
            ).fetchall()
            print(f"Explicações com menção a referência/bibliografia: {len(remaining)}")
            for question_id, text in remaining[:20]:
                lines = [line.strip() for line in text.splitlines() if "refer" in line.lower() or "bibliogr" in line.lower()]
                preview = " | ".join(lines[:2])[:240].encode("ascii", "replace").decode()
                print(f"- questão {question_id}: {preview}")
            return

        if args.dry_run:
            connection.rollback()
            print(f"Referências em coluna própria: {reference_cursor.rowcount}; blocos no texto: {len(updates)}.")
            return

        connection.executemany(
            "UPDATE explanations SET explanation_text = ? WHERE question_id = ?",
            updates,
        )
        print(f"Explicações restauradas: {restored}; referências removidas de {reference_cursor.rowcount} campos e {len(updates)} explicações.")


if __name__ == "__main__":
    main()
