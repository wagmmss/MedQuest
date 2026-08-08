"""Application factory do MedQuest (Flask + blueprints)."""
from flask import Flask, send_from_directory
from flask_cors import CORS

from .config import Config
from .db import STATIC_DIR, close_db, init_db
from .questions import bp as questions_bp
from .stats import bp as stats_bp
from .plan import bp as plan_bp


def create_app():
    app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="")
    app.config.from_object(Config)
    CORS(app)

    @app.route("/")
    def index():
        return send_from_directory(STATIC_DIR, "index.html")

    # Cada blueprint é montado em /api (compatibilidade) e em /api/v1.
    for bp in (questions_bp, stats_bp, plan_bp):
        app.register_blueprint(bp, url_prefix="/api")
        app.register_blueprint(bp, url_prefix="/api/v1", name=f"{bp.name}_v1")

    app.teardown_appcontext(close_db)
    init_db(app)
    return app
