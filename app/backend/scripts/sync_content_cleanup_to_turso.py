"""Sincroniza para o Turso as explicações revisadas e a exclusão do HRAC.

O script é seguro por padrão: sem ``--apply`` ele só compara os bancos. A
sincronização não altera tentativas, favoritos ou revisões dos usuários.
"""

from __future__ import annotations

import argparse
import sqlite3

from sync_incremental_turso import LOCAL_DB, convert_value, execute_pipeline, make_close, make_execute


HRAC_FILTER = """
    UPPER(COALESCE(institution_code, '')) LIKE '%HRAC%'
    OR UPPER(COALESCE(institution_label, '')) LIKE '%HRAC%'
    OR UPPER(COALESCE(source_file, '')) LIKE '%HRAC%'
"""
CHILD_TABLES = (
    "alternatives",
    "question_images",
    "explanations",
    "attempts",
    "favorites",
    "spaced_repetition",
    "flashcards",
    "reclassification_audit",
)


def rows(sql: str, args: list | None = None) -> list[list[dict]]:
    result = execute_pipeline([make_execute(sql, args), make_close()])
    return result["results"][0]["response"]["result"]["rows"]


def remote_question_ids() -> set[int]:
    return {int(row[0]["value"]) for row in rows("SELECT id FROM questions")}


def remote_table_names() -> set[str]:
    return {row[0]["value"] for row in rows("SELECT name FROM sqlite_master WHERE type = 'table'")}


def delete_remote_hrac(tables: set[str]) -> None:
    statements = [make_execute("BEGIN")]
    for table in CHILD_TABLES:
        if table in tables:
            statements.append(make_execute(
                f"DELETE FROM {table} WHERE question_id IN (SELECT id FROM questions WHERE {HRAC_FILTER})"
            ))
    statements.extend((
        make_execute(f"DELETE FROM questions WHERE {HRAC_FILTER}"),
        make_execute("COMMIT"),
        make_close(),
    ))
    execute_pipeline(statements)


def sync_explanations(local_rows: list[sqlite3.Row]) -> None:
    upsert = (
        "INSERT INTO explanations (question_id, explanation_text) VALUES (?, ?) "
        "ON CONFLICT(question_id) DO UPDATE SET explanation_text = excluded.explanation_text"
    )
    batch_size = 25
    for start in range(0, len(local_rows), batch_size):
        batch = local_rows[start:start + batch_size]
        statements = [make_execute("BEGIN")]
        statements.extend(
            make_execute(upsert, [convert_value(row["question_id"]), convert_value(row["explanation_text"])])
            for row in batch
        )
        statements.extend((make_execute("COMMIT"), make_close()))
        execute_pipeline(statements)
        done = min(start + batch_size, len(local_rows))
        if done % 500 < batch_size or done == len(local_rows):
            print(f"  Explicações sincronizadas: {done}/{len(local_rows)}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Efetiva a sincronização no Turso.")
    args = parser.parse_args()

    with sqlite3.connect(LOCAL_DB) as local:
        local.row_factory = sqlite3.Row
        remote_ids = remote_question_ids()
        local_explanations = local.execute(
            "SELECT e.question_id, e.explanation_text FROM explanations e "
            "JOIN questions q ON q.id = e.question_id ORDER BY e.question_id"
        ).fetchall()
        matching_explanations = [row for row in local_explanations if row["question_id"] in remote_ids]
        missing_remote_questions = len(local_explanations) - len(matching_explanations)

    remote_hrac = len(rows(f"SELECT id FROM questions WHERE {HRAC_FILTER}"))
    print(f"Turso: {len(remote_ids)} questões; {remote_hrac} questões HRAC.")
    print(f"Explicações locais a atualizar: {len(matching_explanations)}; questões locais ausentes no Turso: {missing_remote_questions}.")
    if not args.apply:
        return

    tables = remote_table_names()
    delete_remote_hrac(tables)
    sync_explanations(matching_explanations)

    remaining_hrac = len(rows(f"SELECT id FROM questions WHERE {HRAC_FILTER}"))
    if remaining_hrac:
        raise RuntimeError(f"A exclusão remota do HRAC falhou: {remaining_hrac} questões restantes.")
    print("Sincronização concluída: explicações atualizadas e HRAC removido do Turso.")


if __name__ == "__main__":
    main()
