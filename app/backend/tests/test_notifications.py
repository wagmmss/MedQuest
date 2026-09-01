"""Testes herméticos para Notificações PWA Opt-in e Disparo de Lembretes FSRS."""

from datetime import datetime, timezone
import json
import os
import pytest
from flask import g
import requests
from requests.adapters import HTTPAdapter
from urllib3.response import HTTPResponse
import io

from api import create_app
from api.db import db_transaction, get_db
from api.webpush import (
    NoRedirectSession,
    is_safe_push_endpoint,
    send_web_push,
    set_mock_webpush_sender,
)


@pytest.fixture(autouse=True)
def cleanup_mock_sender():
    """Garante limpeza do mock sender antes e depois de cada teste."""
    set_mock_webpush_sender(None)
    yield
    set_mock_webpush_sender(None)


def test_endpoint_ssrf_allowlist_and_deceptive_domains(monkeypatch):
    """Valida proteção SSRF por allowlist explícita e rejeição de domínios enganosos."""
    monkeypatch.setenv(
        "WEB_PUSH_ALLOWED_HOSTS",
        "fcm.googleapis.com,*.push.services.mozilla.com,push.services.mozilla.com,*.push.apple.com,web.push.apple.com",
    )

    # 1. Rejeição de URLs não-HTTPS e IPs privados/localhost
    assert not is_safe_push_endpoint("http://fcm.googleapis.com/fcm/send/abc")
    assert not is_safe_push_endpoint("https://localhost/push")
    assert not is_safe_push_endpoint("https://127.0.0.1:8080/push")
    assert not is_safe_push_endpoint("https://192.168.1.1/push")
    assert not is_safe_push_endpoint("https://10.0.0.5/push")
    assert not is_safe_push_endpoint("https://169.254.169.254/latest/meta-data")
    assert not is_safe_push_endpoint("https://internal.service.local/push")

    # 2. Rejeição de domínios enganosos (prefix/suffix collision)
    assert not is_safe_push_endpoint("https://fcm.googleapis.com.evil.example/push")
    assert not is_safe_push_endpoint("https://evil-fcm.googleapis.com/push")
    assert not is_safe_push_endpoint("https://updates.push.services.mozilla.com.attacker.io/wpush")
    assert not is_safe_push_endpoint("https://web.push.apple.com.fake.com/push")
    assert not is_safe_push_endpoint("https://untrusted-push-server.com/endpoint")

    # 3. Aceitação de domínios legítimos configurados
    assert is_safe_push_endpoint("https://fcm.googleapis.com/fcm/send/token123")
    assert is_safe_push_endpoint("https://updates.push.services.mozilla.com/wpush/v2/token123")
    assert is_safe_push_endpoint("https://dom.push.services.mozilla.com/wpush/v2/token123")
    assert is_safe_push_endpoint("https://web.push.apple.com/token123")
    assert is_safe_push_endpoint("https://api.push.apple.com/token123")


def test_ssrf_allowlist_in_production_fails_closed(monkeypatch):
    """Garante que em produção (FLASK_ENV=production), sem WEB_PUSH_ALLOWED_HOSTS, o envio falhe fechado."""
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.delenv("WEB_PUSH_ALLOWED_HOSTS", raising=False)

    # Nenhum host deve ser aceito
    assert not is_safe_push_endpoint("https://fcm.googleapis.com/fcm/send/token123")
    assert not is_safe_push_endpoint("https://updates.push.services.mozilla.com/wpush")

    # send_web_push deve falhar antes de tentar qualquer envio
    res = send_web_push(
        {"endpoint": "https://fcm.googleapis.com/fcm/send/token123"},
        {"title": "Teste"},
    )
    assert res["status"] == "failed"
    assert res["delivered"] is False
    assert "allowlist" in res["error"].lower()


def test_sender_not_called_for_disallowed_host():
    """Garante que endpoints em hosts não permitidos sejam rejeitados antes de invocar o sender mockado."""
    mock_called = False

    def mock_sender(sub, payload):
        nonlocal mock_called
        mock_called = True
        return {"status": "delivered", "delivered": True}

    set_mock_webpush_sender(mock_sender)

    res = send_web_push(
        {"endpoint": "https://attacker-controlled-host.com/ssrf_target"},
        {"title": "Teste"},
    )
    assert res["status"] == "failed"
    assert res["delivered"] is False
    assert not mock_called  # Sender mockado NÃO foi invocado


def test_host_allowed_reaches_mocked_sender():
    """Garante que hosts permitidos passem na validação e alcancem o sender mockado."""
    mock_called = False

    def mock_sender(sub, payload):
        nonlocal mock_called
        mock_called = True
        return {"status": "delivered", "delivered": True}

    set_mock_webpush_sender(mock_sender)

    res = send_web_push(
        {"endpoint": "https://fcm.googleapis.com/fcm/send/valid_token"},
        {"title": "Teste"},
    )
    assert res["status"] == "delivered"
    assert mock_called is True


