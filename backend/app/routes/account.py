from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/account", tags=["account"])

_ADDRESSES = [{"id": 1, "street": "123 Roast St", "city": "SF", "postalCode": "94107"}]


@router.get("")
async def get_account():
    return {
        "name": "Alex Demo",
        "email": "demo@singleorigin.example",
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
