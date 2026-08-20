"""Application factory do MedQuest (Flask + blueprints)."""
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv() # Carrega as variáveis de ambiente do arquivo .env

from .config import Config
from .db import close_db, init_db
from .questions import bp as questions_bp
from .stats import bp as stats_bp
from .plan import bp as plan_bp
from .flashcards import bp as flashcards_bp


from .logs import bp as logs_bp

def create_app(testing=False):
    app = Flask(__name__)
    app.config.from_object(Config)
    if testing:
        app.config["TESTING"] = True
    import os
    frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
    CORS(app, origins=[frontend_url, "http://localhost:3000", "http://127.0.0.1:3000"])

    @app.route("/")
    def index():
        return jsonify({"status": "ok", "app": "MedQuest API", "docs": "/api"})

    from .auth import require_auth
    
    @app.before_request
    @require_auth
    def authenticate_request():
        if request.path == "/" or request.method == "OPTIONS" or "/images/" in request.path or "/logs/error" in request.path:
            return
        pass

    from werkzeug.exceptions import HTTPException

    @app.errorhandler(Exception)
    def handle_exception(e):
        if isinstance(e, HTTPException):
            return jsonify({"error": e.name, "description": e.description}), e.code
        
        app.logger.error(f"Unhandled Exception: {e}", exc_info=True)
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
