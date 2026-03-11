from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.services.repository import get_order, list_orders_for_user
from app.services.security import require_admin

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])


@router.post("")
async def place_order(payload: dict, _: dict = Depends(require_admin)):
    return {"status": "placed", "order": payload}


@router.get("")
async def list_orders(email: str = "demo@singleorigin.example"):
    return list_orders_for_user(email)


@router.get("/{order_id}")
async def order_detail(order_id: int):
    order = get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="order_not_found")
    return order


@router.get("/{order_id}/invoice")
async def order_invoice(order_id: int):
    return {"order_id": order_id, "invoice_url": f"/invoices/{order_id}.pdf"}


@router.post("/{order_id}/return")
async def order_return(order_id: int, payload: dict, _: dict = Depends(require_admin)):
    return {"order_id": order_id, "status": "return_initiated", "details": payload}
