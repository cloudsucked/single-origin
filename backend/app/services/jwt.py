"""JWT signing and verification helpers.

In dev mode (LAB_JWT_PRIVATE_KEY not set) the app uses HS256 with a symmetric
secret. In lab mode (LAB_JWT_PRIVATE_KEY set) it switches to RS256 using a
fixed RSA-2048 key pair so traffic-generator probes can carry pre-signed static
tokens that Cloudflare API Shield JWT Validation can verify via the JWKS
endpoint without requiring live per-pod authentication.
"""
from __future__ import annotations

import base64
from functools import lru_cache

from jose import jwt

from app.config import settings

_LAB_KEY_ID = "lab-static-key-v1"


@lru_cache(maxsize=1)
def _get_private_key_pem() -> str:
    """Return the lab RSA private key PEM, normalising \\n escape sequences."""
    raw = settings.lab_jwt_private_key
    if not raw:
        return ""
    # Env vars delivered via Terraform store newlines as literal \n sequences
    return raw.replace("\\n", "\n")


def lab_mode() -> bool:
    """Return True when RS256 lab mode is active."""
    return bool(_get_private_key_pem())


@lru_cache(maxsize=1)
def _get_public_key():  # type: ignore[return]
    """Return the parsed RSA public key object (cached after first call)."""
    from cryptography.hazmat.primitives.serialization import load_pem_private_key  # type: ignore[import]

    pem = _get_private_key_pem()
    if not pem:
        return None
    private_key = load_pem_private_key(pem.encode(), password=None)
    return private_key.public_key()  # type: ignore[union-attr]


def _int_to_base64url(n: int) -> str:
    length = (n.bit_length() + 7) // 8
    return base64.urlsafe_b64encode(n.to_bytes(length, "big")).rstrip(b"=").decode()


def issue_token(user: dict) -> str:
    """Issue a signed JWT for the given user dict."""
    from datetime import UTC, datetime, timedelta

    now = datetime.now(UTC)
    claims = {
        "sub": str(user["id"]),
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "iss": "single-origin",
        "aud": "single-origin-api",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=1)).timestamp()),
    }
    if lab_mode():
        return jwt.encode(
            claims,
            _get_private_key_pem(),
            algorithm="RS256",
            headers={"kid": _LAB_KEY_ID},
        )
    return jwt.encode(claims, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    """Decode and verify a JWT using the active signing scheme."""
    if lab_mode():
        return jwt.decode(
            token,
            _get_public_key(),  # type: ignore[arg-type]
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
        options={"verify_aud": False},
    )


def build_jwks() -> dict:
    """Return the JWKS for the active signing key.

    In lab mode serves the RSA public key for Cloudflare API Shield JWT
    Validation. In HS256 dev mode returns an empty key set (JWKS not applicable).
    """
    if not lab_mode():
        return {"keys": []}

    from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers  # type: ignore[import]

    pub_numbers: RSAPublicNumbers = _get_public_key().public_numbers()  # type: ignore[assignment,union-attr]
    return {
        "keys": [
            {
                "kty": "RSA",
                "use": "sig",
                "alg": "RS256",
                "kid": _LAB_KEY_ID,
                "n": _int_to_base64url(pub_numbers.n),
                "e": _int_to_base64url(pub_numbers.e),
            }
        ]
    }
