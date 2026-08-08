"""Configuração por ambiente (nada de debug/segredo hardcoded em produção)."""
import os


class Config:
    DEBUG = os.environ.get("FLASK_DEBUG", "1") == "1"
    HOST = os.environ.get("HOST", "0.0.0.0")
    PORT = int(os.environ.get("PORT", "5050"))
