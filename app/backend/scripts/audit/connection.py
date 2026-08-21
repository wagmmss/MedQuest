import sqlite3
import sys
from pathlib import Path

def get_readonly_connection(db_path: Path) -> sqlite3.Connection:
    """Abre o banco de dados em modo restritamente read-only."""
    if not db_path.is_file():
        raise FileNotFoundError(f"Banco não encontrado: {db_path}")

    uri_path = db_path.absolute().as_uri()
    # Assegura strict read-only com URI
    db = sqlite3.connect(f"{uri_path}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    
    # Adiciona restrição no PRAGMA para evitar queries de alteração
    db.execute("PRAGMA query_only=ON")
    
    return db

def scalar(db: sqlite3.Connection, sql: str, params: tuple = ()) -> int:
    return int(db.execute(sql, params).fetchone()[0] or 0)

def rows(db: sqlite3.Connection, sql: str, params: tuple = ()) -> list[dict]:
    return [dict(row) for row in db.execute(sql, params).fetchall()]

def scalar_str(db: sqlite3.Connection, sql: str, params: tuple = ()) -> str | None:
    res = db.execute(sql, params).fetchone()
    return res[0] if res else None
