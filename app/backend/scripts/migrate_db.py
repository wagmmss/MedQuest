"""Executa o bootstrap e as migrações do banco uma única vez por release.

Use antes de iniciar workers web em produção:
    python -m scripts.migrate_db
"""

from api import create_app


def main():
    create_app(initialize_db=True)


if __name__ == "__main__":
    main()
