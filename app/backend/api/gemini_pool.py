"""
Gemini Key Pool & Concurrency Engine.
Gerencia um pool multi-chave e multi-modelo de APIs Google AI com balanceamento Round-Robin,
detecção automática de Rate Limit (HTTP 429), isolamento de chave com cooldown inteligente,
fallback entre modelos Flash e execução concorrente de alto rendimento.
"""

import os
import json
import time
import logging
import threading
import urllib.request
import urllib.error
import email.utils
import re
from typing import List, Dict, Any, Optional, Tuple, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

from pathlib import Path
from dotenv import load_dotenv, find_dotenv

# Garante que as variáveis de ambiente foram carregadas se gemini_pool for importado diretamente
_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)
else:
    load_dotenv(find_dotenv())

logger = logging.getLogger(__name__)

# ``gemini-3.5-flash`` can return transient 503s for an entire key pool.  Keep
# the lightweight model first so interactive features such as the preceptor do
# not spend their whole request budget waiting for that provider to recover.
DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")
DEFAULT_FALLBACK_MODELS = ("gemini-3.6-flash", "gemini-3.7-flash")


class KeyState:
    def __init__(self, key: str, index: int):
        self.key = key
        self.index = index
        self.cooldown_until: float = 0.0
        self.model_cooldown_until: Dict[str, float] = {}
        self.total_calls: int = 0
        self.success_calls: int = 0
        self.error_calls: int = 0
        self.consecutive_429: int = 0
        self.model_consecutive_429: Dict[str, int] = {}
        self.last_error: str = ""

    @property
    def is_available(self) -> bool:
        return time.time() >= self.cooldown_until

    def is_available_for(self, model: Optional[str] = None) -> bool:
        if not self.is_available:
            return False
        return not model or time.time() >= self.model_cooldown_until.get(model, 0.0)

    def mark_success(self, model: Optional[str] = None):
        self.total_calls += 1
        self.success_calls += 1
        if model:
            self.model_consecutive_429[model] = 0
        else:
            self.consecutive_429 = 0

    def mark_rate_limit(
        self,
        cooldown_seconds: float = 60.0,
        reason: str = "Rate Limit (429)",
        model: Optional[str] = None,
    ):
        self.total_calls += 1
        self.error_calls += 1
        if model:
            consecutive_429 = self.model_consecutive_429.get(model, 0) + 1
            self.model_consecutive_429[model] = consecutive_429
        else:
            self.consecutive_429 += 1
            consecutive_429 = self.consecutive_429
        # Backoff progressivo, independente para cada modelo da mesma chave.
        actual_cooldown = cooldown_seconds * min(consecutive_429, 3)
        cooldown_until = time.time() + actual_cooldown
        if model:
            self.model_cooldown_until[model] = cooldown_until
        else:
            self.cooldown_until = cooldown_until
        self.last_error = f"{reason} [Cooldown {actual_cooldown:.0f}s]"
        scope = f" para o modelo {model}" if model else ""
        logger.warning(f"[GeminiPool] Chave #{self.index} em cooldown{scope} por {actual_cooldown:.0f}s: {reason}")

    def mark_error(self, err: str, cooldown_seconds: float = 60.0, model: Optional[str] = None):
        self.total_calls += 1
        self.error_calls += 1
        self.last_error = err
        err_lower = err.lower()
        if any(keyword in err_lower for keyword in ["timed out", "timeout", "timedout", "connection", "unavailable", "503", "504", "reset"]):
            cooldown_until = time.time() + cooldown_seconds
            if model:
                self.model_cooldown_until[model] = cooldown_until
            else:
                self.cooldown_until = cooldown_until
            scope = f" para o modelo {model}" if model else ""
            logger.warning(f"[GeminiPool] Chave #{self.index} em cooldown{scope} por {cooldown_seconds:.0f}s devido a erro: {err}")


