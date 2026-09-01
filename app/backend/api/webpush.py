"""Módulo auxiliar para envio e gestão de Web Push (RFC 8291 / RFC 8292) — MedQuest.

Utiliza pywebpush para criptografia ECDH/AES-GCM e assinaturas VAPID.
Implementa:
- Proteção SSRF por allowlist explícita (WEB_PUSH_ALLOWED_HOSTS).
- Bloqueio de redirecionamentos HTTP (allow_redirects=False).
- Limpeza de subscrições expiradas (404/410).
- Hook para injeção de dependência em testes herméticos.
"""

import ipaddress
import json
import logging
import os
from urllib.parse import urlparse

from pywebpush import WebPushException, webpush
import requests

logger = logging.getLogger(__name__)

# Hook para testes herméticos (mock sender)
_mock_sender = None

DEFAULT_ALLOWED_HOSTS = [
    "fcm.googleapis.com",
    "*.push.services.mozilla.com",
    "push.services.mozilla.com",
    "*.push.apple.com",
    "web.push.apple.com",
    "push.apple.com",
]


class NoRedirectSession(requests.Session):
    """Sessão HTTP customizada que desativa completamente o seguimento de redirecionamentos (3xx)."""

    def send(self, request, **kwargs):
        kwargs["allow_redirects"] = False
        return super().send(request, **kwargs)

    def resolve_redirects(self, *args, **kwargs):
        # Generator vazio: nunca executa nem gera requisições secundárias de redirecionamento
        return
        yield



def set_mock_webpush_sender(sender_fn):
    """Permite injetar uma função mock para envio de Web Push durante testes unitários."""
    global _mock_sender
    _mock_sender = sender_fn


def get_allowed_hosts() -> list[str]:
    """Retorna a lista de hosts permitidos para endpoints Web Push."""
    raw = os.environ.get("WEB_PUSH_ALLOWED_HOSTS")
    if raw is not None:
        return [h.strip().lower() for h in raw.split(",") if h.strip()]

    # Em produção, se a variável não estiver definida, falha fechado
    is_prod = os.environ.get("FLASK_ENV") == "production"
    if is_prod:
        return []

    return [h.lower() for h in DEFAULT_ALLOWED_HOSTS]


def is_host_allowed(hostname: str, allowed_patterns: list[str]) -> bool:
    """Verifica se o hostname corresponde estritamente a um padrão permitido (exato ou subdomínio)."""
    if not hostname or not allowed_patterns:
        return False
    hostname = hostname.lower().strip()
    for pattern in allowed_patterns:
        pattern = pattern.lower().strip()
        if not pattern:
            continue
        if pattern.startswith("*."):
            base_domain = pattern[2:]
            if hostname == base_domain or hostname.endswith("." + base_domain):
                return True
        else:
            if hostname == pattern:
                return True
    return False


def is_safe_push_endpoint(endpoint: str) -> bool:
    """Valida se o endpoint de push é uma URL HTTPS válida, com host permitido por allowlist e não-privado."""
    if not endpoint or not isinstance(endpoint, str):
        return False
    try:
        parsed = urlparse(endpoint)
        if parsed.scheme != "https":
            return False
        hostname = parsed.hostname
        if not hostname:
            return False
        hostname_lower = hostname.lower()
        if (
            hostname_lower in ("localhost", "127.0.0.1", "::1")
            or hostname_lower.endswith(".local")
            or hostname_lower.endswith(".internal")
        ):
            return False

        # Se for endereço IP literal, rejeitar privados/loopback/reservados
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local:
                return False
        except ValueError:
            pass

        # Validação da allowlist explícita de provedores Web Push
        allowed = get_allowed_hosts()
        if not allowed:
            logger.warning("Allowlist de Web Push vazia ou ausente; bloqueando endpoint %s", endpoint)
            return False

        return is_host_allowed(hostname_lower, allowed)
    except Exception:
        return False


def get_vapid_public_key() -> str | None:
    """Retorna a chave pública VAPID configurada no ambiente."""
    return os.environ.get("VAPID_PUBLIC_KEY") or os.environ.get("NEXT_PUBLIC_VAPID_PUBLIC_KEY") or None


def is_vapid_configured() -> bool:
    """Verifica se o par de chaves VAPID está presente para permitir envios reais."""
    pub = get_vapid_public_key()
    priv = os.environ.get("VAPID_PRIVATE_KEY")
    return bool(pub and priv)


def send_web_push(
    subscription: dict,
    payload: dict | str,
    vapid_private_key: str | None = None,
    vapid_claim_email: str | None = None,
    timeout: int = 5,
) -> dict:
    """Envia uma notificação Web Push usando pywebpush com criptografia RFC 8291 e VAPID RFC 8292.

    Retorna dicionário com:
    - status: 'delivered' | 'failed' | 'expired' | 'vapid_unconfigured'
    - delivered: bool
    - status_code: int | None
    - error: str | None
    """
    endpoint = subscription.get("endpoint", "")
    if not is_safe_push_endpoint(endpoint):
        return {
            "status": "failed",
            "delivered": False,
            "status_code": None,
            "error": "Endpoint inseguro ou não permitido pela allowlist de Web Push.",
        }

    global _mock_sender
    if _mock_sender is not None:
        return _mock_sender(subscription, payload)

    # Se chaves VAPID não estiverem configuradas, falhar com segurança (fail-closed)
    priv_key = vapid_private_key or os.environ.get("VAPID_PRIVATE_KEY")
    pub_key = get_vapid_public_key()
    subject = (
        vapid_claim_email
        or os.environ.get("VAPID_CLAIM_EMAIL")
        or os.environ.get("VAPID_SUBJECT")
        or "mailto:admin@medquest.local"
    )

    if not priv_key or not pub_key:
        logger.info("VAPID não configurada; envio de Web Push ignorado de modo seguro.")
        return {
            "status": "vapid_unconfigured",
            "delivered": False,
            "status_code": None,
            "error": "VAPID keys ausentes no ambiente.",
        }

    body_str = json.dumps(payload) if isinstance(payload, dict) else str(payload)
    session = NoRedirectSession()

    try:
        response = webpush(
            subscription_info=subscription,
            data=body_str,
            vapid_private_key=priv_key,
            vapid_claims={"sub": subject},
            timeout=timeout,
            requests_session=session,
        )
        status_code = getattr(response, "status_code", 201)
        return {
            "status": "delivered",
            "delivered": True,
            "status_code": status_code,
            "error": None,
        }
    except WebPushException as e:
        status_code = getattr(e.response, "status_code", None) if e.response is not None else None
        if status_code in (404, 410):
            logger.info("Push subscription expirada (%s): endpoint %s", status_code, endpoint)
            return {
                "status": "expired",
                "delivered": False,
                "status_code": status_code,
                "error": f"Subscription expirada no push service (HTTP {status_code}).",
            }
        logger.warning("Falha pywebpush: %s", e)
        return {
            "status": "failed",
            "delivered": False,
            "status_code": status_code,
            "error": str(e),
        }
    except Exception as e:
        logger.warning("Exceção geral ao enviar Web Push: %s", e)
        return {
            "status": "failed",
            "delivered": False,
            "status_code": None,
            "error": str(e),
        }
