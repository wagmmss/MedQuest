"""Authenticated, bounded telemetry ingestion and performance diagnostics."""

import hmac
import logging
import os
from urllib.parse import urlsplit

from flask import Blueprint, current_app, g, jsonify, request

from .observability import emit, performance_snapshot

bp = Blueprint("logs", __name__)

WEB_VITAL_NAMES = {"CLS", "FCP", "FID", "INP", "LCP", "TTFB"}


def _safe_path(value):
    if not isinstance(value, str):
        return "unknown"
    try:
        parsed = urlsplit(value[:2048])
        return parsed.path[:512] or "/"
    except ValueError:
        return "unknown"

@bp.route("/logs/error", methods=["POST"])
def log_error():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON body"}), 400
    message = data.get("error")
    if not isinstance(message, str) or not message.strip():
        return jsonify({"error": "error is required"}), 400
    info = data.get("info") if isinstance(data.get("info"), dict) else {}
    emit(
        "frontend_error",
        level=logging.ERROR,
        request_id=getattr(g, "request_id", None),
        owner_scope="guest" if str(g.user_id).startswith("guest:") else "account",
        path=_safe_path(data.get("url")),
        message=message.strip()[:1000],
        digest=str(info.get("digest", ""))[:128],
    )
    return jsonify({"success": True})


@bp.route("/logs/web-vital", methods=["POST"])
def web_vital():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or data.get("name") not in WEB_VITAL_NAMES:
        return jsonify({"error": "Unsupported metric"}), 400
    try:
        value = float(data.get("value"))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid metric value"}), 400
    if value < 0 or value > 3_600_000:
        return jsonify({"error": "Invalid metric value"}), 400
    emit(
        "web_vital",
        request_id=getattr(g, "request_id", None),
        name=data["name"],
        value=round(value, 4),
        rating=data.get("rating") if data.get("rating") in {"good", "needs-improvement", "poor"} else None,
        path=_safe_path(data.get("path")),
    )
    return jsonify({"success": True}), 202


@bp.route("/metrics/performance")
def metrics_performance():
    if not current_app.config.get("TESTING"):
        expected = os.environ.get("METRICS_API_TOKEN", "")
        provided = request.headers.get("X-Metrics-Token", "")
        if not expected:
            return jsonify({"error": "Not Found"}), 404
        if not provided or not hmac.compare_digest(expected, provided):
            return jsonify({"error": "Unauthorized"}), 401
    return jsonify(performance_snapshot())
