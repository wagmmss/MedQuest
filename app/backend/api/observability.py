"""Structured request telemetry with a small in-process performance registry."""

import json
import logging
import math
import os
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime, timezone
import contextlib

from flask import g, request

logger = logging.getLogger("medquest.telemetry")
_latencies = defaultdict(lambda: deque(maxlen=500))
_status_counts = defaultdict(int)

@contextlib.contextmanager
def trace_db(operation_name: str):
    start = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        emit("db_query", level=logging.DEBUG, operation=operation_name, duration_ms=duration_ms)


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


from flask import g, request, has_app_context


def record_domain_event(event_name: str, user_id: str = None, **fields):
    """Emite um evento de negócio estruturado para análise de funil e produto."""
    uid = user_id
    req_id = None
    if has_app_context():
        uid = uid or getattr(g, "user_id", "unknown")
        req_id = getattr(g, "request_id", None)
    else:
        uid = uid or "system"

    emit(
        "domain_event",
        level=logging.INFO,
        event_name=event_name,
        user_id=str(uid),
        request_id=req_id,
        **fields,
    )


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
        total_reqs = sum(statuses.values()) if statuses else len(values)
        error_reqs = sum(count for st, count in statuses.items() if int(st) >= 400)
        error_rate_pct = round((error_reqs / total_reqs * 100), 2) if total_reqs > 0 else 0.0

        routes.append({
            "method": method,
            "route": route,
            "requests": len(values),
            "p50_ms": _percentile(values, 0.5),
            "p95_ms": _percentile(values, 0.95),
            "p99_ms": _percentile(values, 0.99),
            "max_ms": round(max(values), 2) if values else 0.0,
            "error_rate_pct": error_rate_pct,
            "statuses": statuses,
        })
    return {"generated_at": datetime.now(timezone.utc).isoformat(), "routes": routes}


def flush_daily_metrics_to_db(db) -> int:
    """Consolida métricas em memória na tabela de séries temporais SQL."""
    snapshot = performance_snapshot()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    now_iso = datetime.now(timezone.utc).isoformat()
    inserted = 0

    for route_info in snapshot.get("routes", []):
        method = route_info["method"]
        route = route_info["route"]
        p50 = route_info["p50_ms"]
        p95 = route_info["p95_ms"]
        p99 = route_info["p99_ms"]
        req_count = route_info["requests"]
        statuses = route_info.get("statuses", {})
        err_count = sum(count for st, count in statuses.items() if int(st) >= 400)

        db.execute("""
            INSERT INTO telemetry_daily_aggregates
            (date, route, method, p50_ms, p95_ms, p99_ms, request_count, error_count, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(date, route, method) DO UPDATE SET
                p50_ms=excluded.p50_ms,
                p95_ms=excluded.p95_ms,
                p99_ms=excluded.p99_ms,
                request_count=excluded.request_count,
                error_count=excluded.error_count,
                created_at=excluded.created_at
        """, (today, route, method, p50, p95, p99, req_count, err_count, now_iso))
        inserted += 1

    return inserted

