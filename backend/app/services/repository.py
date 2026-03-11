from __future__ import annotations

from app.db import get_conn


def get_user_by_email(email: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, email, password, name, role FROM users WHERE email = ?",
            (email,),
        ).fetchone()
    return dict(row) if row else None


def create_user(email: str, password: str, name: str, role: str = "customer") -> dict:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO users (email, password, name, role) VALUES (?, ?, ?, ?)",
            (email, password, name, role),
        )
        row = conn.execute(
            "SELECT id, email, name, role FROM users WHERE email = ?",
            (email,),
        ).fetchone()
    return dict(row)


def list_products(origin: str | None = None, roast: str | None = None, category: str | None = None) -> list[dict]:
    query = "SELECT id, name, slug, origin, roast_level, category, description, price FROM products WHERE 1=1"
    params: list[str] = []
    if origin:
        query += " AND lower(origin) = lower(?)"
        params.append(origin)
    if roast:
        query += " AND lower(roast_level) = lower(?)"
        params.append(roast)
    if category:
        query += " AND lower(category) = lower(?)"
        params.append(category)
    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def get_product(product_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, name, slug, origin, roast_level, category, description, price FROM products WHERE id = ?",
            (product_id,),
        ).fetchone()
    return dict(row) if row else None


def save_contact(name: str, email: str, message: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO contacts (name, email, message) VALUES (?, ?, ?)",
            (name, email, message),
        )


def list_orders_for_user(email: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, user_email, total, status, billing_address, card_last4, phone FROM orders WHERE user_email = ?",
            (email,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_order(order_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, user_email, total, status, billing_address, card_last4, phone FROM orders WHERE id = ?",
            (order_id,),
        ).fetchone()
    return dict(row) if row else None


def list_subscriptions_for_user(email: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, user_email, plan, frequency, status FROM subscriptions WHERE user_email = ?",
            (email,),
        ).fetchall()
    return [dict(row) for row in rows]


def list_users() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, email, name, role FROM users ORDER BY id ASC",
        ).fetchall()
    return [dict(row) for row in rows]


def list_all_orders() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, user_email, total, status, billing_address, card_last4, phone FROM orders ORDER BY id DESC",
        ).fetchall()
    return [dict(row) for row in rows]


def list_all_subscriptions() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, user_email, plan, frequency, status FROM subscriptions ORDER BY id DESC",
        ).fetchall()
    return [dict(row) for row in rows]


def set_order_status(order_id: int, status: str) -> bool:
    with get_conn() as conn:
        cursor = conn.execute(
            "UPDATE orders SET status = ? WHERE id = ?",
            (status, order_id),
        )
    return cursor.rowcount > 0


def set_subscription_status(subscription_id: int, status: str) -> bool:
    with get_conn() as conn:
        cursor = conn.execute(
            "UPDATE subscriptions SET status = ? WHERE id = ?",
            (status, subscription_id),
        )
    return cursor.rowcount > 0


def admin_dashboard_metrics() -> dict:
    with get_conn() as conn:
        users = conn.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"]
        products = conn.execute("SELECT COUNT(*) AS count FROM products").fetchone()["count"]
        orders = conn.execute("SELECT COUNT(*) AS count FROM orders").fetchone()["count"]
        subscriptions = conn.execute("SELECT COUNT(*) AS count FROM subscriptions").fetchone()["count"]
        contacts = conn.execute("SELECT COUNT(*) AS count FROM contacts").fetchone()["count"]
        revenue = conn.execute("SELECT COALESCE(SUM(total), 0) AS total FROM orders").fetchone()["total"]
    return {
        "users": users,
        "products": products,
        "orders": orders,
        "subscriptions": subscriptions,
        "contacts": contacts,
        "revenue": float(revenue),
    }
