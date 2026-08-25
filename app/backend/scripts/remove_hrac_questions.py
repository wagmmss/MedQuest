"""Remove questões vinculadas ao HRAC e seus dados dependentes.

Por padrão, apenas mostra a quantidade encontrada. Use ``--apply`` para criar
um backup local e efetivar a remoção em uma única transação.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


DB_PATH = Path(os.environ.get("MEDQUEST_DB", Path(__file__).parents[1] / "medquest.db"))
HRAC_FILTER = """
    UPPER(COALESCE(institution_code, '')) LIKE '%HRAC%'
    OR UPPER(COALESCE(institution_label, '')) LIKE '%HRAC%'
    OR UPPER(COALESCE(source_file, '')) LIKE '%HRAC%'
"""


def dependent_tables(connection: sqlite3.Connection) -> list[str]:
    tables = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    result = []
    for (table,) in tables:
        if table == "questions":
            continue
        columns = connection.execute(f'PRAGMA table_info("{table}")').fetchall()
        if any(column[1] == "question_id" for column in columns):
            result.append(table)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Efetiva a exclusão após criar um backup.")
    args = parser.parse_args()

    with sqlite3.connect(DB_PATH) as connection:
        question_ids = [row[0] for row in connection.execute(f"SELECT id FROM questions WHERE {HRAC_FILTER}")]
        if not question_ids:
            print("Nenhuma questão do HRAC encontrada.")
            return

        placeholders = ",".join("?" for _ in question_ids)
        groups = connection.execute(
            f"""SELECT institution_code, institution_label, source_file, COUNT(*)
                FROM questions WHERE id IN ({placeholders})
                GROUP BY institution_code, institution_label, source_file
                ORDER BY COUNT(*) DESC""",
            question_ids,
        ).fetchall()
        print(f"Questões HRAC encontradas: {len(question_ids)}")
        for code, label, source, count in groups:
            print(f"- {count}: código={code or '-'} | instituição={label or '-'} | fonte={source or '-'}")

        tables = dependent_tables(connection)
        dependencies = {
            table: connection.execute(
                f'SELECT COUNT(*) FROM "{table}" WHERE question_id IN ({placeholders})', question_ids
            ).fetchone()[0]
            for table in tables
        }
        for table, count in dependencies.items():
            if count:
                print(f"- {count} registros vinculados em {table}")

        if not args.apply:
            return

        backup = DB_PATH.with_name(f"{DB_PATH.name}.before-remove-hrac-{datetime.now():%Y%m%d_%H%M%S}")
        shutil.copy2(DB_PATH, backup)
        with connection:
            for table in tables:
                connection.execute(f'DELETE FROM "{table}" WHERE question_id IN ({placeholders})', question_ids)
            connection.execute(f"DELETE FROM questions WHERE id IN ({placeholders})", question_ids)
        print(f"Removidas {len(question_ids)} questões do HRAC. Backup: {backup.name}")


if __name__ == "__main__":
    main()
