from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/cart", tags=["cart"])

_CART: dict[str, list[dict]] = {"demo": []}


class CartItemWrite(BaseModel):
    product_id: int
    quantity: int = 1
    name: str = ""
    price: float = 0.0


@router.get("")
async def get_cart(session: str = "demo"):
    return {"session": session, "items": _CART.get(session, [])}


@router.post("/items")
async def add_cart_item(payload: CartItemWrite, session: str = "demo"):
    _CART.setdefault(session, []).append(payload.model_dump())
    return {"session": session, "items": _CART[session]}


@router.put("/items/{item_id}")
async def update_cart_item(item_id: int, payload: CartItemWrite, session: str = "demo"):
    items = _CART.setdefault(session, [])
    if 0 <= item_id < len(items):
        items[item_id] = payload.model_dump()
    return {"session": session, "items": items}


@router.delete("/items/{item_id}")
async def remove_cart_item(item_id: int, session: str = "demo"):
    items = _CART.setdefault(session, [])
    if 0 <= item_id < len(items):
        items.pop(item_id)
    return {"session": session, "items": items}
