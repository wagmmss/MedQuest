import base64
import hmac
import logging
import os
import uuid
from functools import wraps

import jwt
from flask import g, jsonify, request

logger = logging.getLogger(__name__)

# Extract domain from the publishable key
pk = os.getenv("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY", "")
configured_issuer = os.getenv("CLERK_ISSUER", "").rstrip("/") or None
if pk.startswith(("pk_test_", "pk_live_")):
    try:
        domain_b64 = pk.removeprefix("pk_test_").removeprefix("pk_live_").strip("$")
        domain_b64 += "=" * ((4 - len(domain_b64) % 4) % 4)
        domain = base64.b64decode(domain_b64).decode("utf-8")
        domain = domain.removesuffix("$")
        CLERK_ISSUER = configured_issuer or f"https://{domain}"
    except Exception:
        CLERK_ISSUER = configured_issuer
else:
    CLERK_ISSUER = configured_issuer

JWKS_URL = os.getenv(
    "CLERK_JWKS_URL",
    f"{CLERK_ISSUER}/.well-known/jwks.json" if CLERK_ISSUER else "",
) or None
CLERK_AUDIENCE = os.getenv("CLERK_JWT_AUDIENCE") or None


def is_valid_uuid_v4(val: str | None) -> bool:
    """Valida se uma string é um UUID canônico versão 4 (minúsculo, não-nil, version==4)."""
    if not val or not isinstance(val, str):
        return False
    # Nil UUID is strictly rejected
    if val == "00000000-0000-0000-0000-000000000000":
        return False
    try:
        u = uuid.UUID(val, version=4)
        # u.version == 4 checks the version bits, str(u) == val.lower() checks 8-4-4-4-12 canonical format
        return u.version == 4 and str(u) == val.lower()
    except (ValueError, AttributeError, TypeError):
        return False


# Global PyJWKClient instance to cache keys and avoid rate limits/timeouts
jwks_client = jwt.PyJWKClient(JWKS_URL, cache_keys=True, timeout=5) if JWKS_URL else None

CURATOR_EMAILS = {"moraes.wagg@gmail.com"}

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        from flask import current_app
        if current_app.config.get("TESTING"):
            g.user_id = getattr(g, "user_id", "1")
            g.user_email = getattr(g, "user_email", "moraes.wagg@gmail.com")
            return f(*args, **kwargs)

        if request.method == "OPTIONS" or request.path == "/":
            return f(*args, **kwargs)

        proxy_secret = os.environ.get("FLASK_API_PROXY_SECRET", "")
        proxy_token = request.headers.get("X-Internal-Proxy-Token", "")
        if proxy_secret and proxy_token and hmac.compare_digest(proxy_secret, proxy_token):
            g.user_email = (request.headers.get("X-User-Email") or "").strip().lower()
        else:
            g.user_email = ""

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer ") or auth_header == "Bearer null":
            if not proxy_secret or not proxy_token:
                return jsonify({"error": "Unauthorized"}), 401

            if not hmac.compare_digest(proxy_secret, proxy_token):
                return jsonify({"error": "Unauthorized"}), 401

            guest_id = request.headers.get("X-Guest-ID")
            if not is_valid_uuid_v4(guest_id):
                return jsonify({"error": "Unauthorized"}), 401

            g.user_id = f"guest:{guest_id.lower()}"
            return f(*args, **kwargs)

        token = auth_header.removeprefix("Bearer ").strip()
        if not token:
            return jsonify({"error": "Unauthorized"}), 401
        try:
            if not jwks_client or not CLERK_ISSUER:
                return jsonify({"error": "Unauthorized"}), 401
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            decode_options = {
                "algorithms": ["RS256"],
                "issuer": CLERK_ISSUER,
                "options": {
                    "require": ["exp", "iss", "sub"],
                    "verify_aud": CLERK_AUDIENCE is not None,
                },
            }
            if CLERK_AUDIENCE:
                decode_options["audience"] = CLERK_AUDIENCE
            data = jwt.decode(token, signing_key.key, **decode_options)
            sub = data.get("sub")
            if not isinstance(sub, str) or not sub.strip():
                return jsonify({"error": "Unauthorized"}), 401
            g.user_id = sub.strip()
            
            # Extract email if present in JWT claims
            if not g.user_email:
                if "email" in data and isinstance(data["email"], str):
                    g.user_email = data["email"].strip().lower()
                elif "primary_email" in data and isinstance(data["primary_email"], str):
                    g.user_email = data["primary_email"].strip().lower()
        except Exception as exc:
            logger.info("JWT validation failed: %s", type(exc).__name__)
            return jsonify({"error": "Unauthorized"}), 401

        return f(*args, **kwargs)
    return decorated


def require_curator(f):
    @wraps(f)
    @require_auth
    def decorated(*args, **kwargs):
        from flask import current_app
        if current_app.config.get("TESTING") and getattr(g, "is_curator", True):
            return f(*args, **kwargs)

        user_email = (getattr(g, "user_email", None) or "").strip().lower()
        if user_email not in CURATOR_EMAILS:
            return jsonify({"error": "Forbidden: Acesso restrito para curadoria de conteúdo"}), 403
        return f(*args, **kwargs)
    return decorated

