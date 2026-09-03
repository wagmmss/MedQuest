"""Failover configuravel entre os provedores de IA usados pelo MedQuest."""

from __future__ import annotations

import json
import logging
import os
import threading
import time
import urllib.error
import urllib.request
from email.utils import parsedate_to_datetime
from typing import Any, Callable, Dict, Optional

from api.gemini_pool import gemini_pool

logger = logging.getLogger(__name__)

DEFAULT_PROVIDER_ORDER = ("gemini", "groq", "openrouter", "ollama")
DEFAULT_GROQ_MODELS = ("qwen/qwen3.6-27b", "openai/gpt-oss-120b")
DEFAULT_OPENROUTER_MODELS = ("openrouter/free",)
DEFAULT_OLLAMA_MODELS = ("gemma3", "llama3.2")
DEFAULT_GLOBAL_TIMEOUT_BUDGET = 30.0
DEFAULT_PROVIDER_TIMEOUT = 10.0

_cooldowns: dict[tuple[str, int, str], float] = {}
_cooldown_lock = threading.Lock()


def _csv_env(name: str, fallback: tuple[str, ...] = ()) -> list[str]:
    values = [value.strip() for value in os.environ.get(name, "").split(",") if value.strip()]
    return values or [value for value in fallback if value]


def _keys(plural_name: str, singular_name: str) -> list[str]:
    raw = os.environ.get(plural_name, "") or os.environ.get(singular_name, "")
    return [
        value.strip() for value in raw.split(",")
        if len(value.strip()) > 15
        and not value.strip().lower().startswith(("dummy", "test", "gsk_test"))
    ]


def _provider_order() -> list[str]:
    requested = _csv_env("AI_PROVIDER_ORDER", DEFAULT_PROVIDER_ORDER)
    valid = []
    for provider in requested:
        normalized = provider.lower()
        if normalized in DEFAULT_PROVIDER_ORDER and normalized not in valid:
            valid.append(normalized)
    return valid or list(DEFAULT_PROVIDER_ORDER)


def _ollama_enabled() -> bool:
    """Permite desabilitar explicitamente o fallback local em ambientes sem Ollama."""
    return os.environ.get("OLLAMA_ENABLED", "true").strip().lower() not in {"0", "false", "no", "off"}


def _is_available(provider: str, key_index: int, model: str = "*") -> bool:
    now = time.time()
    with _cooldown_lock:
        return now >= max(
            _cooldowns.get((provider, key_index, "*"), 0.0),
            _cooldowns.get((provider, key_index, model), 0.0),
        )


def _set_cooldown(provider: str, key_index: int, seconds: float, model: str = "*") -> None:
    with _cooldown_lock:
        _cooldowns[(provider, key_index, model)] = time.time() + max(1.0, seconds)


def _retry_after(headers: Any, default: float = 60.0) -> float:
    value = headers.get("Retry-After") if headers else None
    if not value:
        return default
    try:
        return max(1.0, float(value))
    except (TypeError, ValueError):
        try:
            return max(1.0, parsedate_to_datetime(value).timestamp() - time.time())
        except (TypeError, ValueError):
            return default


def _is_daily_or_billing_limit(message: str) -> bool:
    normalized = message.lower()
    return any(marker in normalized for marker in (
        "daily limit", "daily quota", "per day", "quota_exceeded",
        "insufficient_quota", "insufficient credits", "credit balance", "billing",
    ))


def _error_status(error: Exception) -> Optional[int]:
    if isinstance(error, urllib.error.HTTPError):
        return error.code
    status = getattr(error, "status_code", None)
    if isinstance(status, int):
        return status
    status = getattr(getattr(error, "response", None), "status_code", None)
    return status if isinstance(status, int) else None


def _error_body(error: Exception) -> str:
    if isinstance(error, urllib.error.HTTPError):
        try:
            return error.read().decode("utf-8", errors="replace")
        except Exception:
            pass
    return str(error)


def _mark_failure(provider: str, key_index: int, model: str, error: Exception) -> None:
    status = _error_status(error)
    message = _error_body(error)
    if status == 429:
        daily = _is_daily_or_billing_limit(message)
        seconds = (
            float(os.environ.get("AI_DAILY_QUOTA_COOLDOWN", "86400"))
            if daily else _retry_after(getattr(error, "headers", None))
        )
        _set_cooldown(provider, key_index, seconds, "*" if daily else model)
    elif status in (401, 402, 403):
        _set_cooldown(provider, key_index, float(os.environ.get("AI_AUTH_ERROR_COOLDOWN", "3600")))
    elif status in (404, 410):
        _set_cooldown(provider, key_index, float(os.environ.get("AI_MODEL_ERROR_COOLDOWN", "3600")), model)
    elif status in (500, 502, 503, 504) or any(
        marker in message.lower() for marker in ("timeout", "timed out", "connection", "unavailable")
    ):
        _set_cooldown(provider, key_index, float(os.environ.get("AI_TRANSIENT_COOLDOWN", "60")), model)


