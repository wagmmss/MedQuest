import pytest

from api.db import TursoConnection, db_transaction


class FakeCursor:
    def __init__(self, rows_affected=1):
        self.description = []
        self.rowcount = rows_affected
        self.lastrowid = None
        self.closed = False

    def fetchone(self):
        return None

    def fetchall(self):
        return []

    def close(self):
        self.closed = True


class FakeClient:
    def __init__(self):
        self.statements = []
        self.committed = False
        self.rolled_back = False
        self.last_cursor = None

    def execute(self, sql, args=()):
        self.statements.append((sql, list(args)))
        self.last_cursor = FakeCursor()
        return self.last_cursor

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        pass


def test_turso_transaction_commits_all_statements_together():
    client = FakeClient()
    db = TursoConnection(client)

    with db_transaction(db, immediate=True):
        db.execute("INSERT INTO attempts VALUES (?)", (1,))
        db.execute("UPDATE idempotency_keys SET status = ?", ("completed",))

    assert [statement[0] for statement in client.statements] == [
        "BEGIN IMMEDIATE",
        "INSERT INTO attempts VALUES (?)",
        "UPDATE idempotency_keys SET status = ?",
    ]
    assert client.committed is True
    assert client.rolled_back is False
    assert db.tx is False


def test_turso_transaction_rolls_back_on_failure():
    client = FakeClient()
    db = TursoConnection(client)

    with pytest.raises(RuntimeError, match="injected failure"), db_transaction(db):
        db.execute("INSERT INTO attempts VALUES (?)", (1,))
        raise RuntimeError("injected failure")

    assert client.committed is False
    assert client.rolled_back is True
    assert db.tx is False


def test_turso_cursor_closes_underlying_cursor():
    client = FakeClient()
    db = TursoConnection(client)

    cursor = db.execute("SELECT 1")
    cursor.close()

    assert client.last_cursor.closed is True


def test_http_turso_url_is_rejected_before_startup(monkeypatch):
    from api import create_app

    monkeypatch.setenv("TURSO_DATABASE_URL", "https://example.invalid")
    monkeypatch.setenv("TURSO_AUTH_TOKEN", "secret")
    with pytest.raises(ValueError, match="must use libsql:// or wss://"):
        create_app()


def test_partial_turso_configuration_is_rejected(monkeypatch):
    from api import create_app

    monkeypatch.setenv("TURSO_DATABASE_URL", "libsql://example.invalid")
    monkeypatch.delenv("TURSO_AUTH_TOKEN", raising=False)
    with pytest.raises(ValueError, match="must be configured together"):
        create_app()
