from pathlib import Path
import os
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from app.db import init_db, seed_db
from app.main import app

init_db()
seed_db()

client = TestClient(app)


def _admin_headers() -> dict:
    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": os.environ["SEED_ADMIN_EMAIL"],
            "password": os.environ["SEED_ADMIN_PASSWORD"],
        },
    )
    token = login.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_product_mutations_require_admin() -> None:
    payload = {
        "name": "Admin Only",
        "slug": "admin-only",
        "origin": "Test",
        "roast_level": "medium",
        "category": "beans",
        "description": "admin protected",
        "price": 12.5,
    }
    response = client.post("/api/v1/products", json=payload)
    assert response.status_code == 401


def test_order_mutations_require_admin() -> None:
    response = client.post("/api/v1/orders", json={"items": []})
    assert response.status_code == 401


def test_admin_can_mutate_products_and_orders() -> None:
    headers = _admin_headers()

    create_product = client.post(
        "/api/v1/products",
        json={
            "name": "Admin Created",
            "slug": "admin-created",
            "origin": "Kenya",
            "roast_level": "light",
            "category": "beans",
            "description": "created by admin",
            "price": 23,
        },
        headers=headers,
    )
    assert create_product.status_code == 200

    place_order = client.post("/api/v1/orders", json={"items": [{"product_id": 1, "quantity": 1}]}, headers=headers)
    assert place_order.status_code == 200
