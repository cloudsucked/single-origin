from __future__ import annotations

from fastapi import Header, HTTPException
from jose import JWTError

from app.services.jwt import decode_token


def require_admin(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="missing_admin_token")

    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_token(token)
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="invalid_admin_token") from exc

    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="admin_role_required")
    return payload
