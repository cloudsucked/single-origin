from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr

from app.db import get_conn
from app.services.repository import (
    admin_dashboard_metrics,
    create_user,
    delete_user,
    get_user_by_email,
    get_user_by_id,
    list_all_orders,
    list_all_subscriptions,
    list_audit_logs,
    list_products,
    list_users,
    log_audit_event,
    set_order_status,
    set_subscription_status,
    update_user,
)
from app.services.security import require_admin

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _actor(admin: dict) -> str:
    return admin.get("email", "admin")


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

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


class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str
    role: str = "customer"


class UserUpdate(BaseModel):
    email: EmailStr
    name: str
    role: str


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@router.get("/dashboard", summary="Admin dashboard metrics")
async def dashboard(_: dict = Depends(require_admin)):
    return admin_dashboard_metrics()


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

@router.get("/users", summary="List all users")
async def users(_: dict = Depends(require_admin)):
    return list_users()


@router.post("/users", summary="Create a user")
async def create_user_admin(payload: UserCreate, admin: dict = Depends(require_admin)):
    if get_user_by_email(payload.email):
        raise HTTPException(status_code=409, detail="email_already_exists")
    user = create_user(payload.email, payload.password, payload.name, payload.role)
    log_audit_event(
        actor=_actor(admin),
        action="CREATE_USER",
        target_type="user",
        target_id=str(user["id"]),
        severity="low",
    )
    return user


@router.put("/users/{user_id}", summary="Update a user")
async def update_user_admin(user_id: int, payload: UserUpdate, admin: dict = Depends(require_admin)):
    if not get_user_by_id(user_id):
        raise HTTPException(status_code=404, detail="user_not_found")
    existing = get_user_by_email(payload.email)
    if existing and existing["id"] != user_id:
        raise HTTPException(status_code=409, detail="email_already_exists")
    if not update_user(user_id, payload.email, payload.name, payload.role):
        raise HTTPException(status_code=404, detail="user_not_found")
    log_audit_event(
        actor=_actor(admin),
        action="UPDATE_USER",
        target_type="user",
        target_id=str(user_id),
        severity="low",
    )
    return get_user_by_id(user_id)


@router.delete("/users/{user_id}", summary="Delete a user")
async def delete_user_admin(user_id: int, admin: dict = Depends(require_admin)):
    if not delete_user(user_id):
        raise HTTPException(status_code=404, detail="user_not_found")
    log_audit_event(
        actor=_actor(admin),
        action="DELETE_USER",
        target_type="user",
        target_id=str(user_id),
        severity="medium",
    )
    return {"deleted": True, "id": user_id}


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

@router.get("/products", summary="List all products")
async def products(_: dict = Depends(require_admin)):
    return list_products()


@router.post("/products", summary="Create a product")
async def create_product(payload: ProductWrite, admin: dict = Depends(require_admin)):
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
    product = dict(row)
    log_audit_event(
        actor=_actor(admin),
        action="CREATE_PRODUCT",
        target_type="product",
        target_id=str(product["id"]),
        severity="low",
    )
    return product


@router.put("/products/{product_id}", summary="Update a product")
async def update_product(product_id: int, payload: ProductWrite, admin: dict = Depends(require_admin)):
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
    log_audit_event(
        actor=_actor(admin),
        action="UPDATE_PRODUCT",
        target_type="product",
        target_id=str(product_id),
        severity="low",
    )
    return {"updated": True, "id": product_id}


@router.delete("/products/{product_id}", summary="Delete a product")
async def delete_product(product_id: int, admin: dict = Depends(require_admin)):
    with get_conn() as conn:
        cursor = conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="product_not_found")
    log_audit_event(
        actor=_actor(admin),
        action="DELETE_PRODUCT",
        target_type="product",
        target_id=str(product_id),
        severity="medium",
    )
    return {"deleted": True, "id": product_id}


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------

@router.get("/orders", summary="List all orders")
async def orders(_: dict = Depends(require_admin)):
    return list_all_orders()


@router.patch("/orders/{order_id}/status", summary="Update order status")
async def order_status(order_id: int, payload: StatusUpdate, admin: dict = Depends(require_admin)):
    if not set_order_status(order_id, payload.status):
        raise HTTPException(status_code=404, detail="order_not_found")
    log_audit_event(
        actor=_actor(admin),
        action=f"SET_ORDER_STATUS_{payload.status}",
        target_type="order",
        target_id=str(order_id),
        severity="info",
    )
    return {"updated": True, "id": order_id, "status": payload.status}


# ---------------------------------------------------------------------------
# Subscriptions
# ---------------------------------------------------------------------------

@router.get("/subscriptions", summary="List all subscriptions")
async def subscriptions(_: dict = Depends(require_admin)):
    return list_all_subscriptions()


@router.patch("/subscriptions/{subscription_id}/status", summary="Update subscription status")
async def subscription_status(subscription_id: int, payload: StatusUpdate, admin: dict = Depends(require_admin)):
    if not set_subscription_status(subscription_id, payload.status):
        raise HTTPException(status_code=404, detail="subscription_not_found")
    log_audit_event(
        actor=_actor(admin),
        action=f"SET_SUBSCRIPTION_STATUS_{payload.status}",
        target_type="subscription",
        target_id=str(subscription_id),
        severity="info",
    )
    return {"updated": True, "id": subscription_id, "status": payload.status}


# ---------------------------------------------------------------------------
# Audit logs
# ---------------------------------------------------------------------------

@router.get("/audit-logs", summary="List audit log entries")
async def audit_logs(_: dict = Depends(require_admin)):
    return list_audit_logs(limit=100)
