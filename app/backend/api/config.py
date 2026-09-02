"""Configuração por ambiente (nada de debug/segredo hardcoded em produção)."""
import os


class Config:
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
    HOST = os.environ.get("HOST", "0.0.0.0")
    PORT = int(os.environ.get("PORT", "5050"))
    # Em produção, o container executa `scripts.migrate_db` antes de subir os
    # workers. Isso impede que cada worker Gunicorn dispute DDL/locks ao
    # iniciar. Desenvolvimento local continua com bootstrap automático.
    AUTO_MIGRATE = os.environ.get("MEDQUEST_AUTO_MIGRATE", "1") == "1"
