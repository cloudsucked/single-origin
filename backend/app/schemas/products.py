from __future__ import annotations

from pydantic import BaseModel


class Product(BaseModel):
    id: int
    name: str
    slug: str
    origin: str | None = None
    roast_level: str | None = None
    category: str
    description: str
    price: float


class ProductFarmCoordinates(BaseModel):
    lat: float
    lng: float


class ProductFarm(BaseModel):
    name: str
    coordinates: ProductFarmCoordinates
    farmer: str


class ProductDetail(Product):
    farm: ProductFarm


class ProductDeleteResponse(BaseModel):
    deleted: bool
    id: int


class ProductReview(BaseModel):
    id: int
    rating: int
    title: str
    body: str


class ProductReviewCreateResponse(BaseModel):
    status: str
    product_id: int
    review: dict


class SearchResult(BaseModel):
    type: str
    id: int
    name: str


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
