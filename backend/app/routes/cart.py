from __future__ import annotations

from dataclasses import dataclass, field
from time import monotonic

from fastapi import APIRouter
from pydantic import BaseModel

from app.config import settings

router = APIRouter(prefix="/api/v1/cart", tags=["cart"])


@dataclass
class CartState:
    items: list[dict] = field(default_factory=list)
    updated_at: float = field(default_factory=monotonic)


_CART: dict[str, CartState] = {"demo": CartState()}


class CartItemWrite(BaseModel):
    product_id: int
    quantity: int = 1
    name: str = ""
    price: float = 0.0


def _prune_carts(now: float | None = None) -> None:
    current = monotonic() if now is None else now
    ttl = max(settings.cart_ttl_seconds, 0)
    if ttl > 0:
        for session, cart in list(_CART.items()):
            if session != "demo" and current - cart.updated_at > ttl:
                del _CART[session]

    max_sessions = max(settings.cart_max_sessions, 1)
    excess = len(_CART) - max_sessions
    if excess <= 0:
        return

    oldest_sessions = sorted(
        (entry for entry in _CART.items() if entry[0] != "demo"),
        key=lambda entry: entry[1].updated_at,
    )
    for session, _ in oldest_sessions[:excess]:
        del _CART[session]


def _get_existing_cart(session: str) -> CartState | None:
    _prune_carts()
    cart = _CART.get(session)
    if cart:
        cart.updated_at = monotonic()
    return cart


def _get_or_create_cart(session: str) -> CartState:
    cart = _get_existing_cart(session)
    if cart is None:
        _prune_carts()
        max_sessions = max(settings.cart_max_sessions, 1)
        excess = len(_CART) - max_sessions + 1
        if excess > 0:
            oldest_sessions = sorted(
                (entry for entry in _CART.items() if entry[0] != "demo"),
                key=lambda entry: entry[1].updated_at,
            )
            for old_session, _ in oldest_sessions[:excess]:
                del _CART[old_session]
        cart = CartState()
        _CART[session] = cart
    return cart


@router.get("")
async def get_cart(session: str = "demo"):
    cart = _get_existing_cart(session)
    return {"session": session, "items": cart.items if cart else []}


@router.post("/items")
async def add_cart_item(payload: CartItemWrite, session: str = "demo"):
    cart = _get_or_create_cart(session)
    cart.items.append(payload.model_dump())
    max_items = max(settings.cart_max_items_per_session, 1)
    if len(cart.items) > max_items:
        del cart.items[: len(cart.items) - max_items]
    cart.updated_at = monotonic()
    return {"session": session, "items": cart.items}


@router.put("/items/{item_id}")
async def update_cart_item(item_id: int, payload: CartItemWrite, session: str = "demo"):
    cart = _get_existing_cart(session)
    if cart is None:
        return {"session": session, "items": []}
    if 0 <= item_id < len(cart.items):
        cart.items[item_id] = payload.model_dump()
    return {"session": session, "items": cart.items}


@router.delete("/items/{item_id}")
async def remove_cart_item(item_id: int, session: str = "demo"):
    cart = _get_existing_cart(session)
    if cart is None:
        return {"session": session, "items": []}
    if 0 <= item_id < len(cart.items):
        cart.items.pop(item_id)
    return {"session": session, "items": cart.items}


@router.delete("")
async def clear_cart(session: str = "demo"):
    if session == "demo":
        _CART["demo"] = CartState()
    else:
        _CART.pop(session, None)
    return {"session": session, "items": []}
