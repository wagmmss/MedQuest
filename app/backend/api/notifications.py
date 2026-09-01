"""Blueprint: Gestão de Notificações PWA Opt-in e Disparo de Revisões FSRS (MedQuest).

Implementa:
- Preferências por usuário (horário, dias da semana, ativação/desativação).
- Inscrição, listagem segura e revogação de assinaturas Web Push.
- Endpoint de cron idempotente com limite estrito de 1 lembrete diário por usuário.
- Payload 100% genérico (sem dados médicos, nomes de questões ou notas).
"""

from datetime import datetime, timezone
import hmac
import json
import logging
import os

from flask import Blueprint, g, jsonify, request

from .db import db_transaction, get_db
from .observability import record_domain_event
from .schemas import (
    CronDispatchIn,
    NotificationConfigIn,
    PushSubscriptionIn,
    PushUnsubscribeIn,
    ValidationError,
    validation_errors,
)
from .webpush import get_vapid_public_key, send_web_push

bp = Blueprint("notifications", __name__)
logger = logging.getLogger(__name__)


def _verify_cron_secret(req) -> bool:
    """Valida o segredo de autenticação do cron de notificações."""
    configured_secret = os.environ.get("NOTIFICATIONS_CRON_SECRET") or os.environ.get("CRON_SECRET") or ""
    if not configured_secret:
        return False

    provided_secret = req.headers.get("X-Cron-Secret", "")
    if not provided_secret:
        auth_header = req.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            provided_secret = auth_header.removeprefix("Bearer ").strip()

    if not provided_secret:
        return False

    return hmac.compare_digest(configured_secret, provided_secret)


@bp.route("/notifications/config", methods=["GET"])
def get_config():
    """Retorna as preferências de notificação do usuário autenticado."""
    db = get_db()
    row = db.execute(
        "SELECT enabled, preferred_hour, days_of_week, max_daily_reminders, updated_at FROM notification_configs WHERE user_id = ?",
        (g.user_id,),
    ).fetchone()

    subs_count = db.execute(
        "SELECT COUNT(*) AS n FROM push_subscriptions WHERE user_id = ?",
        (g.user_id,),
    ).fetchone()["n"]

    if row:
        try:
            days = json.loads(row["days_of_week"])
        except Exception:
            days = [0, 1, 2, 3, 4, 5, 6]

        config = {
            "enabled": bool(row["enabled"]),
            "preferred_hour": int(row["preferred_hour"]),
            "days_of_week": days,
            "max_daily_reminders": int(row["max_daily_reminders"] or 1),
            "updated_at": row["updated_at"],
            "has_active_subscription": subs_count > 0,
            "vapid_public_key": get_vapid_public_key(),
        }
    else:
        config = {
            "enabled": False,
            "preferred_hour": 8,
            "days_of_week": [0, 1, 2, 3, 4, 5, 6],
            "max_daily_reminders": 1,
            "updated_at": None,
            "has_active_subscription": subs_count > 0,
            "vapid_public_key": get_vapid_public_key(),
        }

    return jsonify(config)


@bp.route("/notifications/config", methods=["PUT"])
def update_config():
    """Atualiza as preferências de notificação do usuário autenticado."""
    try:
        data = NotificationConfigIn.model_validate(request.get_json(force=True) or {})
    except ValidationError as e:
        return jsonify({"error": "invalid input", "details": validation_errors(e)}), 400

    db = get_db()
    now_iso = datetime.now(timezone.utc).isoformat()
    days_json = json.dumps(data.days_of_week)

    with db_transaction(db, immediate=True):
        db.execute(
            """
            INSERT INTO notification_configs (user_id, enabled, preferred_hour, days_of_week, max_daily_reminders, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                enabled = excluded.enabled,
                preferred_hour = excluded.preferred_hour,
                days_of_week = excluded.days_of_week,
                max_daily_reminders = excluded.max_daily_reminders,
                updated_at = excluded.updated_at
            """,
            (g.user_id, 1 if data.enabled else 0, data.preferred_hour, days_json, data.max_daily_reminders, now_iso),
        )

    record_domain_event("notification_config_updated", user_id=g.user_id, enabled=data.enabled)

    return jsonify({
        "enabled": data.enabled,
        "preferred_hour": data.preferred_hour,
        "days_of_week": data.days_of_week,
        "max_daily_reminders": data.max_daily_reminders,
        "updated_at": now_iso,
    })


