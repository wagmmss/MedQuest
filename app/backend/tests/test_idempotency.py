import os
import uuid
import hashlib
import sqlite3
import threading
import time
import pytest
import json
from api import create_app
from api.idempotency import cleanup_idempotency_keys, complete_idempotency, LostLeaseError
from tests.conftest import SCHEMA_AND_SEED

PROXY_SECRET = "super-secret-proxy-token-12345"


@pytest.fixture
def idemp_app(tmp_path, monkeypatch):
    dbfile = tmp_path / "idemp_test.db"
    con = sqlite3.connect(dbfile)
    con.executescript(SCHEMA_AND_SEED)
    con.commit()
    con.close()

    monkeypatch.setenv("MEDQUEST_DB", str(dbfile))
    monkeypatch.setenv("FLASK_API_PROXY_SECRET", PROXY_SECRET)
    monkeypatch.delenv("TURSO_DATABASE_URL", raising=False)
    monkeypatch.delenv("TURSO_AUTH_TOKEN", raising=False)

    app = create_app()
    app.config["TESTING"] = False
    return app


@pytest.fixture
def idemp_client(idemp_app):
    return idemp_app.test_client()


def test_idempotency_invalid_uuid_returns_400(idemp_client):
    guest_id = str(uuid.uuid4())
    headers = {
        "X-Internal-Proxy-Token": PROXY_SECRET,
        "X-Guest-ID": guest_id,
        "X-Idempotency-Key": "not-a-uuid-v4",
    }
    r = idemp_client.post(
        "/api/questions/1/attempt",
        headers=headers,
        json={"selected_letter": "B", "time_spent_ms": 1000, "confidence": "certeza"},
    )
    assert r.status_code == 400
    assert "Invalid X-Idempotency-Key" in r.get_json()["error"]


def test_idempotency_single_attempt_repeated_does_not_duplicate(idemp_client):
    guest_id = str(uuid.uuid4())
    key = str(uuid.uuid4())
    headers = {
        "X-Internal-Proxy-Token": PROXY_SECRET,
        "X-Guest-ID": guest_id,
        "X-Idempotency-Key": key,
    }
    payload = {"selected_letter": "B", "time_spent_ms": 2000, "confidence": "certeza"}

    # 1º envio
    r1 = idemp_client.post("/api/questions/1/attempt", headers=headers, json=payload)
    assert r1.status_code == 200
    data1 = r1.get_json()
    assert data1["is_correct"] is True

    # 2º envio (repetido com mesma chave e mesmo payload)
    r2 = idemp_client.post("/api/questions/1/attempt", headers=headers, json=payload)
    assert r2.status_code == 200
    data2 = r2.get_json()
    assert data1 == data2

    # Verificar que foi gravada exatamente 1 tentativa no banco
    stats = idemp_client.get("/api/stats/overview", headers={"X-Internal-Proxy-Token": PROXY_SECRET, "X-Guest-ID": guest_id})
    assert stats.get_json()["total_attempts"] == 1


def test_idempotency_batch_repeated_does_not_advance_fsrs_twice(idemp_client):
    guest_id = str(uuid.uuid4())
    key = str(uuid.uuid4())
    headers = {
        "X-Internal-Proxy-Token": PROXY_SECRET,
        "X-Guest-ID": guest_id,
        "X-Idempotency-Key": key,
    }
    payload = {
        "attempts": [
            {"question_id": 1, "selected_letter": "B", "confidence": "certeza", "time_spent_ms": 1500},
            {"question_id": 2, "selected_letter": "A", "confidence": "certeza", "time_spent_ms": 1800},
        ]
    }

    # 1º envio do lote
    r1 = idemp_client.post("/api/attempt/batch", headers=headers, json=payload)
    assert r1.status_code == 200
    res1 = r1.get_json()["results"]
    assert len(res1) == 2
    date_q1 = res1[0]["next_review_date"]

    # 2º envio do lote
    r2 = idemp_client.post("/api/attempt/batch", headers=headers, json=payload)
    assert r2.status_code == 200
    res2 = r2.get_json()["results"]
    assert res1 == res2
    assert res2[0]["next_review_date"] == date_q1

    # Total de tentativas registradas deve ser exatamente 2
    stats = idemp_client.get("/api/stats/overview", headers={"X-Internal-Proxy-Token": PROXY_SECRET, "X-Guest-ID": guest_id})
    assert stats.get_json()["total_attempts"] == 2


