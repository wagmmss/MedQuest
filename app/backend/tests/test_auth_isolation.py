import sqlite3
import uuid
from types import SimpleNamespace

import pytest

from api import create_app
from tests.conftest import SCHEMA_AND_SEED

PROXY_SECRET = "super-secret-proxy-token-12345"


@pytest.fixture
def auth_client(tmp_path, monkeypatch):
    dbfile = tmp_path / "auth_test.db"
    con = sqlite3.connect(dbfile)
    con.executescript(SCHEMA_AND_SEED)
    con.commit()
    con.close()

    monkeypatch.setenv("MEDQUEST_DB", str(dbfile))
    monkeypatch.setenv("FLASK_API_PROXY_SECRET", PROXY_SECRET)
    monkeypatch.delenv("TURSO_DATABASE_URL", raising=False)
    monkeypatch.delenv("TURSO_AUTH_TOKEN", raising=False)

    app = create_app()
    # Explicitly disable testing bypass so require_auth executes all real checks
    app.config["TESTING"] = False
    return app.test_client()


def test_auth_missing_proxy_secret_env(auth_client, monkeypatch):
    monkeypatch.delenv("FLASK_API_PROXY_SECRET", raising=False)
    response = auth_client.get(
        "/api/meta",
        headers={
            "X-Internal-Proxy-Token": PROXY_SECRET,
            "X-Guest-ID": str(uuid.uuid4()),
        },
    )
    assert response.status_code == 401
    assert response.get_json() == {"error": "Unauthorized"}


def test_auth_no_token_returns_401(auth_client):
    response = auth_client.get("/api/meta")
    assert response.status_code == 401
    assert response.get_json() == {"error": "Unauthorized"}


def test_auth_invalid_proxy_secret(auth_client):
    response = auth_client.get(
        "/api/meta",
        headers={
            "X-Internal-Proxy-Token": "wrong-secret",
            "X-Guest-ID": str(uuid.uuid4()),
        },
    )
    assert response.status_code == 401
    assert response.get_json() == {"error": "Unauthorized"}


def test_auth_valid_proxy_no_guest_id(auth_client):
    response = auth_client.get(
        "/api/meta",
        headers={
            "X-Internal-Proxy-Token": PROXY_SECRET,
        },
    )
    assert response.status_code == 401
    assert response.get_json() == {"error": "Unauthorized"}


def test_auth_rejects_uuid_v1(auth_client):
    uuid_v1 = str(uuid.uuid1())
    response = auth_client.get(
        "/api/meta",
        headers={
            "X-Internal-Proxy-Token": PROXY_SECRET,
            "X-Guest-ID": uuid_v1,
        },
    )
    assert response.status_code == 401
    assert response.get_json() == {"error": "Unauthorized"}


def test_auth_rejects_nil_uuid(auth_client):
    nil_uuid = "00000000-0000-0000-0000-000000000000"
    response = auth_client.get(
        "/api/meta",
        headers={
            "X-Internal-Proxy-Token": PROXY_SECRET,
            "X-Guest-ID": nil_uuid,
        },
    )
    assert response.status_code == 401
    assert response.get_json() == {"error": "Unauthorized"}


def test_auth_rejects_malformed_string(auth_client):
    response = auth_client.get(
        "/api/meta",
        headers={
            "X-Internal-Proxy-Token": PROXY_SECRET,
            "X-Guest-ID": "not-a-valid-uuid-v4",
        },
    )
    assert response.status_code == 401
    assert response.get_json() == {"error": "Unauthorized"}


def test_auth_accepts_valid_uuid_v4_returns_exact_200(auth_client):
    valid_uuid = str(uuid.uuid4())
    response = auth_client.get(
        "/api/meta",
        headers={
            "X-Internal-Proxy-Token": PROXY_SECRET,
            "X-Guest-ID": valid_uuid,
        },
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "institutions" in data
    assert "areas" in data


def test_auth_guest_data_isolation(auth_client):
    guest_a = str(uuid.uuid4())
    guest_b = str(uuid.uuid4())

    headers_a = {
        "X-Internal-Proxy-Token": PROXY_SECRET,
        "X-Guest-ID": guest_a,
    }
    headers_b = {
        "X-Internal-Proxy-Token": PROXY_SECRET,
        "X-Guest-ID": guest_b,
    }

    # Guest A responde à questão 1
    resp_a = auth_client.post(
        "/api/questions/1/attempt",
        headers=headers_a,
        json={"selected_letter": "B", "time_spent_ms": 1500, "confidence": "certeza"},
    )
    assert resp_a.status_code == 200
    assert resp_a.get_json()["is_correct"] is True

    # Guest A consulta overview stats e vê 1 tentativa
    stats_a = auth_client.get("/api/stats/overview", headers=headers_a)
    assert stats_a.status_code == 200
    assert stats_a.get_json()["total_attempts"] == 1

    # Guest B consulta overview stats e DEVE ver 0 tentativas (isolamento completo)
    stats_b = auth_client.get("/api/stats/overview", headers=headers_b)
    assert stats_b.status_code == 200
    assert stats_b.get_json()["total_attempts"] == 0


def test_auth_does_not_bypass_unknown_routes_containing_images(auth_client):
    response = auth_client.get("/api/private/images/not-a-public-route")
    assert response.status_code == 401


def test_jwt_requires_issuer_expiration_and_subject(auth_client, monkeypatch):
    from api import auth

    captured = {}

    class FakeJwksClient:
        def get_signing_key_from_jwt(self, token):
            assert token == "signed-token"
            return SimpleNamespace(key="public-key")

    def fake_decode(token, key, **kwargs):
        captured.update(kwargs)
        return {"sub": "user-123"}

    monkeypatch.setattr(auth, "jwks_client", FakeJwksClient())
    monkeypatch.setattr(auth, "CLERK_ISSUER", "https://issuer.example")
    monkeypatch.setattr(auth, "CLERK_AUDIENCE", None)
    monkeypatch.setattr(auth.jwt, "decode", fake_decode)

    response = auth_client.get(
        "/api/meta",
        headers={"Authorization": "Bearer signed-token"},
    )
    assert response.status_code == 200
    assert captured["issuer"] == "https://issuer.example"
    assert captured["algorithms"] == ["RS256"]
    assert captured["options"]["require"] == ["exp", "iss", "sub"]
    assert captured["options"]["verify_aud"] is False


def test_performance_metrics_require_separate_operational_token(auth_client, monkeypatch):
    auth_headers = {
        "X-Internal-Proxy-Token": PROXY_SECRET,
        "X-Guest-ID": str(uuid.uuid4()),
    }
    disabled = auth_client.get("/api/metrics/performance", headers=auth_headers)
    assert disabled.status_code == 404

    monkeypatch.setenv("METRICS_API_TOKEN", "metrics-secret")
    unauthorized = auth_client.get("/api/metrics/performance", headers=auth_headers)
    assert unauthorized.status_code == 401

    allowed = auth_client.get(
        "/api/metrics/performance",
        headers={**auth_headers, "X-Metrics-Token": "metrics-secret"},
    )
    assert allowed.status_code == 200
    assert "routes" in allowed.get_json()
