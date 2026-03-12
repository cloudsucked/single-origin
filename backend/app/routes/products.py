from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel

from app.db import get_conn
from app.schemas.common import DetailErrorResponse
from app.schemas.products import (
    Product,
    ProductDeleteResponse,
    ProductDetail,
    ProductReview,
    ProductReviewCreateResponse,
)
from app.services.repository import get_product, list_products
from app.services.security import require_admin

router = APIRouter(prefix="/api/v1/products", tags=["products"])


class ProductWrite(BaseModel):
    name: str
    slug: str
    origin: str | None = None
    roast_level: str | None = None
    category: str = "beans"
    description: str
    price: float


@router.get("", response_model=list[Product], summary="List products")
async def get_products(origin: str | None = None, roast: str | None = None, category: str | None = None):
    return list_products(origin=origin, roast=roast, category=category)


@router.get(
    "/{product_id}",
    response_model=ProductDetail,
    responses={404: {"model": DetailErrorResponse, "description": "Product not found."}},
    summary="Get product details",
)
async def get_product_detail(product_id: int):
    product = get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="product_not_found")
    product["farm"] = {
        "name": "Demo Farm",
        "coordinates": {"lat": 9.04, "lng": 38.74},
        "farmer": "Abebe Bekele",
    }
    return product


@router.post("", response_model=Product, summary="Create product")
async def create_product(
    payload: ProductWrite = Body(
        ...,
        examples=[
            {
                "name": "Ethiopia Guji Natural",
                "slug": "ethiopia-guji-natural",
                "origin": "Ethiopia",
                "roast_level": "light",
                "category": "beans",
                "description": "Blueberry and floral cup profile.",
                "price": 22.5,
            }
        ],
    ),
    _: dict = Depends(require_admin),
):
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


@router.put(
    "/{product_id}",
    response_model=Product,
    responses={404: {"model": DetailErrorResponse, "description": "Product not found."}},
    summary="Update product",
)
async def update_product(product_id: int, payload: ProductWrite, _: dict = Depends(require_admin)):
    with get_conn() as conn:
        conn.execute(
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
    product = get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="product_not_found")
    return product


@router.delete("/{product_id}", response_model=ProductDeleteResponse, summary="Delete product")
async def delete_product(product_id: int, _: dict = Depends(require_admin)):
    with get_conn() as conn:
        conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
    return {"deleted": True, "id": product_id}


@router.get("/{product_id}/reviews", response_model=list[ProductReview], summary="List product reviews")
async def list_reviews(product_id: int):
    _ = product_id
    return [{"id": 1, "rating": 5, "title": "Excellent", "body": "<b>Best coffee</b>"}]


@router.post("/{product_id}/reviews", response_model=ProductReviewCreateResponse, summary="Create product review")
async def create_review(product_id: int, payload: dict):
    return {"status": "accepted", "product_id": product_id, "review": payload}