def test_idempotency_mismatched_payload_returns_409(idemp_client):
    guest_id = str(uuid.uuid4())
    key = str(uuid.uuid4())
    headers = {
        "X-Internal-Proxy-Token": PROXY_SECRET,
        "X-Guest-ID": guest_id,
        "X-Idempotency-Key": key,
    }

    # 1º envio com letra B
    r1 = idemp_client.post(
        "/api/questions/1/attempt",
        headers=headers,
        json={"selected_letter": "B", "time_spent_ms": 1000, "confidence": "certeza"},
    )
    assert r1.status_code == 200

    # 2º envio com mesma chave mas letra C
    r2 = idemp_client.post(
        "/api/questions/1/attempt",
        headers=headers,
        json={"selected_letter": "C", "time_spent_ms": 1000, "confidence": "certeza"},
    )
    assert r2.status_code == 409
    assert "Conflict" in r2.get_json()["error"]


def test_idempotency_different_users_same_key_are_isolated(idemp_client):
    user_a = str(uuid.uuid4())
    user_b = str(uuid.uuid4())
    shared_key = str(uuid.uuid4())

    # Usuário A responde B
    r_a = idemp_client.post(
        "/api/questions/1/attempt",
        headers={"X-Internal-Proxy-Token": PROXY_SECRET, "X-Guest-ID": user_a, "X-Idempotency-Key": shared_key},
        json={"selected_letter": "B", "time_spent_ms": 1000, "confidence": "certeza"},
    )
    assert r_a.status_code == 200
    assert r_a.get_json()["is_correct"] is True

    # Usuário B responde C com a mesma chave (mas escopo de usuário diferente)
    r_b = idemp_client.post(
        "/api/questions/1/attempt",
        headers={"X-Internal-Proxy-Token": PROXY_SECRET, "X-Guest-ID": user_b, "X-Idempotency-Key": shared_key},
        json={"selected_letter": "C", "time_spent_ms": 1000, "confidence": "certeza"},
    )
    assert r_b.status_code == 200
    assert r_b.get_json()["is_correct"] is False


def test_concurrent_identical_requests_single_attempt(idemp_app):
    """
    Dispara duas requisições paralelas e concorrentes usando uma barreira de sincronização
    com a mesma chave e payload. Ambas devem retornar 200 com resultado idêntico, e o banco
    deve registrar EXATAMENTE 1 tentativa e 1 avanço FSRS.
    """
    guest_id = str(uuid.uuid4())
    key = str(uuid.uuid4())
    headers = {
        "X-Internal-Proxy-Token": PROXY_SECRET,
        "X-Guest-ID": guest_id,
        "X-Idempotency-Key": key,
    }
    payload = {"selected_letter": "B", "time_spent_ms": 2000, "confidence": "certeza"}

    barrier = threading.Barrier(2)
    results = [None, None]
    status_codes = [None, None]

    def worker(idx):
        client = idemp_app.test_client()
        barrier.wait()
        res = client.post("/api/questions/1/attempt", headers=headers, json=payload)
        status_codes[idx] = res.status_code
        results[idx] = res.get_json()

    t1 = threading.Thread(target=worker, args=(0,))
    t2 = threading.Thread(target=worker, args=(1,))

    t1.start()
    t2.start()
    t1.join(timeout=10)
    t2.join(timeout=10)

    assert status_codes[0] == 200
    assert status_codes[1] == 200
    assert results[0] == results[1]
    assert results[0]["is_correct"] is True

    # Verificar que o DB tem exatamente 1 tentativa para o usuário
    client = idemp_app.test_client()
    stats = client.get("/api/stats/overview", headers={"X-Internal-Proxy-Token": PROXY_SECRET, "X-Guest-ID": guest_id})
    assert stats.get_json()["total_attempts"] == 1


def test_concurrent_conflicting_payloads_same_key(idemp_app):
    """
    Dispara duas requisições simultâneas com a mesma chave mas payloads conflitantes.
    Exatamente uma deve vencer (200) e a outra deve receber 409 Conflict.
    """
    guest_id = str(uuid.uuid4())
    key = str(uuid.uuid4())
    headers = {
        "X-Internal-Proxy-Token": PROXY_SECRET,
        "X-Guest-ID": guest_id,
        "X-Idempotency-Key": key,
    }

    barrier = threading.Barrier(2)
    status_codes = [None, None]

    def worker(idx, letter):
        client = idemp_app.test_client()
        barrier.wait()
        res = client.post(
            "/api/questions/1/attempt",
            headers=headers,
            json={"selected_letter": letter, "time_spent_ms": 1000, "confidence": "certeza"},
        )
        status_codes[idx] = res.status_code

    t1 = threading.Thread(target=worker, args=(0, "B"))
    t2 = threading.Thread(target=worker, args=(1, "C"))

    t1.start()
    t2.start()
    t1.join(timeout=10)
    t2.join(timeout=10)

    # Um deve ser 200 e o outro 409
    assert sorted(status_codes) == [200, 409]

    # Verificar total de tentativas no banco
    client = idemp_app.test_client()
    stats = client.get("/api/stats/overview", headers={"X-Internal-Proxy-Token": PROXY_SECRET, "X-Guest-ID": guest_id})
    assert stats.get_json()["total_attempts"] == 1


