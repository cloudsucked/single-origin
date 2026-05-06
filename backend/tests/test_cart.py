from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.routes import cart as cart_module


client = TestClient(app)


def setup_function() -> None:
    cart_module._CART.clear()
    cart_module._CART["demo"] = cart_module.CartState()


def test_get_cart_does_not_create_new_session() -> None:
    response = client.get("/api/v1/cart?session=unknown")

    assert response.status_code == 200
    assert response.json() == {"session": "unknown", "items": []}
    assert "unknown" not in cart_module._CART


def test_add_cart_item_caps_items_per_session(monkeypatch) -> None:
    monkeypatch.setattr(settings, "cart_max_items_per_session", 2)

    for product_id in (1, 2, 3):
        response = client.post(
            "/api/v1/cart/items?session=bounded",
            json={"product_id": product_id, "quantity": 1},
        )
        assert response.status_code == 200

    items = response.json()["items"]
    assert [item["product_id"] for item in items] == [2, 3]


def test_cart_sessions_are_capped(monkeypatch) -> None:
    monkeypatch.setattr(settings, "cart_max_sessions", 3)
    monkeypatch.setattr(settings, "cart_ttl_seconds", 0)

    for session in ("a", "b", "c", "d"):
        response = client.post(
            f"/api/v1/cart/items?session={session}",
            json={"product_id": 1, "quantity": 1},
        )
        assert response.status_code == 200

    assert "demo" in cart_module._CART
    assert "a" not in cart_module._CART
    assert set(cart_module._CART) == {"demo", "c", "d"}


def test_cart_sessions_expire(monkeypatch) -> None:
    monkeypatch.setattr(settings, "cart_ttl_seconds", 1)

    cart_module._CART["old"] = cart_module.CartState(updated_at=0)
    cart_module._prune_carts(now=2)

    assert "old" not in cart_module._CART
    assert "demo" in cart_module._CART