def _messages(prompt: str, system_instruction: Optional[str], json_mode: bool) -> list[dict[str, str]]:
    messages = []
    if system_instruction:
        instruction = system_instruction
        if json_mode:
            instruction += " Responda somente com JSON valido, sem cercas Markdown."
        messages.append({"role": "system", "content": instruction})
    messages.append({"role": "user", "content": prompt})
    return messages


def _valid_text(text: Any, validator: Optional[Callable[[str], bool]]) -> bool:
    return isinstance(text, str) and bool(text.strip()) and (validator is None or validator(text.strip()))


def _try_groq(prompt: str, system_instruction: Optional[str], json_mode: bool,
              temperature: float, timeout: int,
              validator: Optional[Callable[[str], bool]]) -> Optional[Dict[str, Any]]:
    keys = _keys("GROQ_API_KEYS", "GROQ_API_KEY")
    if not keys:
        return None
    from groq import Groq

    messages = _messages(prompt, system_instruction, json_mode)
    for model in _csv_env("GROQ_MODELS", DEFAULT_GROQ_MODELS):
        for key_index, key in enumerate(keys):
            if not _is_available("groq", key_index, model):
                continue
            try:
                client = Groq(api_key=key, timeout=timeout, max_retries=0)
                kwargs: Dict[str, Any] = {"messages": messages, "model": model, "temperature": temperature}
                if json_mode:
                    kwargs["response_format"] = {"type": "json_object"}
                completion = client.chat.completions.create(**kwargs)
                text = completion.choices[0].message.content or ""
                if _valid_text(text, validator):
                    return {"text": text.strip(), "source": "groq", "model": model}
                logger.warning("[UniversalPool] Groq retornou resposta vazia/invalida (%s).", model)
            except Exception as error:
                _mark_failure("groq", key_index, model, error)
                logger.warning("[UniversalPool] Groq/%s falhou: %s", model, error)
    return None


def _try_openrouter(prompt: str, system_instruction: Optional[str], json_mode: bool,
                    temperature: float, timeout: int,
                    validator: Optional[Callable[[str], bool]]) -> Optional[Dict[str, Any]]:
    keys = _keys("OPENROUTER_API_KEYS", "OPENROUTER_API_KEY")
    if not keys:
        return None
    messages = _messages(prompt, system_instruction, json_mode)
    for model in _csv_env("OPENROUTER_MODELS", DEFAULT_OPENROUTER_MODELS):
        for key_index, key in enumerate(keys):
            if not _is_available("openrouter", key_index, model):
                continue
            payload: Dict[str, Any] = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": 2500,
            }
            if json_mode:
                payload["response_format"] = {"type": "json_object"}
            request = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {key}", "Content-Type": "application/json",
                    "HTTP-Referer": os.environ.get("OPENROUTER_SITE_URL", "http://localhost:3000"),
                    "X-Title": "MedQuest",
                },
            )
            try:
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    data = json.loads(response.read().decode("utf-8"))
                choices = data.get("choices") or []
                text = choices[0].get("message", {}).get("content", "") if choices else ""
                if _valid_text(text, validator):
                    return {"text": text.strip(), "source": "openrouter", "model": data.get("model") or model}
                logger.warning("[UniversalPool] OpenRouter retornou resposta vazia/invalida (%s).", model)
            except Exception as error:
                _mark_failure("openrouter", key_index, model, error)
                logger.warning("[UniversalPool] OpenRouter/%s falhou: %s", model, error)
    return None


