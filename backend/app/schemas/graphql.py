from __future__ import annotations

from pydantic import BaseModel


class GraphQLRequest(BaseModel):
    query: str
    variables: dict | None = None


class GraphQLProduct(BaseModel):
    id: str
    name: str
    slug: str


class GraphQLProductsData(BaseModel):
    products: list[GraphQLProduct]


class GraphQLProductData(BaseModel):
    product: GraphQLProduct


class GraphQLError(BaseModel):
    message: str


class GraphQLResponse(BaseModel):
    data: dict
    errors: list[GraphQLError] | None = None
