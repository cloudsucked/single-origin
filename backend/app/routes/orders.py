from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.db import get_conn
from app.services.repository import get_order, list_orders_for_user
from app.services.security import require_admin

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])


class OrderItemWrite(BaseModel):
    product_id: int
    quantity: int
    name: str = ""
    price: float = 0.0


class PlaceOrderRequest(BaseModel):
    email: str = "demo@singleorigin.example"
    items: list[OrderItemWrite] = []
    billing_address: str = ""
    card_last4: str = "0000"
    phone: str = ""
    total: float = 0.0


@router.post("")
async def place_order(payload: PlaceOrderRequest):
    with get_conn() as conn:
        cursor = conn.execute(
            """
            INSERT INTO orders (user_email, total, status, billing_address, card_last4, phone)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                payload.email,
                payload.total,
                "PROCESSING",
                payload.billing_address,
                payload.card_last4[-4:] if len(payload.card_last4) >= 4 else payload.card_last4,
                payload.phone,
            ),
        )
        order_id = cursor.lastrowid or 0
    order = get_order(order_id)
    return {"status": "placed", "order": order}


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
