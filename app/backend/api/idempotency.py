import hashlib
import json
import time
from datetime import datetime, timezone
import sqlite3
from flask import request, jsonify, Response
from .auth import is_valid_uuid_v4


LEASE_DURATION_SECONDS = 30.0


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

    # 1. Tentar inserção atômica com status 'processing'
    try:
        db.execute(
            """INSERT INTO idempotency_keys (user_id, key, method, path, payload_hash, status, status_code, response_body, lease_expires_at, created_at)
               VALUES (?, ?, ?, ?, ?, 'processing', NULL, NULL, ?, ?)""",
            (user_id, normalized_key, method, path, payload_hash, lease_expires_at, created_at)
        )
        db.commit()
        return None, None, normalized_key
    except (sqlite3.IntegrityError, Exception):
        # Chave já existe ou conflito concorrente de inserção
        pass

    # 2. Investigar o registro existente
    existing = db.execute(
        "SELECT status, method, path, payload_hash, status_code, response_body, lease_expires_at FROM idempotency_keys WHERE user_id = ? AND key = ?",
        (user_id, normalized_key)
    ).fetchone()

    if not existing:
        # Se foi removido por concorrência/cleanup, tenta inserir novamente
        try:
            db.execute(
                """INSERT INTO idempotency_keys (user_id, key, method, path, payload_hash, status, status_code, response_body, lease_expires_at, created_at)
                   VALUES (?, ?, ?, ?, ?, 'processing', NULL, NULL, ?, ?)""",
                (user_id, normalized_key, method, path, payload_hash, lease_expires_at, created_at)
            )
            db.commit()
            return None, None, normalized_key
        except Exception:
            return None, (jsonify({"error": "Concurrent idempotency conflict"}), 409), None

    # Verificar divergência de rota, método ou payload
    if (existing["payload_hash"] != payload_hash or 
        existing["path"] != path or 
        existing["method"] != method):
        return None, (jsonify({"error": "Conflict: X-Idempotency-Key already used with different payload or route"}), 409), None

    # Se já foi concluída com sucesso
    if existing["status"] == "completed" and existing["response_body"] is not None:
        return Response(existing["response_body"], status=existing["status_code"] or 200, mimetype="application/json"), None, None

    # Se está em 'processing'
    if existing["status"] == "processing":
        current_lease = existing["lease_expires_at"] or 0
        if now_ts > current_lease:
            # Lease expirado -> tentativa de recuperação atômica
            try:
                cur = db.execute(
                    """UPDATE idempotency_keys 
                       SET status = 'processing', lease_expires_at = ?, payload_hash = ?, method = ?, path = ?
                       WHERE user_id = ? AND key = ? AND status = 'processing' AND lease_expires_at <= ?""",
                    (lease_expires_at, payload_hash, method, path, user_id, normalized_key, current_lease)
                )
                db.commit()
                # Se atualizou 1 linha, venceu o lease abandonado
                if getattr(cur, "rowcount", 0) > 0 or getattr(cur, "lastrowid", None) is not None:
                    return None, None, normalized_key
            except Exception:
                pass

        # Aguardar brevemente (polling de até 1.5s) caso a requisição concorrente esteja finalizando
        for _ in range(15):
            time.sleep(0.1)
            row = db.execute(
                "SELECT status, status_code, response_body FROM idempotency_keys WHERE user_id = ? AND key = ?",
                (user_id, normalized_key)
            ).fetchone()
            if row and row["status"] == "completed" and row["response_body"] is not None:
                return Response(row["response_body"], status=row["status_code"] or 200, mimetype="application/json"), None, None

        return None, (jsonify({"error": "Conflict: Operation with this idempotency key is currently processing"}), 409), None

    return None, None, normalized_key


def complete_idempotency(db, user_id: str, status_code: int, response_data: dict | list):
    """
    Marca a chave de idempotência como completed gravando atomicamente a resposta.
    """
    key = request.headers.get("X-Idempotency-Key")
    if not key or not is_valid_uuid_v4(key):
        return

    normalized_key = key.lower()
    response_body = json.dumps(response_data)

    db.execute(
        """UPDATE idempotency_keys
           SET status = 'completed', status_code = ?, response_body = ?, lease_expires_at = 0
           WHERE user_id = ? AND key = ? AND status = 'processing'""",
        (status_code, response_body, user_id, normalized_key)
    )


def fail_idempotency(db, user_id: str, key: str):
    """
    Libera a chave em caso de falha não-recuperável ou erro interno do servidor.
    """
    if not key:
        return
    try:
        db.execute(
            "UPDATE idempotency_keys SET status = 'failed', lease_expires_at = 0 WHERE user_id = ? AND key = ?",
            (user_id, key.lower())
        )
        db.commit()
    except Exception:
        pass


def cleanup_idempotency_keys(db, max_age_days: int = 7):
    """
    Limpa chaves antigas concluídas ou falhas para liberar espaço.
    """
    try:
        db.execute(
            """DELETE FROM idempotency_keys 
               WHERE (status = 'completed' AND created_at < datetime('now', ?))
                  OR (status = 'failed' AND created_at < datetime('now', '-1 day'))""",
            (f"-{max_age_days} days",)
        )
        db.commit()
    except Exception:
        pass