def test_lease_expiration_and_recovery(idemp_app):
    """
    Simula uma requisição que falhou/travou deixando status 'processing' com lease expirado.
    Uma nova tentativa com mesma chave e payload deve recuperar o lease e concluir a operação.
    """
    guest_id = str(uuid.uuid4())
    key = str(uuid.uuid4())
    headers = {
        "X-Internal-Proxy-Token": PROXY_SECRET,
        "X-Guest-ID": guest_id,
        "X-Idempotency-Key": key,
    }
    payload = {"selected_letter": "B", "time_spent_ms": 1500, "confidence": "certeza"}
    raw_body = json.dumps(payload).encode("utf-8")
    payload_hash = hashlib.sha256(raw_body).hexdigest()

    # Inserir manualmente uma chave abandonada com lease expirado (no passado)
    with idemp_app.app_context():
        from api.db import get_db
        db = get_db()
        expired_ts = time.time() - 60.0
        db.execute(
            """INSERT INTO idempotency_keys (user_id, key, method, path, payload_hash, status, lease_expires_at, created_at)
               VALUES (?, ?, 'POST', '/api/questions/1/attempt', ?, 'processing', ?, '2026-01-01T00:00:00')""",
            (f"guest:{guest_id}", key.lower(), payload_hash, expired_ts)
        )
        db.commit()

    # O cliente tenta enviar novamente -> deve recuperar o lease expirado e ter sucesso 200
    client = idemp_app.test_client()
    r = client.post("/api/questions/1/attempt", headers=headers, data=raw_body, content_type="application/json")
    assert r.status_code == 200
    assert r.get_json()["is_correct"] is True

    # Confirmar status final no banco
    with idemp_app.app_context():
        from api.db import get_db
        db = get_db()
        row = db.execute("SELECT status, status_code FROM idempotency_keys WHERE user_id = ? AND key = ?", (f"guest:{guest_id}", key.lower())).fetchone()
        assert row["status"] == "completed"
        assert row["status_code"] == 200


def test_cleanup_idempotency_keys(idemp_app):
    """
    Testa a função de limpeza excluindo chaves antigas.
    """
    with idemp_app.app_context():
        from api.db import get_db
        db = get_db()
        old_completed = str(uuid.uuid4())
        old_failed = str(uuid.uuid4())
        recent_completed = str(uuid.uuid4())

        db.execute(
            """INSERT INTO idempotency_keys (user_id, key, method, path, payload_hash, status, status_code, lease_expires_at, created_at)
               VALUES ('u1', ?, 'POST', '/api/test', 'hash1', 'completed', 200, 0, datetime('now', '-10 days'))""",
            (old_completed,)
        )
        db.execute(
            """INSERT INTO idempotency_keys (user_id, key, method, path, payload_hash, status, status_code, lease_expires_at, created_at)
               VALUES ('u1', ?, 'POST', '/api/test', 'hash2', 'failed', 500, 0, datetime('now', '-2 days'))""",
            (old_failed,)
        )
        db.execute(
            """INSERT INTO idempotency_keys (user_id, key, method, path, payload_hash, status, status_code, lease_expires_at, created_at)
               VALUES ('u1', ?, 'POST', '/api/test', 'hash3', 'completed', 200, 0, datetime('now', '-1 hour'))""",
            (recent_completed,)
        )
        db.commit()

        cleanup_idempotency_keys(db, max_age_days=7)

        assert db.execute("SELECT 1 FROM idempotency_keys WHERE key = ?", (old_completed,)).fetchone() is None
        assert db.execute("SELECT 1 FROM idempotency_keys WHERE key = ?", (old_failed,)).fetchone() is None
        assert db.execute("SELECT 1 FROM idempotency_keys WHERE key = ?", (recent_completed,)).fetchone() is not None


def test_failed_reservation_can_be_recovered(idemp_app):
    guest_id = str(uuid.uuid4())
    key = str(uuid.uuid4())
    payload = {"selected_letter": "B", "time_spent_ms": 1500, "confidence": "certeza"}
    raw_body = json.dumps(payload).encode("utf-8")

    with idemp_app.app_context():
        from api.db import get_db
        db = get_db()
        db.execute(
            """INSERT INTO idempotency_keys
               (user_id, key, method, path, payload_hash, status, lease_expires_at, created_at)
               VALUES (?, ?, 'POST', '/api/questions/1/attempt', ?, 'failed', 0, ?)""",
            (
                f"guest:{guest_id}",
                key,
                hashlib.sha256(raw_body).hexdigest(),
                "2026-01-01T00:00:00+00:00",
            ),
        )
        db.commit()

    response = idemp_app.test_client().post(
        "/api/questions/1/attempt",
        headers={
            "X-Internal-Proxy-Token": PROXY_SECRET,
            "X-Guest-ID": guest_id,
            "X-Idempotency-Key": key,
        },
        data=raw_body,
        content_type="application/json",
    )
    assert response.status_code == 200

    with idemp_app.app_context():
        from api.db import get_db
        db = get_db()
        assert db.execute(
            "SELECT COUNT(*) AS total FROM attempts WHERE user_id = ?",
            (f"guest:{guest_id}",),
        ).fetchone()["total"] == 1


