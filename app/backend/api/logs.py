from flask import Blueprint, request, jsonify
import logging
import os

bp = Blueprint("logs", __name__)

# Basic logging setup
LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "frontend_errors.log")
logging.basicConfig(filename=LOG_FILE, level=logging.ERROR, 
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

@bp.route("/logs/error", methods=["POST"])
def log_error():
    data = request.json
    if not data:
        return jsonify({"success": False}), 400
    
    # Extract error info
    error_msg = data.get("error", "Unknown error")
    info = data.get("info", {})
    url = data.get("url", "unknown")
    user_id = data.get("user_id", "anonymous")
    
    # Log to file
    logging.error(f"[FRONTEND ERROR] User: {user_id} | URL: {url} | Error: {error_msg} | Info: {info}")
    
    return jsonify({"success": True})
