# -*- coding: utf-8 -*-
"""
Backup consistente do medquest.db usando a API de backup online do SQLite.

Diferente de copiar o arquivo (o que pode capturar o banco no meio de uma
escrita e gerar um .db corrompido), sqlite3.Connection.backup() tira um
snapshot transacionalmente consistente mesmo com o app rodando.

Uso:
    python backup_db.py                # cria backups/medquest_<timestamp>.db
    python backup_db.py --tag pre-fts  # cria backups/medquest_<timestamp>_pre-fts.db
    python backup_db.py --keep 5       # mantém só os 5 backups mais recentes

Rode SEMPRE antes de qualquer script que escreve no banco
(reclassify_subtemas.py, migrations, merge_*.py).
"""
import argparse
import os
import sqlite3
import sys
from datetime import datetime

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BACKEND_DIR, "medquest.db")
BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(BACKEND_DIR)), "backups")

KEEP_DEFAULT = 10


def make_backup(tag: str | None = None) -> str:
    if not os.path.exists(DB_PATH):
        print(f"ERRO: banco não encontrado em {DB_PATH}")
        sys.exit(1)

    os.makedirs(BACKUP_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    suffix = f"_{tag}" if tag else ""
    dest = os.path.join(BACKUP_DIR, f"medquest_{stamp}{suffix}.db")

    src = sqlite3.connect(DB_PATH)
    dst = sqlite3.connect(dest)
    try:
        with dst:
            src.backup(dst)
    finally:
        dst.close()
        src.close()

    size_mb = os.path.getsize(dest) / (1024 * 1024)
    print(f"Backup criado: {dest}  ({size_mb:.1f} MB)")
    return dest


def prune(keep: int) -> None:
    """Remove os backups mais antigos, mantendo os `keep` mais recentes."""
    if not os.path.isdir(BACKUP_DIR):
        return
    files = sorted(
        (f for f in os.listdir(BACKUP_DIR) if f.startswith("medquest_") and f.endswith(".db")),
        reverse=True,
    )
    for old in files[keep:]:
        os.remove(os.path.join(BACKUP_DIR, old))
        print(f"  removido backup antigo: {old}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Backup consistente do medquest.db")
    p.add_argument("--tag", help="sufixo descritivo, ex.: pre-reclass")
    p.add_argument("--keep", type=int, default=KEEP_DEFAULT,
                   help=f"quantos backups manter (padrão: {KEEP_DEFAULT})")
    a = p.parse_args()

    make_backup(a.tag)
    prune(a.keep)