def test_no_redirect_session_enforces_allow_redirects_false():
    """Garante que NoRedirectSession desativa seguimento automático de redirecionamentos (3xx)."""
    session = NoRedirectSession()

    class Mock302Adapter(HTTPAdapter):
        def send(self, request, **kwargs):
            resp = requests.Response()
            resp.status_code = 302
            resp.headers["Location"] = "https://evil.internal.service/leak"
            resp.raw = io.BytesIO(b"Redirect")
            resp.url = request.url
            return resp

    session.mount("https://", Mock302Adapter())
    resp = session.post("https://fcm.googleapis.com/test", allow_redirects=True)
    # Status deve ser 302 direto sem ter seguido para a URL de Location e sem histórico
    assert resp.status_code == 302
    assert resp.headers["Location"] == "https://evil.internal.service/leak"
    assert len(resp.history) == 0


def test_notification_config_get_and_update(client):
    """Valida obtenção e atualização das preferências de notificação do usuário."""
    # Obter configuração inicial padrão
    res = client.get("/api/notifications/config")
    assert res.status_code == 200
    data = res.get_json()
    assert data["enabled"] is False
    assert data["preferred_hour"] == 8
    assert data["days_of_week"] == [0, 1, 2, 3, 4, 5, 6]
    assert data["has_active_subscription"] is False

    # Atualizar preferências
    update_res = client.put(
        "/api/notifications/config",
        json={
            "enabled": True,
            "preferred_hour": 20,
            "days_of_week": [0, 2, 4],
            "max_daily_reminders": 1,
        },
    )
    assert update_res.status_code == 200
    updated = update_res.get_json()
    assert updated["enabled"] is True
    assert updated["preferred_hour"] == 20
    assert updated["days_of_week"] == [0, 2, 4]

    # Obter novamente e confirmar persistência
    res2 = client.get("/api/notifications/config")
    assert res2.status_code == 200
    data2 = res2.get_json()
    assert data2["enabled"] is True
    assert data2["preferred_hour"] == 20
    assert data2["days_of_week"] == [0, 2, 4]


def test_max_daily_reminders_strict_constraint(client):
    """Garante que a API rejeita qualquer valor de max_daily_reminders diferente de 1."""
    res_invalid = client.put(
        "/api/notifications/config",
        json={
            "enabled": True,
            "preferred_hour": 8,
            "days_of_week": [0, 1, 2],
            "max_daily_reminders": 5,
        },
    )
    assert res_invalid.status_code == 400


def test_push_subscription_lifecycle(client):
    """Valida registro, idempotência de endpoint e revogação de assinaturas Web Push."""
    sub_payload = {
        "endpoint": "https://updates.push.services.mozilla.com/wpush/v2/test_endpoint_123",
        "keys": {
            "p256dh": "BNcRdreALRFXTkOOUHK1EtK2wtaz5Ry4YfYCA_0QT9t0A4If7q",
            "auth": "tBHItJI5svbpez7KI4CCXg",
        },
    }

    # Inscrição
    res = client.post("/api/notifications/subscribe", json=sub_payload)
    assert res.status_code == 200
    assert res.get_json()["success"] is True

    # Confirmar que a configuração agora reporta subscription ativa
    cfg = client.get("/api/notifications/config").get_json()
    assert cfg["has_active_subscription"] is True
    assert cfg["enabled"] is True

    # Re-inscrição do mesmo endpoint (idempotente/upsert sem duplicação)
    res_dup = client.post("/api/notifications/subscribe", json=sub_payload)
    assert res_dup.status_code == 200

    # Revogação por endpoint específico
    del_res = client.delete(
        "/api/notifications/subscribe",
        json={"endpoint": "https://updates.push.services.mozilla.com/wpush/v2/test_endpoint_123"},
    )
    assert del_res.status_code == 200
    assert del_res.get_json()["success"] is True

    # Confirmar remoção
    cfg_after = client.get("/api/notifications/config").get_json()
    assert cfg_after["has_active_subscription"] is False


