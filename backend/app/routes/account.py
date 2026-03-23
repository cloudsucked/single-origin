from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from jose import JWTError, jwt

from app.config import settings
from app.services.repository import get_user_by_email

router = APIRouter(prefix="/api/v1/account", tags=["account"])

_ADDRESSES = [{"id": 1, "street": "123 Roast St", "city": "SF", "postalCode": "94107"}]


def _get_email_from_token(request: Request) -> str | None:
    """Return email from a valid Bearer JWT, None if no token present, or raise 401 if token is malformed/invalid."""
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth.removeprefix("Bearer ")
    try:
        claims = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            audience="single-origin-api",
        )
        return claims.get("email")
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="invalid_token") from exc


@router.get("")
async def get_account(request: Request):
    email = _get_email_from_token(request) or settings.seed_demo_email
    user = get_user_by_email(email)
    if user:
        return {
            "name": user["name"],
            "email": user["email"],
            "phone": "+1-555-0100",
            "payment_methods": [{"brand": "visa", "last4": "4242"}],
        }
    return {
        "name": "Alex Demo",
        "email": email,
        "phone": "+1-555-0100",
        "payment_methods": [{"brand": "visa", "last4": "4242"}],
    }


@router.put("")
async def update_account(payload: dict):
    return {"updated": True, "profile": payload}


@router.get("/addresses")
async def list_addresses():
    return _ADDRESSES


@router.post("/addresses")
async def add_address(payload: dict):
    payload = dict(payload)
    payload["id"] = max(a["id"] for a in _ADDRESSES) + 1 if _ADDRESSES else 1
    _ADDRESSES.append(payload)
    return payload


@router.delete("/addresses/{address_id}")
async def delete_address(address_id: int):
    global _ADDRESSES
    _ADDRESSES = [addr for addr in _ADDRESSES if addr["id"] != address_id]
    return {"deleted": True, "id": address_id}


@router.get("/taste-profile")
async def get_taste_profile():
    return {"roast": "medium", "methods": ["pour-over", "espresso"], "email": "demo@singleorigin.example"}


@router.put("/taste-profile")
async def update_taste_profile(payload: dict):
    return {"updated": True, "taste_profile": payload}
