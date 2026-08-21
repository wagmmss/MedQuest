"""Application factory do MedQuest (Flask + blueprints)."""
import logging
import platform

from dotenv import load_dotenv
from flask import Flask, g, jsonify, request
from flask_cors import CORS

load_dotenv() # Carrega as variáveis de ambiente do arquivo .env

from .config import Config
from .db import close_db, init_db
from .flashcards import bp as flashcards_bp
from .logs import bp as logs_bp
from .observability import configure_logging, emit, finish_request, start_request
from .plan import bp as plan_bp
from .questions import bp as questions_bp
from .stats import bp as stats_bp


def create_app(testing=False):
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024
    if testing:
        app.config["TESTING"] = True
    configure_logging(app)
    import os
    frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
    CORS(app, origins=[frontend_url, "http://localhost:3000", "http://127.0.0.1:3000"])

    app.before_request(start_request)
    app.after_request(finish_request)

    @app.route("/")
    def index():
        return jsonify({
            "status": "ok",
            "app": "MedQuest API",
            "docs": "/api",
            "python": platform.python_version(),
        })

    from .auth import require_auth
    
    @app.before_request
    @require_auth
    def authenticate_request():
        if request.path == "/" or request.method == "OPTIONS" or "/images/" in request.path:
            return

    from werkzeug.exceptions import HTTPException

    @app.errorhandler(Exception)
    def handle_exception(e):
        if isinstance(e, HTTPException):
            return jsonify({"error": e.name, "description": e.description}), e.code
        
        emit(
            "unhandled_exception",
            level=logging.ERROR,
            request_id=getattr(g, "request_id", None),
            route=request.url_rule.rule if request.url_rule else request.path,
            error_type=type(e).__name__,
        )
        app.logger.exception("Unhandled exception request_id=%s", getattr(g, "request_id", None))
        is_debug = app.config.get('DEBUG', False)
        return jsonify({
            "error": "Internal Server Error", 
            "description": str(e) if is_debug else "An unexpected error occurred"
        }), 500

    # Cada blueprint é montado em /api (compatibilidade) e em /api/v1.
    for bp in (questions_bp, stats_bp, plan_bp, flashcards_bp, logs_bp):
        app.register_blueprint(bp, url_prefix="/api")
        app.register_blueprint(bp, url_prefix="/api/v1", name=f"{bp.name}_v1")

    app.teardown_appcontext(close_db)
    init_db(app)
    return app
