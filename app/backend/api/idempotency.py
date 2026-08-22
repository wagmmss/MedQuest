import hashlib
import json
import logging
import time
import uuid
from datetime import datetime, timezone

from flask import Response, jsonify, request

from .auth import is_valid_uuid_v4
from .db import db_transaction

LEASE_DURATION_SECONDS = 30.0
logger = logging.getLogger(__name__)


class LostLeaseError(RuntimeError):
    """Raised when an obsolete worker tries to commit protected effects."""


def _owns_lease(db, user_id: str, key: str, lease_token: str, status: str) -> bool:
    cursor = db.execute(
        """SELECT 1 AS owned FROM idempotency_keys
           WHERE user_id = ? AND key = ? AND lease_owner_token = ? AND status = ?""",
        (user_id, key, lease_token, status),
    )
    rows = cursor.fetchall()
    row = rows[0] if rows else None
    cursor.close()
    return row is not None


def _database_unavailable():
    return jsonify({"error": "Idempotency storage is temporarily unavailable"}), 503


def reserve_idempotency(db, user_id: str, path: str, method: str, raw_payload: bytes):
    """
    Tenta reservar atomicamente a chave de idempotência antes de qualquer efeito.
    
    Retorna uma tupla (cached_response, error_tuple, lease_token):
      - Se cached_response não for None: chave já concluída com mesmo payload -> retornar resposta.
      - Se error_tuple não for None: conflito (409) ou erro de validação (400) -> retornar erro.
      - Se lease_token não for None: requisição reservou a chave com sucesso -> prosseguir e chamar complete_idempotency ao final.
      - Se todos forem None: requisição não enviou X-Idempotency-Key -> executar sem idempotência.
    """
    key = request.headers.get("X-Idempotency-Key")
    if not key:
        return None, None, None

    if not is_valid_uuid_v4(key):
        return None, (jsonify({"error": "Invalid X-Idempotency-Key: must be a canonical UUID v4"}), 400), None

    normalized_key = key.lower()
    payload_hash = hashlib.sha256(raw_payload).hexdigest()
    now_ts = time.time()
    lease_expires_at = now_ts + LEASE_DURATION_SECONDS
    created_at = datetime.now(timezone.utc).isoformat()
    lease_owner_token = str(uuid.uuid4())

    # INSERT OR IGNORE has the same conflict semantics on SQLite and libSQL.
    try:
        with db_transaction(db, immediate=True):
            db.execute(
                """INSERT OR IGNORE INTO idempotency_keys (user_id, key, method, path, payload_hash, status, status_code, response_body, lease_expires_at, lease_owner_token, created_at)
                   VALUES (?, ?, ?, ?, ?, 'processing', 0, '', ?, ?, ?)""",
                (user_id, normalized_key, method, path, payload_hash, lease_expires_at, lease_owner_token, created_at)
            )
            reserved = _owns_lease(db, user_id, normalized_key, lease_owner_token, "processing")
        if reserved:
            return None, None, lease_owner_token
    except Exception:
        logger.exception("Unable to reserve idempotency key")
        return None, _database_unavailable(), None

    # 2. Investigar o registro existente
    cursor = db.execute(
        "SELECT status, method, path, payload_hash, status_code, response_body, lease_expires_at FROM idempotency_keys WHERE user_id = ? AND key = ?",
        (user_id, normalized_key)
    )
    rows = cursor.fetchall()
    existing = rows[0] if rows else None
    cursor.close()

    if not existing:
        return None, (jsonify({"error": "Idempotency state changed concurrently; retry the request"}), 409), None

    # Verificar divergência de rota, método ou payload
    if (existing["payload_hash"] != payload_hash or 
        existing["path"] != path or 
        existing["method"] != method):
        return None, (jsonify({"error": "Conflict: X-Idempotency-Key already used with different payload or route"}), 409), None

    # Se já foi concluída com sucesso
    if existing["status"] == "completed" and existing["response_body"] is not None:
        return Response(existing["response_body"], status=existing["status_code"] or 200, mimetype="application/json"), None, None

    # Se está em 'processing' ou 'failed'
    if existing["status"] in ("processing", "failed"):
        current_lease = existing["lease_expires_at"] or 0
        if existing["status"] == "failed" or now_ts > current_lease:
            # Lease expirado ou status failed -> tentativa de recuperação atômica
            try:
                with db_transaction(db, immediate=True):
                    db.execute(
                        """UPDATE idempotency_keys 
                           SET status = 'processing', lease_expires_at = ?, payload_hash = ?, method = ?, path = ?, lease_owner_token = ?
                           WHERE user_id = ? AND key = ?
                             AND (status = 'failed' OR (status = 'processing' AND lease_expires_at <= ?))""",
                        (lease_expires_at, payload_hash, method, path, lease_owner_token, user_id, normalized_key, now_ts)
                    )
                    took_over = _owns_lease(db, user_id, normalized_key, lease_owner_token, "processing")
                if took_over:
                    return None, None, lease_owner_token
            except Exception:
                logger.exception("Unable to take over an expired idempotency lease")
                return None, _database_unavailable(), None

        # Aguardar brevemente (polling de até 1.5s) caso a requisição concorrente esteja finalizando
        for _ in range(15):
            time.sleep(0.1)
            cursor = db.execute(
                "SELECT status, status_code, response_body FROM idempotency_keys WHERE user_id = ? AND key = ?",
                (user_id, normalized_key)
            )
            rows = cursor.fetchall()
            row = rows[0] if rows else None
            cursor.close()
            if row and row["status"] == "completed" and row["response_body"] is not None:
                return Response(row["response_body"], status=row["status_code"] or 200, mimetype="application/json"), None, None

        return None, (jsonify({"error": "Conflict: Operation with this idempotency key is currently processing"}), 409), None

    return None, (jsonify({"error": "Invalid idempotency state"}), 409), None


