from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.db import get_conn
from app.services.repository import (
    admin_dashboard_metrics,
    list_all_orders,
    list_all_subscriptions,
    list_products,
    list_users,
    set_order_status,
    set_subscription_status,
)
from app.services.security import require_admin

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


class StatusUpdate(BaseModel):
    status: str


class ProductWrite(BaseModel):
    name: str
    slug: str
    origin: str | None = None
    roast_level: str | None = None
    category: str = "beans"
    description: str
    price: float


@router.get("/dashboard")
async def dashboard(_: dict = Depends(require_admin)):
    return admin_dashboard_metrics()


@router.get("/users")
async def users(_: dict = Depends(require_admin)):
    return list_users()


@router.get("/products")
async def products(_: dict = Depends(require_admin)):
    return list_products()


@router.post("/products")
async def create_product(payload: ProductWrite, _: dict = Depends(require_admin)):
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO products (name, slug, origin, roast_level, category, description, price)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.name,
                payload.slug,
                payload.origin,
                payload.roast_level,
                payload.category,
                payload.description,
                payload.price,
            ),
        )
        row = conn.execute(
            "SELECT id, name, slug, origin, roast_level, category, description, price FROM products WHERE slug = ?",
            (payload.slug,),
        ).fetchone()
    return dict(row)


@router.put("/products/{product_id}")
async def update_product(product_id: int, payload: ProductWrite, _: dict = Depends(require_admin)):
    with get_conn() as conn:
        cursor = conn.execute(
            """
            UPDATE products
            SET name = ?, slug = ?, origin = ?, roast_level = ?, category = ?, description = ?, price = ?
            WHERE id = ?
            """,
            (
                payload.name,
                payload.slug,
                payload.origin,
                payload.roast_level,
                payload.category,
                payload.description,
                payload.price,
                product_id,
            ),
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="product_not_found")
    return {"updated": True, "id": product_id}


@router.delete("/products/{product_id}")
async def delete_product(product_id: int, _: dict = Depends(require_admin)):
    with get_conn() as conn:
        cursor = conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="product_not_found")
    return {"deleted": True, "id": product_id}


@router.get("/orders")
async def orders(_: dict = Depends(require_admin)):
    return list_all_orders()


@router.patch("/orders/{order_id}/status")
async def order_status(order_id: int, payload: StatusUpdate, _: dict = Depends(require_admin)):
    if not set_order_status(order_id, payload.status):
        raise HTTPException(status_code=404, detail="order_not_found")
    return {"updated": True, "id": order_id, "status": payload.status}


@router.get("/subscriptions")
async def subscriptions(_: dict = Depends(require_admin)):
    return list_all_subscriptions()


@router.patch("/subscriptions/{subscription_id}/status")
async def subscription_status(subscription_id: int, payload: StatusUpdate, _: dict = Depends(require_admin)):
    if not set_subscription_status(subscription_id, payload.status):
        raise HTTPException(status_code=404, detail="subscription_not_found")
    return {"updated": True, "id": subscription_id, "status": payload.status}


@router.get("/audit-logs")
async def audit_logs(_: dict = Depends(require_admin)):
    return [
        {"id": "evt_1", "actor": "admin@singleorigin.example", "action": "LOGIN", "severity": "info"},
        {"id": "evt_2", "actor": "admin@singleorigin.example", "action": "UPDATE_PRODUCT", "severity": "low"},
        {"id": "evt_3", "actor": "admin@singleorigin.example", "action": "REFUND_ORDER", "severity": "medium"},
    ]
