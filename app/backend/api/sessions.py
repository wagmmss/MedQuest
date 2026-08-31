import datetime
import json
import logging

from flask import Blueprint, g, jsonify, request

from .auth import require_auth
from .db import db_transaction, get_db
from .observability import trace_db

bp = Blueprint("sessions", __name__)
logger = logging.getLogger(__name__)

@bp.route("/sessions/<session_type>", methods=["GET"])
@require_auth
def get_session(session_type: str):
    """Retorna a sessão salva para o usuário e tipo (ex: quiz, simulado)."""
    user_id = getattr(g, "user_id", "1")
    db = get_db()
    with trace_db("select_learning_session"):
        row = db.execute(
            "SELECT state_json, updated_at FROM learning_sessions WHERE user_id = ? AND session_type = ?",
            (user_id, session_type)
        ).fetchone()
    
    if not row:
        return jsonify({"data": None})
    
    try:
        data = json.loads(row["state_json"])
        return jsonify({"data": data, "updated_at": row["updated_at"]})
    except json.JSONDecodeError:
        return jsonify({"data": None})


@bp.route("/sessions/<session_type>", methods=["PUT"])
@require_auth
def save_session(session_type: str):
    """Salva a sessão para o usuário e tipo."""
    user_id = getattr(g, "user_id", "1")
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid body"}), 400
    
    now = datetime.datetime.now(datetime.UTC).isoformat()
    state_json = json.dumps(data)
    
    db = get_db()
    with trace_db("upsert_learning_session"), db_transaction(db):
        db.execute(
            """INSERT INTO learning_sessions (user_id, session_type, state_json, updated_at) 
               VALUES (?, ?, ?, ?)
               ON CONFLICT(user_id, session_type) DO UPDATE SET 
               state_json=excluded.state_json, updated_at=excluded.updated_at""",
            (user_id, session_type, state_json, now)
        )
    return jsonify({"success": True})


@bp.route("/sessions/<session_type>", methods=["DELETE"])
@require_auth
def delete_session(session_type: str):
    """Deleta a sessão para o usuário e tipo."""
    user_id = getattr(g, "user_id", "1")
    db = get_db()
    with trace_db("delete_learning_session"), db_transaction(db):
        db.execute(
            "DELETE FROM learning_sessions WHERE user_id = ? AND session_type = ?",
            (user_id, session_type)
        )
    return jsonify({"success": True})
