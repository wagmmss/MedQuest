import os
import hmac
import uuid
import base64
from functools import lru_cache, wraps
from flask import request, jsonify, g
import jwt
import requests

CLERK_SECRET = os.getenv("CLERK_SECRET_KEY")

# Extract domain from the publishable key
pk = os.getenv("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY", "pk_test_bWFueS1sb3VzZS04Ny5jbGVyay5hY2NvdW50cy5kZXYk")
if pk.startswith("pk_test_") or pk.startswith("pk_live_"):
    try:
        domain_b64 = pk.split("_")[-1].strip("$")
        domain_b64 += "=" * ((4 - len(domain_b64) % 4) % 4)
        domain = base64.b64decode(domain_b64).decode("utf-8")
        if domain.endswith("$"):
            domain = domain[:-1]
        JWKS_URL = f"https://{domain}/.well-known/jwks.json"
    except Exception:
        JWKS_URL = None
else:
    JWKS_URL = None


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


@lru_cache(maxsize=1)
def get_jwks():
    if not JWKS_URL:
        return None
    r = requests.get(JWKS_URL, timeout=5)
    r.raise_for_status()
    return r.json()


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        from flask import current_app
        if current_app.config.get("TESTING"):
            g.user_id = getattr(g, "user_id", "1")
            return f(*args, **kwargs)

        if request.method == "OPTIONS" or request.path == "/":
            return f(*args, **kwargs)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer ") or auth_header == "Bearer null":
            proxy_secret = os.environ.get("FLASK_API_PROXY_SECRET", "")
            proxy_token = request.headers.get("X-Internal-Proxy-Token", "")

            if not proxy_secret or not proxy_token:
                return jsonify({"error": "Unauthorized"}), 401

            if not hmac.compare_digest(proxy_secret, proxy_token):
                return jsonify({"error": "Unauthorized"}), 401

            guest_id = request.headers.get("X-Guest-ID")
            if not is_valid_uuid_v4(guest_id):
                return jsonify({"error": "Unauthorized"}), 401

            g.user_id = f"guest:{guest_id.lower()}"
            return f(*args, **kwargs)

        token = auth_header.split(" ")[1]
        try:
            jwks_client = jwt.PyJWKClient(JWKS_URL)
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            data = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                options={"verify_aud": False}
            )
            sub = data.get("sub")
            if not isinstance(sub, str) or not sub.strip():
                return jsonify({"error": "Unauthorized"}), 401
            g.user_id = sub.strip()
        except Exception:
            return jsonify({"error": "Unauthorized"}), 401

        return f(*args, **kwargs)
    return decorated