@bp.route("/notifications/subscribe", methods=["POST"])
def subscribe():
    """Registra uma assinatura Web Push do navegador para o usuário atual."""
    try:
        data = PushSubscriptionIn.model_validate(request.get_json(force=True) or {})
    except ValidationError as e:
        return jsonify({"error": "invalid input", "details": validation_errors(e)}), 400

    db = get_db()
    now_iso = datetime.now(timezone.utc).isoformat()

    with db_transaction(db, immediate=True):
        db.execute(
            """
            INSERT INTO push_subscriptions (user_id, endpoint, p256dh, auth, created_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, endpoint) DO UPDATE SET
                p256dh = excluded.p256dh,
                auth = excluded.auth,
                created_at = excluded.created_at
            """,
            (g.user_id, data.endpoint, data.keys.p256dh, data.keys.auth, now_iso),
        )

        # Habilita automaticamente as notificações nas preferências ao subscrever
        db.execute(
            """
            INSERT INTO notification_configs (user_id, enabled, preferred_hour, days_of_week, max_daily_reminders, updated_at)
            VALUES (?, 1, 8, '[0,1,2,3,4,5,6]', 1, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                enabled = 1,
                updated_at = excluded.updated_at
            """,
            (g.user_id, now_iso),
        )

    record_domain_event("push_subscribed", user_id=g.user_id)

    return jsonify({"success": True})


@bp.route("/notifications/subscribe", methods=["DELETE"])
def unsubscribe():
    """Remove uma ou todas as assinaturas Web Push do usuário autenticado."""
    payload = request.get_json(silent=True) or {}
    try:
        data = PushUnsubscribeIn.model_validate(payload)
    except ValidationError as e:
        return jsonify({"error": "invalid input", "details": validation_errors(e)}), 400

    db = get_db()
    now_iso = datetime.now(timezone.utc).isoformat()

    with db_transaction(db, immediate=True):
        if data.endpoint:
            db.execute(
                "DELETE FROM push_subscriptions WHERE user_id = ? AND endpoint = ?",
                (g.user_id, data.endpoint),
            )
        else:
            db.execute(
                "DELETE FROM push_subscriptions WHERE user_id = ?",
                (g.user_id,),
            )
            # Desativa nas preferências caso todas as subscriptions tenham sido revogadas
            db.execute(
                "UPDATE notification_configs SET enabled = 0, updated_at = ? WHERE user_id = ?",
                (now_iso, g.user_id),
            )

    record_domain_event("push_unsubscribed", user_id=g.user_id, endpoint_specific=bool(data.endpoint))

    return jsonify({"success": True})