def _try_ollama(prompt: str, system_instruction: Optional[str], json_mode: bool,
                temperature: float, timeout: int,
                validator: Optional[Callable[[str], bool]]) -> Optional[Dict[str, Any]]:
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
    messages = _messages(prompt, system_instruction, json_mode)
    defaults = (os.environ.get("OLLAMA_MODEL", ""), *DEFAULT_OLLAMA_MODELS)
    for model in _csv_env("OLLAMA_MODELS", defaults):
        if not _is_available("ollama", 0, model):
            continue
        payload: Dict[str, Any] = {
            "model": model, "messages": messages, "stream": False,
            "options": {"temperature": temperature},
        }
        if json_mode:
            payload["format"] = "json"
        request = urllib.request.Request(
            f"{host}/api/chat", data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
            text = data.get("message", {}).get("content", "")
            if _valid_text(text, validator):
                return {"text": text.strip(), "source": "ollama", "model": data.get("model") or model}
            logger.warning("[UniversalPool] Ollama retornou resposta vazia/invalida (%s).", model)
        except Exception as error:
            _mark_failure("ollama", 0, model, error)
            logger.warning("[UniversalPool] Ollama/%s falhou: %s", model, error)
    return None


def generate_content_with_fallback(
    prompt: str,
    system_instruction: Optional[str] = None,
    json_mode: bool = False,
    temperature: float = 0.2,
    timeout: Optional[int] = None,
    response_validator: Optional[Callable[[str], bool]] = None,
) -> Dict[str, Any]:
    """Tenta os provedores configurados dentro de um orçamento total compartilhado.

    ``timeout`` limita cada provedor, enquanto ``AI_GLOBAL_TIMEOUT_BUDGET``
    limita a requisição inteira. Cada provedor recebe uma fatia justa do tempo
    restante, para que uma falha lenta não impeça os fallbacks de serem usados.
    """
    attempts: list[str] = []
    global_budget = max(1.0, float(os.environ.get("AI_GLOBAL_TIMEOUT_BUDGET", str(DEFAULT_GLOBAL_TIMEOUT_BUDGET))))
    configured_provider_timeout = max(
        1.0,
        float(os.environ.get("AI_PROVIDER_TIMEOUT", str(DEFAULT_PROVIDER_TIMEOUT))),
    )
    provider_timeout = float(timeout) if timeout is not None else configured_provider_timeout
    providers = [provider for provider in _provider_order() if provider != "ollama" or _ollama_enabled()]
    start_time = time.perf_counter()

    for provider_index, provider in enumerate(providers):
        elapsed = time.perf_counter() - start_time
        remaining = global_budget - elapsed
        if remaining <= 0.3:
            logger.warning("[UniversalPool] Budget global de IA esgotado (%.2fs decorridos).", elapsed)
            break

        providers_left = len(providers) - provider_index
        # Reserva tempo para os provedores seguintes. Isso é especialmente
        # importante para o Preceptor, cujo prompt pode demorar alguns segundos.
        fair_share = remaining / max(1, providers_left)
        current_timeout = max(1.0, min(provider_timeout, fair_share))
        attempts.append(provider)
        if provider == "gemini":
            if gemini_pool.total_keys <= 0:
                continue
            try:
                response = gemini_pool.generate_content(
                    prompt=prompt, system_instruction=system_instruction, json_mode=json_mode,
                    temperature=temperature, timeout=int(current_timeout),
                    max_total_seconds=current_timeout,
                )
                text = response.get("text", "")
                if _valid_text(text, response_validator):
                    return {"text": text.strip(), "source": "gemini", "model": response.get("model", "gemini")}
                logger.warning("[UniversalPool] Gemini retornou resposta vazia/invalida.")
            except Exception as error:
                logger.warning("[UniversalPool] Gemini falhou: %s", error)
        elif provider == "groq":
            response = _try_groq(prompt, system_instruction, json_mode, temperature, int(current_timeout), response_validator)
            if response:
                return response
        elif provider == "openrouter":
            response = _try_openrouter(prompt, system_instruction, json_mode, temperature, int(current_timeout), response_validator)
            if response:
                return response
        elif provider == "ollama":
            response = _try_ollama(prompt, system_instruction, json_mode, temperature, int(current_timeout), response_validator)
            if response:
                return response
    raise RuntimeError(f"Todos os provedores de IA falharam ({', '.join(attempts)}).")


def provider_status() -> Dict[str, Any]:
    """Retorna configuracao operacional sem revelar chaves ou segredos."""
    now = time.time()
    groq_keys = _keys("GROQ_API_KEYS", "GROQ_API_KEY")
    openrouter_keys = _keys("OPENROUTER_API_KEYS", "OPENROUTER_API_KEY")
    groq_models = _csv_env("GROQ_MODELS", DEFAULT_GROQ_MODELS)
    openrouter_models = _csv_env("OPENROUTER_MODELS", DEFAULT_OPENROUTER_MODELS)

    def available_count(provider: str, keys: list[str], models: list[str]) -> int:
        return sum(1 for index in range(len(keys)) if any(_is_available(provider, index, model) for model in models))

    with _cooldown_lock:
        cooldowns = [
            {"provider": provider, "key_index": index + 1, "model": model,
             "remaining_seconds": round(until - now)}
            for (provider, index, model), until in _cooldowns.items() if until > now
        ]
    ollama_defaults = (os.environ.get("OLLAMA_MODEL", ""), *DEFAULT_OLLAMA_MODELS)
    active_order = [provider for provider in _provider_order() if provider != "ollama" or _ollama_enabled()]
    return {
        "order": active_order,
        "providers": {
            "gemini": {"configured": gemini_pool.total_keys > 0, "keys": gemini_pool.total_keys,
                        "models": list(gemini_pool.models)},
            "groq": {"configured": bool(groq_keys), "keys": len(groq_keys),
                     "available_keys": available_count("groq", groq_keys, groq_models), "models": groq_models},
            "openrouter": {"configured": bool(openrouter_keys), "keys": len(openrouter_keys),
                           "available_keys": available_count("openrouter", openrouter_keys, openrouter_models),
                           "models": openrouter_models},
            "ollama": {"configured": _ollama_enabled(), "host": os.environ.get("OLLAMA_HOST", "http://localhost:11434"),
                       "models": _csv_env("OLLAMA_MODELS", ollama_defaults), "reachable": None},
        },
        "cooldowns": cooldowns,
        "timeouts": {
            "global_budget_seconds": max(1.0, float(os.environ.get("AI_GLOBAL_TIMEOUT_BUDGET", str(DEFAULT_GLOBAL_TIMEOUT_BUDGET)))),
            "provider_timeout_seconds": max(1.0, float(os.environ.get("AI_PROVIDER_TIMEOUT", str(DEFAULT_PROVIDER_TIMEOUT)))),
        },
    }
