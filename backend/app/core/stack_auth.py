"""
Stack Auth JWT verification via JWKS for LibreWork.
Verifies ES256-signed access tokens using Stack Auth's public keys.
"""
import jwt
from jwt import PyJWKClient
from functools import lru_cache

from app.core.config import settings


@lru_cache()
def get_jwks_client() -> PyJWKClient:
    jwks_url = (
        f"https://api.stack-auth.com/api/v1/projects/"
        f"{settings.STACK_PROJECT_ID}/.well-known/jwks.json"
    )
    return PyJWKClient(jwks_url)


def verify_stack_auth_token(access_token: str) -> dict:
    """Verify a Stack Auth access token via JWKS. Returns decoded JWT payload.

    Raises:
        jwt.ExpiredSignatureError: Token has expired.
        jwt.InvalidTokenError: Token is malformed or signature is invalid.
    """
    jwks_client = get_jwks_client()
    signing_key = jwks_client.get_signing_key_from_jwt(access_token)
    payload = jwt.decode(
        access_token,
        signing_key.key,
        algorithms=["ES256"],
        audience=settings.STACK_PROJECT_ID,
    )
    return payload