@bp.route("/notifications/cron/dispatch", methods=["POST"])
def cron_dispatch():
    """Endpoint interno executado periodicamente pelo cron para enviar lembretes FSRS."""
    if not _verify_cron_secret(request):
        return jsonify({"error": "Unauthorized"}), 401

    payload = request.get_json(silent=True) or {}
    try:
        data = CronDispatchIn.model_validate(payload)
    except ValidationError as e:
        return jsonify({"error": "invalid input", "details": validation_errors(e)}), 400

    now_utc = datetime.now(timezone.utc)
    today_date = now_utc.strftime("%Y-%m-%d")
    current_hour = now_utc.hour
    current_weekday = now_utc.weekday()  # 0=Segunda, 6=Domingo

    db = get_db()

    # Busca configurações ativas
    if data.force_user_id:
        configs = db.execute(
            "SELECT user_id, preferred_hour, days_of_week, max_daily_reminders FROM notification_configs WHERE user_id = ? AND enabled = 1",
            (data.force_user_id,),
        ).fetchall()
    else:
        configs = db.execute(
            "SELECT user_id, preferred_hour, days_of_week, max_daily_reminders FROM notification_configs WHERE enabled = 1"
        ).fetchall()

    dispatched_count = 0
    eligible_count = 0
    skipped_already_dispatched = 0

    generic_payload = {
        "title": "MedQuest",
        "body": "Você tem revisões pendentes para hoje. Mantenha seu ritmo de estudos!",
        "url": "/revisao-ativa",
        "tag": "medquest-fsrs-review",
    }

    for cfg in configs:
        user_id = str(cfg["user_id"])

        # Validação do horário e dia da semana (a menos que ignore_hour=True)
        if not data.ignore_hour:
            if int(cfg["preferred_hour"]) != current_hour:
                continue

            try:
                days = json.loads(cfg["days_of_week"])
                if current_weekday not in days:
                    continue
            except Exception:
                pass

        # Verifica se há revisões FSRS vencidas na data de hoje ou anterior
        due_srs = db.execute(
            "SELECT 1 FROM spaced_repetition WHERE user_id = ? AND next_review_date <= ? LIMIT 1",
            (user_id, today_date),
        ).fetchone()

        due_fc = db.execute(
            "SELECT 1 FROM flashcards WHERE user_id = ? AND next_review_date <= ? LIMIT 1",
            (user_id, today_date),
        ).fetchone()

        if not due_srs and not due_fc:
            continue

        # Reserva atômica em transação imediata: apenas o processo que efetuar o INSERT pode disparar
        try:
            with db_transaction(db, immediate=True):
                cur = db.execute(
                    """
                    INSERT INTO notification_dispatches (user_id, dispatch_date, status, created_at)
                    VALUES (?, ?, 'reserved', ?)
                    ON CONFLICT(user_id, dispatch_date) DO NOTHING
                    """,
                    (user_id, today_date, now_utc.isoformat()),
                )
                reserved = (cur.rowcount > 0)
        except Exception:
            reserved = False

        if not reserved:
            skipped_already_dispatched += 1
            continue

        eligible_count += 1

        # Busca subscriptions do usuário
        subscriptions = db.execute(
            "SELECT id, endpoint, p256dh, auth FROM push_subscriptions WHERE user_id = ?",
            (user_id,),
        ).fetchall()

        if not subscriptions:
            with db_transaction(db, immediate=True):
                db.execute(
                    "UPDATE notification_dispatches SET status = 'no_subscription' WHERE user_id = ? AND dispatch_date = ?",
                    (user_id, today_date),
                )
            continue

        user_sent = False
        expired_count = 0
        for sub in subscriptions:
            sub_dict = {
                "endpoint": sub["endpoint"],
                "keys": {"p256dh": sub["p256dh"], "auth": sub["auth"]},
            }
            res = send_web_push(sub_dict, generic_payload)

            if res.get("status") == "delivered":
                user_sent = True
            elif res.get("status") == "expired":
                expired_count += 1
                # Limpeza automática de subscrição expirada
                with db_transaction(db, immediate=True):
                    db.execute("DELETE FROM push_subscriptions WHERE id = ?", (sub["id"],))

        final_status = "delivered" if user_sent else ("expired" if expired_count == len(subscriptions) else "failed")
        with db_transaction(db, immediate=True):
            db.execute(
                "UPDATE notification_dispatches SET status = ? WHERE user_id = ? AND dispatch_date = ?",
                (final_status, user_id, today_date),
            )

        if user_sent:
            dispatched_count += 1
            record_domain_event("notification_dispatched", user_id=user_id, status="delivered", dispatch_date=today_date)
        else:
            record_domain_event("notification_dispatched", user_id=user_id, status=final_status, dispatch_date=today_date)

    return jsonify({
        "success": True,
        "dispatched_count": dispatched_count,
        "eligible_count": eligible_count,
        "skipped_already_dispatched": skipped_already_dispatched,
    })