def test_lost_lease_rolls_back_protected_effect(idemp_app):
    guest_id = str(uuid.uuid4())
    user_id = f"guest:{guest_id}"
    key = str(uuid.uuid4())
    old_token = str(uuid.uuid4())
    new_token = str(uuid.uuid4())

    with idemp_app.test_request_context(headers={"X-Idempotency-Key": key}):
        from api.db import get_db, db_transaction
        db = get_db()
        db.execute(
            """INSERT INTO idempotency_keys
               (user_id, key, method, path, payload_hash, status, lease_expires_at, lease_owner_token, created_at)
               VALUES (?, ?, 'POST', '/api/questions/1/attempt', 'hash', 'processing', ?, ?, ?)""",
            (user_id, key, time.time() + 30, new_token, "2026-01-01T00:00:00+00:00"),
        )
        db.commit()

        with pytest.raises(LostLeaseError):
            with db_transaction(db, immediate=True):
                db.execute(
                    """INSERT INTO attempts
                       (question_id, selected_letter, is_correct, answered_at, confidence, user_id)
                       VALUES (1, 'B', 1, 'now', 'certeza', ?)""",
                    (user_id,),
                )
                db.execute(
                    """INSERT INTO spaced_repetition
                       (question_id, next_review_date, fsrs_card, user_id)
                       VALUES (1, 'tomorrow', '{}', ?)""",
                    (user_id,),
                )
                complete_idempotency(db, user_id, 200, {"ok": True}, old_token)

        assert db.execute(
            "SELECT COUNT(*) AS total FROM attempts WHERE user_id = ?", (user_id,)
        ).fetchone()["total"] == 0
        assert db.execute(
            "SELECT 1 FROM spaced_repetition WHERE user_id = ?", (user_id,)
        ).fetchone() is None
        row = db.execute(
            "SELECT status, lease_owner_token FROM idempotency_keys WHERE user_id = ? AND key = ?",
            (user_id, key),
        ).fetchone()
        assert row["status"] == "processing"
        assert row["lease_owner_token"] == new_token


def test_empty_batch_response_is_cached(idemp_client):
    guest_id = str(uuid.uuid4())
    key = str(uuid.uuid4())
    headers = {
        "X-Internal-Proxy-Token": PROXY_SECRET,
        "X-Guest-ID": guest_id,
        "X-Idempotency-Key": key,
    }
    first = idemp_client.post("/api/attempt/batch", headers=headers, json={"attempts": []})
    second = idemp_client.post("/api/attempt/batch", headers=headers, json={"attempts": []})
    assert first.status_code == second.status_code == 200
    assert first.get_json() == second.get_json() == {"results": []}


def test_favorite_toggle_replay_does_not_toggle_back(idemp_client):
    guest_id = str(uuid.uuid4())
    key = str(uuid.uuid4())
    headers = {
        "X-Internal-Proxy-Token": PROXY_SECRET,
        "X-Guest-ID": guest_id,
        "X-Idempotency-Key": key,
    }
    first = idemp_client.post("/api/questions/1/favorite", headers=headers, json={})
    second = idemp_client.post("/api/questions/1/favorite", headers=headers, json={})
    assert first.status_code == second.status_code == 200
    assert first.get_json() == second.get_json()
    assert second.get_json()["is_favorite"] is True


def test_review_replay_advances_fsrs_only_once(idemp_client):
    guest_id = str(uuid.uuid4())
    base_headers = {
        "X-Internal-Proxy-Token": PROXY_SECRET,
        "X-Guest-ID": guest_id,
    }
    attempt_headers = {**base_headers, "X-Idempotency-Key": str(uuid.uuid4())}
    attempt = idemp_client.post(
        "/api/questions/1/attempt",
        headers=attempt_headers,
        json={"selected_letter": "B", "time_spent_ms": 1000, "confidence": "defer"},
    )
    assert attempt.status_code == 200

    review_headers = {**base_headers, "X-Idempotency-Key": str(uuid.uuid4())}
    first = idemp_client.post(
        "/api/questions/1/review", headers=review_headers, json={"confidence": "certeza"}
    )
    second = idemp_client.post(
        "/api/questions/1/review", headers=review_headers, json={"confidence": "certeza"}
    )
    assert first.status_code == second.status_code == 200
    assert first.get_json() == second.get_json()