def complete_idempotency(db, user_id: str, status_code: int, response_data: dict | list, lease_token: str):
    """
    Marca a chave de idempotência como completed gravando atomicamente a resposta.
    """
    key = request.headers.get("X-Idempotency-Key")
    if not key or not is_valid_uuid_v4(key) or not lease_token:
        return

    normalized_key = key.lower()
    response_body = json.dumps(response_data)

    cursor = db.execute(
        """UPDATE idempotency_keys
           SET status = 'completed', status_code = ?, response_body = ?, lease_expires_at = 0
           WHERE user_id = ? AND key = ? AND lease_owner_token = ? AND status = 'processing'""",
        (status_code, response_body, user_id, normalized_key, lease_token)
    )
    cursor.close()

    if not _owns_lease(db, user_id, normalized_key, lease_token, "completed"):
        raise LostLeaseError("Idempotency lease was lost before completion")


def fail_idempotency(db, user_id: str, lease_token: str):
    """
    Libera a chave em caso de falha não-recuperável ou erro interno do servidor.
    """
    key = request.headers.get("X-Idempotency-Key")
    if not key or not is_valid_uuid_v4(key) or not lease_token:
        return False

    with db_transaction(db, immediate=True):
        cursor = db.execute(
            """UPDATE idempotency_keys
               SET status = 'failed', lease_expires_at = 0
               WHERE user_id = ? AND key = ? AND lease_owner_token = ? AND status = 'processing'""",
            (user_id, key.lower(), lease_token)
        )
        cursor.close()
        changed = _owns_lease(db, user_id, key.lower(), lease_token, "failed")
    return changed


def cleanup_idempotency_keys(db, max_age_days: int = 7):
    """
    Limpa chaves antigas concluídas ou falhas para liberar espaço.
    """
    try:
        with db_transaction(db, immediate=True):
            db.execute(
                """DELETE FROM idempotency_keys
                   WHERE (status = 'completed' AND created_at < datetime('now', ?))
                      OR (status = 'failed' AND created_at < datetime('now', '-1 day'))""",
                (f"-{max_age_days} days",)
            )
        return
    except Exception:
        logger.exception("Unable to clean old idempotency keys")
        raise