def test_multi_user_isolation(app):
    """Garante que preferências e subscriptions de um usuário nunca sejam acessíveis por outro."""
    client_a = app.test_client()
    client_b = app.test_client()

    # Contexto do Usuário A
    with app.test_request_context():
        g.user_id = "user_alpha_1"
        res_a = client_a.put(
            "/api/notifications/config",
            json={"enabled": True, "preferred_hour": 14, "days_of_week": [1, 3], "max_daily_reminders": 1},
        )
        assert res_a.status_code == 200

        sub_res = client_a.post(
            "/api/notifications/subscribe",
            json={
                "endpoint": "https://fcm.googleapis.com/fcm/send/user_alpha_sub",
                "keys": {"p256dh": "key_a", "auth": "auth_a"},
            },
        )
        assert sub_res.status_code == 200

    # Contexto do Usuário B (não deve ver nem ser afetado pelos dados do Usuário A)
    with app.test_request_context():
        g.user_id = "user_beta_2"
        res_b = client_b.get("/api/notifications/config")
        data_b = res_b.get_json()
        assert data_b["enabled"] is False  # Padrão para novo usuário
        assert data_b["has_active_subscription"] is False

        # Tentativa de revogar endpoint do Usuário A a partir do Usuário B (não deve afetar Usuário A)
        del_b = client_b.delete(
            "/api/notifications/subscribe",
            json={"endpoint": "https://fcm.googleapis.com/fcm/send/user_alpha_sub"},
        )
        assert del_b.status_code == 200

    # Verificar que Usuário A continua intacto
    with app.test_request_context():
        g.user_id = "user_alpha_1"
        res_a_check = client_a.get("/api/notifications/config")
        assert res_a_check.get_json()["has_active_subscription"] is True
        assert res_a_check.get_json()["preferred_hour"] == 14


def test_cron_dispatch_auth_in_non_testing_mode(tmp_path, monkeypatch):
    """Valida autenticação em modo de produção (TESTING=False): cron tem auth própria e outras rotas continuam protegidas."""
    cron_secret = "prod_cron_secret_789"
    monkeypatch.setenv("NOTIFICATIONS_CRON_SECRET", cron_secret)

    dbfile = tmp_path / "medquest_nontest.db"
    monkeypatch.setenv("MEDQUEST_DB", str(dbfile))

    # Cria app explicitamente sem testing mode
    app = create_app(testing=False)
    client = app.test_client()

    # 1. Cron sem segredo -> 401
    res_no_sec = client.post("/api/notifications/cron/dispatch")
    assert res_no_sec.status_code == 401

    # 2. Cron com segredo inválido -> 401
    res_bad_sec = client.post(
        "/api/notifications/cron/dispatch",
        headers={"X-Cron-Secret": "invalid_secret"},
    )
    assert res_bad_sec.status_code == 401

    # 3. Cron com segredo válido -> 200 (alcança o handler e executa com sucesso)
    res_ok = client.post(
        "/api/notifications/cron/dispatch",
        headers={"X-Cron-Secret": cron_secret},
    )
    assert res_ok.status_code == 200
    assert res_ok.get_json()["success"] is True

    # 4. Outras rotas da API continuam 100% protegidas e retornam 401 sem JWT/proxy token
    res_stats = client.get("/api/stats/overview")
    assert res_stats.status_code == 401

    res_notif_cfg = client.get("/api/notifications/config")
    assert res_notif_cfg.status_code == 401


def test_cron_dispatch_atomic_reservation_and_concurrency(app, monkeypatch):
    """Garante que sob concorrência apenas 1 worker reserva o dispatch e dispara a notificação."""
    cron_secret = "test_atomic_cron"
    monkeypatch.setenv("NOTIFICATIONS_CRON_SECRET", cron_secret)

    sender_invocation_count = 0

    def mock_sender(sub, payload):
        nonlocal sender_invocation_count
        sender_invocation_count += 1
        return {"status": "delivered", "delivered": True, "status_code": 201, "error": None}

    set_mock_webpush_sender(mock_sender)

    today_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    with app.app_context():
        db = get_db()
        with db_transaction(db, immediate=True):
            db.execute(
                """
                INSERT INTO notification_configs (user_id, enabled, preferred_hour, days_of_week, max_daily_reminders, updated_at)
                VALUES ('user_race', 1, 8, '[0,1,2,3,4,5,6]', 1, ?)
                ON CONFLICT(user_id) DO UPDATE SET enabled=1
                """,
                (today_date,),
            )
            db.execute(
                """
                INSERT INTO push_subscriptions (user_id, endpoint, p256dh, auth, created_at)
                VALUES ('user_race', 'https://fcm.googleapis.com/fcm/send/race_sub', 'k', 'a', ?)
                ON CONFLICT(user_id, endpoint) DO NOTHING
                """,
                (today_date,),
            )
            db.execute(
                """
                INSERT INTO flashcards (question_id, front, back, created_at, next_review_date, user_id)
                VALUES (10, 'Frente', 'Verso', ?, ?, 'user_race')
                """,
                (today_date, today_date),
            )

    client1 = app.test_client()
    client2 = app.test_client()

    # Execução 1: ganha a reserva
    res1 = client1.post(
        "/api/notifications/cron/dispatch",
        headers={"X-Cron-Secret": cron_secret},
        json={"force_user_id": "user_race", "ignore_hour": True},
    )
    assert res1.status_code == 200
    assert res1.get_json()["dispatched_count"] == 1

    # Execução 2: encontra a reserva atômica já ocupada e pula sem invocar o sender
    res2 = client2.post(
        "/api/notifications/cron/dispatch",
        headers={"X-Cron-Secret": cron_secret},
        json={"force_user_id": "user_race", "ignore_hour": True},
    )
    assert res2.status_code == 200
    assert res2.get_json()["dispatched_count"] == 0
    assert res2.get_json()["skipped_already_dispatched"] == 1

    # Confirma que o sender foi chamado EXATAMENTE 1 vez
    assert sender_invocation_count == 1


