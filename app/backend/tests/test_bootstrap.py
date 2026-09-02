"""Teste de regressão para validar o bootstrap do banco de dados em um SQLite vazio."""
import os
import sqlite3
from api import create_app
from api.config import Config


def test_empty_database_bootstrap(tmp_path):
    """Garante que create_app inicializa corretamente todas as tabelas e índices em um banco vazio."""
    empty_db = tmp_path / "brand_new_empty.db"
    assert not empty_db.exists()

    os.environ["MEDQUEST_DB"] = str(empty_db)
    try:
        app = create_app(testing=True)
        assert empty_db.exists()

        client = app.test_client()
        res = client.get("/")
        assert res.status_code == 200

        # Verifica se as tabelas core e índices foram criados sem erro
        con = sqlite3.connect(empty_db)
        cur = con.cursor()
        tables = [row[0] for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        con.close()

        expected_tables = [
            "questions",
            "alternatives",
            "attempts",
            "explanations",
            "question_images",
            "favorites",
            "spaced_repetition",
            "planner_progress",
            "flashcards",
            "simulado_sessions",
            "idempotency_keys",
            "telemetry_daily_aggregates",
        ]
        for table in expected_tables:
            assert table in tables, f"Tabela '{table}' deveria ter sido criada no bootstrap do banco vazio"
    finally:
        os.environ.pop("MEDQUEST_DB", None)


def test_production_worker_skips_bootstrap_after_release_migration(tmp_path, monkeypatch):
    """Workers de produção não devem disputar DDL depois do bootstrap único."""
    db_path = tmp_path / "release_managed.db"
    monkeypatch.setenv("MEDQUEST_DB", str(db_path))
    monkeypatch.setattr(Config, "AUTO_MIGRATE", False)

    # Com a flag de produção, o worker não executa DDL no boot.
    create_app()
    assert not db_path.exists()

    create_app(initialize_db=True)
    assert db_path.exists()
