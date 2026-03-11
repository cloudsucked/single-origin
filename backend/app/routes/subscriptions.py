from __future__ import annotations

from fastapi import APIRouter

from app.services.repository import list_subscriptions_for_user

router = APIRouter(prefix="/api/v1/subscriptions", tags=["subscriptions"])


@router.get("")
async def list_subscriptions(email: str = "demo@singleorigin.example"):
    return list_subscriptions_for_user(email)


@router.post("")
async def create_subscription(payload: dict):
    return {"status": "created", "subscription": payload}


@router.get("/{subscription_id}")
async def get_subscription(subscription_id: int):
    return {"id": subscription_id, "plan": "Explorer", "status": "ACTIVE"}


@router.put("/{subscription_id}")
async def update_subscription(subscription_id: int, payload: dict):
    return {"id": subscription_id, "updated": True, "changes": payload}


@router.delete("/{subscription_id}")
async def cancel_subscription(subscription_id: int):
    return {"id": subscription_id, "status": "CANCELLED"}


@router.get("/{subscription_id}/shipments")
async def shipments(subscription_id: int):
    return {"id": subscription_id, "shipments": [{"date": "2026-03-01", "status": "upcoming"}]}
