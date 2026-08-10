import os
import jwt
import requests
from functools import lru_cache
from flask import request, jsonify, g
from functools import wraps

# Your Clerk publishable key can be used to construct the domain
# But it's easier to just decode without verifying signature in development,
# OR fetch the JWKS from the Clerk Frontend API.
CLERK_SECRET = os.getenv("CLERK_SECRET_KEY")

# Extract domain from the publishable key
import base64
pk = os.getenv("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY", "pk_test_bWFueS1sb3VzZS04Ny5jbGVyay5hY2NvdW50cy5kZXYk")
if pk.startswith("pk_test_") or pk.startswith("pk_live_"):
    try:
        domain_b64 = pk.split("_")[-1].strip("$")
        # Add padding if necessary
        domain_b64 += "=" * ((4 - len(domain_b64) % 4) % 4)
        domain = base64.b64decode(domain_b64).decode("utf-8")
        if domain.endswith("$"):
            domain = domain[:-1]
        JWKS_URL = f"https://{domain}/.well-known/jwks.json"
    except Exception:
        JWKS_URL = None
else:
    JWKS_URL = None

@lru_cache(maxsize=1)
def get_jwks():
    if not JWKS_URL:
        return None
    r = requests.get(JWKS_URL)
    r.raise_for_status()
    return r.json()

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method == "OPTIONS" or request.path == "/":
            return f(*args, **kwargs)
            
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Unauthorized", "message": "Token de autenticação não fornecido."}), 401
            
        token = auth_header.split(" ")[1]
        try:
            # We use pyjwt with the PyJWKClient to verify
            jwks_client = jwt.PyJWKClient(JWKS_URL)
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            data = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                options={"verify_aud": False}
            )
            g.user_id = data.get("sub")
        except Exception as e:
            print("JWT Verification failed:", e)
            return jsonify({"error": "Unauthorized", "message": str(e)}), 401
            
        return f(*args, **kwargs)
    return decorated
