"""
MedQuest — ponto de entrada do backend Flask.

A aplicação foi reorganizada em blueprints no pacote `api/`
(questions, stats, plan) com validação Pydantic, SRS via FSRS e config por ambiente.

Uso:
    python app.py            (dev; abre http://localhost:5050)
Produção (WSGI): `from app import app as application`.
"""
from api import create_app
from api.config import Config

app = create_app()

if __name__ == "__main__":
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