def test_cron_dispatch_stale_subscription_pruning(app, client, monkeypatch):
    """Garante que subscrições que retornam 410 Gone / expired sejam limpas automaticamente."""
    cron_secret = "test_cron_secret_prune"
    monkeypatch.setenv("NOTIFICATIONS_CRON_SECRET", cron_secret)

    def mock_expired_sender(sub, payload):
        return {"status": "expired", "delivered": False, "status_code": 410, "error": "Subscription expired"}

    set_mock_webpush_sender(mock_expired_sender)

    today_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    with app.app_context():
        db = get_db()
        with db_transaction(db, immediate=True):
            db.execute(
                """
                INSERT INTO notification_configs (user_id, enabled, preferred_hour, days_of_week, max_daily_reminders, updated_at)
                VALUES ('user_stale', 1, 8, '[0,1,2,3,4,5,6]', 1, ?)
                ON CONFLICT(user_id) DO UPDATE SET enabled=1
                """,
                (today_date,),
            )
            db.execute(
                """
                INSERT INTO push_subscriptions (user_id, endpoint, p256dh, auth, created_at)
                VALUES ('user_stale', 'https://fcm.googleapis.com/fcm/send/stale_sub', 'k', 'a', ?)
                ON CONFLICT(user_id, endpoint) DO NOTHING
                """,
                (today_date,),
            )
            db.execute(
                """
                INSERT INTO flashcards (question_id, front, back, created_at, next_review_date, user_id)
                VALUES (2, 'Frente Stale', 'Verso Stale', ?, ?, 'user_stale')
                """,
                (today_date, today_date),
            )

    res = client.post(
        "/api/notifications/cron/dispatch",
        headers={"X-Cron-Secret": cron_secret},
        json={"force_user_id": "user_stale", "ignore_hour": True},
    )
    assert res.status_code == 200

    # Verificar se a subscription foi excluída do banco
    with app.app_context():
        db = get_db()
        sub = db.execute(
            "SELECT 1 FROM push_subscriptions WHERE user_id = 'user_stale' AND endpoint = 'https://fcm.googleapis.com/fcm/send/stale_sub'"
        ).fetchone()
        assert sub is None


def test_cron_dispatch_vapid_absent_fail_safe(app, client, monkeypatch):
    """Garante que o cron opera de modo seguro e sem exceções quando chaves VAPID estão ausentes."""
    cron_secret = "test_cron_secret_vapid_none"
    monkeypatch.setenv("NOTIFICATIONS_CRON_SECRET", cron_secret)
    monkeypatch.delenv("VAPID_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("NEXT_PUBLIC_VAPID_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("VAPID_PRIVATE_KEY", raising=False)

    today_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    with app.app_context():
        db = get_db()
        with db_transaction(db, immediate=True):
            db.execute(
                """
                INSERT INTO notification_configs (user_id, enabled, preferred_hour, days_of_week, max_daily_reminders, updated_at)
                VALUES ('user_vapid_test', 1, 8, '[0,1,2,3,4,5,6]', 1, ?)
                ON CONFLICT(user_id) DO UPDATE SET enabled=1
                """,
                (today_date,),
            )
            db.execute(
                """
                INSERT INTO push_subscriptions (user_id, endpoint, p256dh, auth, created_at)
                VALUES ('user_vapid_test', 'https://fcm.googleapis.com/fcm/send/endpoint_vapid', 'k', 'a', ?)
                ON CONFLICT(user_id, endpoint) DO NOTHING
                """,
                (today_date,),
            )
            db.execute(
                """
                INSERT INTO flashcards (question_id, front, back, created_at, next_review_date, user_id)
                VALUES (3, 'Frente', 'Verso', ?, ?, 'user_vapid_test')
                """,
                (today_date, today_date),
            )

    # Executar sem mock (testando o fallback de webpush.py diretamente)
    res = client.post(
        "/api/notifications/cron/dispatch",
        headers={"X-Cron-Secret": cron_secret},
        json={"force_user_id": "user_vapid_test", "ignore_hour": True},
    )
    assert res.status_code == 200
    assert res.get_json()["success"] is True
