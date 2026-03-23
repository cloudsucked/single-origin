from __future__ import annotations

from fastapi import Header, HTTPException
from jose import JWTError, jwt

from app.config import settings
from app.routes.auth import _get_lab_private_key, _lab_mode


def _decode_token(token: str) -> dict:
    """Decode and verify a JWT using the active signing scheme."""
    if _lab_mode():
        from cryptography.hazmat.primitives.serialization import load_pem_private_key  # type: ignore[import]

        private_key = load_pem_private_key(_get_lab_private_key().encode(), password=None)
        public_key = private_key.public_key()  # type: ignore[union-attr]
        return jwt.decode(
            token,
            public_key,  # type: ignore[arg-type]
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
        options={"verify_aud": False},
    )


def require_admin(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="missing_admin_token")

    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = _decode_token(token)
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="invalid_admin_token") from exc

    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="admin_role_required")
    return payload