class GeminiPool:
    def __init__(self, keys: Optional[List[str]] = None, default_model: str = DEFAULT_MODEL):
        self.default_model = default_model
        self.models = self._load_models(default_model)
        self.lock = threading.Lock()
        self._keys: List[KeyState] = []
        self._current_index = 0
        self._load_keys(keys)

    def _load_keys(self, explicit_keys: Optional[List[str]] = None):
        if explicit_keys:
            raw_list = explicit_keys
        else:
            raw_env = os.environ.get("GEMINI_API_KEYS", "") or os.environ.get("GEMINI_API_KEY", "")
            raw_list = [k.strip() for k in raw_env.split(",") if k.strip()]

        self._keys = [
            KeyState(key=k, index=i + 1)
            for i, k in enumerate(raw_list)
            if len(k) > 10 and not k.lower().startswith(("dummy", "test", "gsk_test"))
        ]
        if not self._keys:
            logger.warning("[GeminiPool] Nenhuma chave Gemini válida encontrada.")
        else:
            logger.info(f"[GeminiPool] {len(self._keys)} chaves Google AI registradas com sucesso.")

    @staticmethod
    def _split_models(value: str) -> List[str]:
        return [model.strip() for model in value.split(",") if model.strip()]

    def _load_models(self, default_model: str) -> List[str]:
        """Retorna a cadeia de fallback sem repetir modelos.

        GEMINI_MODELS tem prioridade e aceita uma lista separada por vírgulas. Se não
        estiver configurada, preservamos GEMINI_MODEL e adicionamos os Flash de fallback.
        """
        configured = self._split_models(os.environ.get("GEMINI_MODELS", ""))
        candidates = configured or [default_model, *DEFAULT_FALLBACK_MODELS]
        models = []
        for candidate in candidates:
            if candidate not in models:
                models.append(candidate)
        return models

    def _model_candidates(self, requested_model: Optional[str]) -> List[str]:
        if not requested_model:
            return self.models
        return [requested_model, *(model for model in self.models if model != requested_model)]

    @staticmethod
    def _retry_after_seconds(error: urllib.error.HTTPError, body: str) -> float:
        """Usa a orientação do servidor quando ela estiver disponível."""
        retry_after = error.headers.get("Retry-After") if error.headers else None
        if retry_after:
            try:
                return max(1.0, float(retry_after))
            except ValueError:
                try:
                    return max(1.0, email.utils.parsedate_to_datetime(retry_after).timestamp() - time.time())
                except (TypeError, ValueError):
                    pass
        retry_match = re.search(r'"retryDelay"\s*:\s*"([0-9.]+)s"', body)
        return max(1.0, float(retry_match.group(1))) if retry_match else 60.0

    @staticmethod
    def _is_account_quota_exhausted(body: str) -> bool:
        """Distingue quota da conta/projeto de limite temporário de um modelo."""
        normalized = body.lower()
        markers = (
            "exceeded your current quota",
            "check your plan and billing",
            "daily quota",
            "quota_exceeded",
        )
        return any(marker in normalized for marker in markers)

    @property
    def total_keys(self) -> int:
        return len(self._keys)

    def get_available_key(
        self, max_wait_seconds: float = 30.0, model: Optional[str] = None
    ) -> Tuple[Optional[KeyState], str]:
        """Obtém a próxima chave disponível via Round-Robin com checagem de cooldown."""
        with self.lock:
            if not self._keys:
                return None, "Nenhuma chave registrada no pool."

            start_time = time.time()
            while time.time() - start_time <= max_wait_seconds:
                # Tenta encontrar uma chave pronta
                for _ in range(len(self._keys)):
                    candidate = self._keys[self._current_index]
                    self._current_index = (self._current_index + 1) % len(self._keys)
                    if candidate.is_available_for(model):
                        return candidate, ""

                # Se todas estiverem em cooldown, calcula o menor tempo de espera
                min_wait = min(
                    k.model_cooldown_until.get(model, k.cooldown_until) if model else k.cooldown_until
                    for k in self._keys
                ) - time.time()
                if min_wait <= 0:
                    continue
                if min_wait > (max_wait_seconds - (time.time() - start_time)):
                    break
                time.sleep(min(min_wait + 0.1, 2.0))

            return None, "Todas as chaves do pool estão em cooldown/rate limit."

    def generate_content(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        json_mode: bool = False,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_retries: int = 4,
        timeout: int = 25,
        max_total_seconds: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Executa uma chamada ao Gemini com fallback automático entre chaves e modelos.
        Retorna dicionário contendo 'text', 'raw_response', e 'key_index'.
        """
        payload: Dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature
            }
        }
        if json_mode:
            payload["generationConfig"]["responseMimeType"] = "application/json"
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        body = json.dumps(payload).encode("utf-8")
        last_exception = None
        deadline = time.monotonic() + max_total_seconds if max_total_seconds else None

        for target_model in self._model_candidates(model):
            if deadline and time.monotonic() >= deadline:
                break
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{target_model}:generateContent"
            logger.info("[GeminiPool] Tentando modelo %s.", target_model)

            # Pelo menos uma tentativa por chave: assim contas independentes não são
            # descartadas apenas porque uma chave anterior atingiu seu limite.
            attempts_for_model = max(max_retries, len(self._keys))
            for _ in range(attempts_for_model):
                if deadline and time.monotonic() >= deadline:
                    last_exception = TimeoutError("Orcamento total do provedor Gemini esgotado.")
                    break
                # Não aguarda uma chave que já está em cooldown: tenta o próximo modelo.
                key_state, err_msg = self.get_available_key(max_wait_seconds=0.1, model=target_model)
                if not key_state:
                    last_exception = RuntimeError(err_msg)
                    logger.warning("[GeminiPool] Modelo %s indisponível: %s", target_model, err_msg)
                    break

                req = urllib.request.Request(
                    url,
                    data=body,
                    headers={"Content-Type": "application/json", "x-goog-api-key": key_state.key}
                )

                try:
                    request_timeout = timeout
                    if deadline:
                        request_timeout = max(0.5, min(timeout, deadline - time.monotonic()))
                    with urllib.request.urlopen(req, timeout=request_timeout) as resp:
                        data = json.loads(resp.read().decode("utf-8"))
                        key_state.mark_success(target_model)
                        candidates = data.get("candidates", [])
                        if not candidates:
                            raise ValueError(f"Resposta vazia ou bloqueada por filtro de segurança: {data}")
                        parts = candidates[0].get("content", {}).get("parts", [])
                        text = parts[0].get("text", "") if parts else ""
                        return {"text": text, "raw": data, "key_index": key_state.index, "model": target_model}

                except urllib.error.HTTPError as e:
                    try:
                        err_body = e.read().decode("utf-8")
                    except Exception:
                        err_body = ""
                    if e.code == 429 or "RESOURCE_EXHAUSTED" in err_body:
                        cooldown_seconds = self._retry_after_seconds(e, err_body)
                        quota_is_global = self._is_account_quota_exhausted(err_body)
                        # Quota diária/financeira pertence à conta da chave, não ao
                        # modelo. Evita desperdiçar chamadas nos demais fallbacks.
                        if quota_is_global:
                            cooldown_seconds = max(cooldown_seconds, float(os.environ.get("GEMINI_ACCOUNT_QUOTA_COOLDOWN", "86400")))
                        key_state.mark_rate_limit(
                            cooldown_seconds=cooldown_seconds,
                            reason=f"HTTP 429 ({err_body[:100]})",
                            model=None if quota_is_global else target_model,
                        )
                        last_exception = RuntimeError(f"Rate limit na chave #{key_state.index}: {err_body[:200]}")
                        continue
                    if e.code == 404:
                        key_state.mark_error(f"Modelo indisponível: HTTP {e.code}", model=target_model)
                        last_exception = RuntimeError(f"Modelo {target_model} indisponível: {err_body[:200]}")
                        break
                    if e.code in (500, 503, 504):
                        key_state.mark_error(f"HTTP {e.code}", cooldown_seconds=60.0, model=target_model)
                        last_exception = RuntimeError(f"Erro no servidor Gemini ({e.code}): {err_body[:200]}")
                        time.sleep(0.5)
                        continue
                    key_state.mark_error(f"HTTP {e.code}: {err_body[:100]}", model=target_model)
                    raise RuntimeError(f"Erro na API Gemini ({e.code}): {err_body}")

                except Exception as e:
                    is_timeout = any(kw in str(e).lower() for kw in ["timed out", "timeout"])
                    key_state.mark_error(str(e), cooldown_seconds=60.0, model=target_model)
                    last_exception = e
                    time.sleep(0.2)
                    if is_timeout:
                        # Se o modelo sofreu timeout, avança imediatamente para o próximo
                        # modelo de fallback da cadeia em vez de esgotar o prazo insistindo no mesmo.
                        logger.warning("[GeminiPool] Timeout no modelo %s. Tentando próximo modelo de fallback.", target_model)
                        break

        raise RuntimeError(
            f"Nenhum modelo do pool respondeu após os fallbacks {self._model_candidates(model)}. "
            f"Último erro: {last_exception}"
        )

    def generate_batch_parallel(
        self,
        items: List[Any],
        process_item_fn: Callable[[Any, "GeminiPool"], Any],
        max_workers: Optional[int] = None
    ) -> List[Any]:
        """
        Processa uma lista de itens em paralelo, distribuindo a carga de forma equilibrada
        entre todas as chaves do pool.
        """
        num_keys = max(1, len(self._keys))
        # Otimiza o número de threads com base no número de chaves disponíveis
        workers = max_workers or min(num_keys * 3, 18)
        results = [None] * len(items)

        def _worker(idx: int, item: Any):
            res = process_item_fn(item, self)
            return idx, res

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(_worker, i, it) for i, it in enumerate(items)]
            for future in as_completed(futures):
                try:
                    idx, res = future.result()
                    results[idx] = res
                except Exception as e:
                    logger.error(f"[GeminiPool Batch] Erro ao processar item: {e}")

        return results

    def health_check(self) -> Dict[str, Any]:
        """Executa um ping de validação em todas as chaves cadastradas."""
        report = []
        for state in self._keys:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.default_model}:generateContent"
            payload = {"contents": [{"parts": [{"text": "ping"}]}]}
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json", "x-goog-api-key": state.key}
            )
            t0 = time.time()
            try:
                with urllib.request.urlopen(req, timeout=5) as resp:
                    latency = (time.time() - t0) * 1000
                    report.append({
                        "key_index": state.index,
                        "key_prefix": state.key[:10] + "...",
                        "status": "HEALTHY",
                        "latency_ms": round(latency, 1),
                        "total_calls": state.total_calls,
                        "success_calls": state.success_calls,
                        "error_calls": state.error_calls
                    })
            except Exception as e:
                report.append({
                    "key_index": state.index,
                    "key_prefix": state.key[:10] + "...",
                    "status": "UNHEALTHY",
                    "error": str(e),
                    "total_calls": state.total_calls,
                    "success_calls": state.success_calls,
                    "error_calls": state.error_calls
                })
        return {
            "model": self.default_model,
            "total_keys": len(self._keys),
            "keys_report": report
        }


# Instância Singleton global para uso em todo o backend
gemini_pool = GeminiPool()
