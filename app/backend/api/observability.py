"""Structured request telemetry with a small in-process performance registry."""

import json
import logging
import math
import os
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime, timezone

from flask import g, request

logger = logging.getLogger("medquest.telemetry")
_latencies = defaultdict(lambda: deque(maxlen=500))
_status_counts = defaultdict(int)


def configure_logging(app):
    """Use stdout JSON logs so the hosting platform can index and alert on them."""
    level = getattr(logging, os.environ.get("LOG_LEVEL", "INFO").upper(), logging.INFO)
    root = logging.getLogger()
    root.setLevel(level)
    if not root.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        root.addHandler(handler)
    app.logger.setLevel(level)


def emit(event, level=logging.INFO, **fields):
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        **fields,
    }
    logger.log(level, json.dumps(payload, ensure_ascii=False, separators=(",", ":")))


def _route_name():
    return request.url_rule.rule if request.url_rule else request.path


def start_request():
    incoming = request.headers.get("X-Request-ID", "")
    try:
        request_id = str(uuid.UUID(incoming))
    except (ValueError, TypeError, AttributeError):
        request_id = str(uuid.uuid4())
    g.request_id = request_id
    g.request_started_at = time.perf_counter()


def finish_request(response):
    started = getattr(g, "request_started_at", None)
    duration_ms = round((time.perf_counter() - started) * 1000, 2) if started else 0.0
    route = _route_name()
    metric_key = (request.method, route)
    _latencies[metric_key].append(duration_ms)
    _status_counts[(request.method, route, response.status_code)] += 1

    request_id = getattr(g, "request_id", str(uuid.uuid4()))
    response.headers["X-Request-ID"] = request_id
    response.headers["Server-Timing"] = f'app;dur={duration_ms:.2f}'
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    if request.is_secure:
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")

    emit(
        "http_request",
        request_id=request_id,
        method=request.method,
        route=route,
        status=response.status_code,
        duration_ms=duration_ms,
    )
    return response


def _percentile(values, quantile):
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, math.ceil(len(ordered) * quantile) - 1)
    return round(ordered[index], 2)


def performance_snapshot():
    routes = []
    for (method, route), values in sorted(_latencies.items()):
        statuses = {
            str(status): count
            for (status_method, status_route, status), count in _status_counts.items()
            if status_method == method and status_route == route
        }
        routes.append({
            "method": method,
            "route": route,
            "requests": len(values),
            "p50_ms": _percentile(values, 0.5),
            "p95_ms": _percentile(values, 0.95),
            "max_ms": round(max(values), 2) if values else 0.0,
            "statuses": statuses,
        })
    return {"generated_at": datetime.now(timezone.utc).isoformat(), "routes": routes}
