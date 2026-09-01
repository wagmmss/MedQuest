import io
import json
import urllib.error

import pytest

from api import universal_pool


class _Response:
    def __init__(self, data):
        self._data = json.dumps(data).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self):
        return self._data


@pytest.fixture(autouse=True)
def clear_provider_cooldowns():
    universal_pool._cooldowns.clear()
    yield
    universal_pool._cooldowns.clear()


def test_short_gemini_answer_continues_to_openrouter(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER_ORDER", "gemini,openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-test-key-long-enough-123")
    monkeypatch.setenv("OPENROUTER_MODELS", "openrouter/free")
    monkeypatch.setattr(universal_pool.gemini_pool, "_keys", [object()])
    monkeypatch.setattr(
        universal_pool.gemini_pool,
        "generate_content",
        lambda **_: {"text": "curto", "model": "gemini-test"},
    )
    monkeypatch.setattr(
        universal_pool.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: _Response({
            "model": "free/model",
            "choices": [{"message": {"content": "explicacao detalhada"}}],
        }),
    )

    result = universal_pool.generate_content_with_fallback(
        "prompt", response_validator=lambda text: len(text) > 10
    )

    assert result["source"] == "openrouter"
    assert result["model"] == "free/model"


def test_daily_quota_skips_exhausted_openrouter_key(monkeypatch):
    universal_pool._cooldowns.clear()
    monkeypatch.setenv("AI_PROVIDER_ORDER", "openrouter")
    monkeypatch.setenv(
        "OPENROUTER_API_KEYS",
        "or-first-key-long-enough-123,or-second-key-long-enough-456",
    )
    monkeypatch.setenv("OPENROUTER_MODELS", "openrouter/free")
    calls = []

    def fake_urlopen(request, **_kwargs):
        calls.append(request.headers["Authorization"])
        if len(calls) == 1:
            raise urllib.error.HTTPError(
                request.full_url,
                429,
                "rate limit",
                {},
                io.BytesIO(b'{"error":"daily quota exceeded"}'),
            )
        return _Response({"choices": [{"message": {"content": "resposta valida"}}]})

    monkeypatch.setattr(universal_pool.urllib.request, "urlopen", fake_urlopen)

    result = universal_pool.generate_content_with_fallback("prompt")

    assert result["source"] == "openrouter"
    assert len(calls) == 2
    status = universal_pool.provider_status()
    assert status["providers"]["openrouter"]["available_keys"] == 1
    assert status["cooldowns"][0]["remaining_seconds"] > 86000


def test_provider_status_never_contains_secret(monkeypatch):
    secret = "or-super-secret-key-123456"
    monkeypatch.setenv("OPENROUTER_API_KEY", secret)

    serialized = json.dumps(universal_pool.provider_status())

    assert secret not in serialized
    assert "openrouter" in serialized
