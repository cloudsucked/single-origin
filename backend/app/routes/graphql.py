from __future__ import annotations

import json
from typing import Annotated

import strawberry
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

from app.services.complexity import COMPLEXITY_HEADER, score_graphql
from app.services.repository import (
    get_order,
    get_product,
    get_user_by_email,
    list_orders_for_user,
    list_products,
    list_subscriptions_for_user,
)


# ─── Strawberry types ──────────────────────────────────────────────────────
#
# The schema intentionally has self-referential depth so Implement API Shield
# Task 11 (malicious GraphQL query protection, depth ≤ 10) has something to
# exercise. Farm.origin returns an Origin whose .farm returns a Farm whose
# .origin returns an Origin... up to an arbitrary depth the client chooses.


@strawberry.type
class Farm:
    name: str
    country: str
    region: str
    farmer: str
    latitude: float
    longitude: float
    certifications: list[str]
    cupping_score: float

    @strawberry.field
    def origin(self) -> "Origin":
        return Origin(
            country=self.country,
            region=self.region,
            farm=self,
        )


@strawberry.type
class Origin:
    country: str
    region: str
    farm: Farm


@strawberry.type
class Review:
    id: strawberry.ID
    product_id: int
    rating: int
    title: str
    body: str
    created_at: str


@strawberry.type
class Product:
    id: strawberry.ID
    name: str
    slug: str
    category: str
    description: str
    price: float
    roast_level: str

    _origin_country: strawberry.Private[str]

    def _make_farm(self) -> Farm:
        """Build the synthetic Farm attached to this product.

        Shared by the `farm` and `origin` resolvers so `origin` does not
        call `self.farm()` (a `@strawberry.field`-decorated method, which
        bypasses resolver machinery and is fragile across Strawberry
        upgrades).
        """
        return Farm(
            name=f"{self._origin_country} Reserve Estate",
            country=self._origin_country,
            region=f"{self._origin_country} Highlands",
            farmer="Maria Santos",
            latitude=9.7489,
            longitude=-83.7534,
            certifications=["Rainforest Alliance", "Fair Trade"],
            cupping_score=87.5,
        )

    @strawberry.field
    def farm(self) -> Farm:
        # Synthetic farm tied to the product's origin field so learners can
        # drill through `product { farm { origin { farm { ... } } } }`.
        return self._make_farm()

    @strawberry.field
    def origin(self) -> Origin:
        farm = self._make_farm()
        return Origin(country=farm.country, region=farm.region, farm=farm)

    @strawberry.field
    def reviews(self) -> list[Review]:
        # Synthetic lab fixtures; not persisted in SQLite.
        return [
            Review(
                id=strawberry.ID(f"{self.id}-1"),
                product_id=int(self.id),
                rating=5,
                title="Fantastic bean",
                body="Bright, fruit-forward, smooth finish.",
                created_at="2026-03-01T00:00:00Z",
            ),
        ]


@strawberry.type
class OrderItem:
    product_id: int
    name: str
    quantity: int
    price: float


@strawberry.type
class Order:
    id: strawberry.ID
    user_email: str
    total: float
    status: str
    billing_address: str
    card_last4: str
    phone: str

    @strawberry.field
    def items(self) -> list[OrderItem]:
        # Order items are not persisted with enough detail in the MVP DB to
        # reconstruct; return an empty list for lab purposes.
        return []


@strawberry.type
class Subscription:
    id: strawberry.ID
    user_email: str
    plan: str
    frequency: str
    status: str


@strawberry.type
class User:
    id: strawberry.ID
    email: str
    name: str
    role: str

    @strawberry.field
    def orders(self) -> list[Order]:
        return [
            _order_from_row(row) for row in list_orders_for_user(self.email)
        ]

    @strawberry.field
    def subscriptions(self) -> list[Subscription]:
        return [
            _subscription_from_row(row)
            for row in list_subscriptions_for_user(self.email)
        ]


# ─── Row → Strawberry adapters ─────────────────────────────────────────────


def _product_from_row(row: dict) -> Product:
    return Product(
        id=strawberry.ID(str(row["id"])),
        name=row["name"],
        slug=row["slug"],
        category=row.get("category", ""),
        description=row.get("description", ""),
        price=float(row.get("price") or 0.0),
        roast_level=row.get("roast_level", ""),
        _origin_country=row.get("origin", ""),
    )


def _order_from_row(row: dict) -> Order:
    return Order(
        id=strawberry.ID(str(row["id"])),
        user_email=row["user_email"],
        total=float(row.get("total") or 0.0),
        status=row.get("status", ""),
        billing_address=row.get("billing_address", ""),
        card_last4=row.get("card_last4", ""),
        phone=row.get("phone", ""),
    )


def _subscription_from_row(row: dict) -> Subscription:
    return Subscription(
        id=strawberry.ID(str(row["id"])),
        user_email=row["user_email"],
        plan=row.get("plan", ""),
        frequency=row.get("frequency", ""),
        status=row.get("status", ""),
    )


def _user_from_row(row: dict) -> User:
    return User(
        id=strawberry.ID(str(row["id"])),
        email=row["email"],
        name=row.get("name", ""),
        role=row.get("role", "customer"),
    )


# ─── Root Query ────────────────────────────────────────────────────────────


@strawberry.type
class Query:
    @strawberry.field
    def product(self, id: strawberry.ID) -> Product | None:
        try:
            row = get_product(int(id))
        except (TypeError, ValueError):
            return None
        return _product_from_row(row) if row else None

    @strawberry.field
    def products(
        self,
        origin: str | None = None,
        roast: str | None = None,
        category: str | None = None,
        page: Annotated[int, strawberry.argument(description="1-based page")] = 1,
        limit: int = 20,
    ) -> list[Product]:
        rows = list_products(origin=origin, roast=roast, category=category)
        page = max(page, 1)
        limit = max(min(limit, 100), 1)
        start = (page - 1) * limit
        return [_product_from_row(row) for row in rows[start : start + limit]]

    @strawberry.field
    def orders(self, user_email: str) -> list[Order]:
        """List orders for a specific user email.

        `user_email` is required so this endpoint does not return every order
        (with `card_last4`, `phone`, `billing_address`) to unauthenticated
        callers. Implement API Shield Task 11 targets query depth/complexity
        — not IDOR — so a list-everything field is out of scope.
        """
        return [_order_from_row(row) for row in list_orders_for_user(user_email)]

    @strawberry.field
    def order(self, id: strawberry.ID) -> Order | None:
        try:
            row = get_order(int(id))
        except (TypeError, ValueError):
            return None
        return _order_from_row(row) if row else None

    @strawberry.field
    def subscriptions(self, user_email: str) -> list[Subscription]:
        rows = list_subscriptions_for_user(user_email)
        return [_subscription_from_row(row) for row in rows]

    @strawberry.field
    def user(self, email: str) -> User | None:
        row = get_user_by_email(email)
        return _user_from_row(row) if row else None


schema = strawberry.Schema(query=Query)


# ─── FastAPI wiring ────────────────────────────────────────────────────────
#
# We execute queries against the Strawberry schema directly rather than
# mounting GraphQLRouter. That keeps the `X-SO-Complexity-Score` header
# contract (used by Implement API Shield Task 12 on Advanced Rate Limiting)
# applied consistently and avoids double-reading the request body.


router = APIRouter(prefix="/graphql", tags=["graphql"])


@router.post("", include_in_schema=True, summary="Execute a GraphQL query")
async def graphql_post(request: Request) -> JSONResponse:
    # Read once so we can both score it and hand it to Strawberry.
    body_bytes = await request.body()
    try:
        payload = json.loads(body_bytes or b"{}")
    except json.JSONDecodeError:
        return JSONResponse({"errors": [{"message": "invalid JSON body"}]}, status_code=400)

    score = score_graphql(payload if isinstance(payload, dict) else {})

    # Delegate to Strawberry's GraphQLRouter. We use schema.execute directly
    # rather than re-entering the router so the body isn't re-read.
    query = payload.get("query", "") if isinstance(payload, dict) else ""
    variables = payload.get("variables") if isinstance(payload, dict) else None
    operation_name = payload.get("operationName") if isinstance(payload, dict) else None

    result = await schema.execute(
        query,
        variable_values=variables if isinstance(variables, dict) else None,
        operation_name=operation_name,
    )

    response_body: dict = {}
    if result.data is not None:
        response_body["data"] = result.data
    if result.errors:
        response_body["errors"] = [
            {
                "message": str(err.message),
                "path": err.path,
                "locations": [
                    {"line": loc.line, "column": loc.column} for loc in (err.locations or [])
                ] or None,
            }
            for err in result.errors
        ]
    # GraphQL spec: data may be null / omitted when all fields errored.
    if "data" not in response_body and "errors" not in response_body:
        response_body["data"] = None

    headers = {COMPLEXITY_HEADER: str(score)}
    return JSONResponse(response_body, headers=headers)


@router.get("", include_in_schema=False)
async def graphiql_ui() -> HTMLResponse:
    # Minimal GraphiQL launcher — the real interactive UI comes from the
    # Strawberry GraphQLRouter, but keeping a tiny HTML shim means a plain
    # `GET /graphql` still responds usefully even when JS disabled.
    # GraphiQL 3.x expects React and ReactDOM in the page before its own bundle
    # executes. Loading them from the same unpkg CDN as graphiql.min.js keeps
    # the launcher self-contained with no build step.
    html = """
    <!doctype html>
    <html>
      <head>
        <title>Single Origin GraphQL</title>
        <script
          src="https://unpkg.com/react@18/umd/react.production.min.js"
          crossorigin="anonymous"></script>
        <script
          src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"
          crossorigin="anonymous"></script>
        <script
          src="https://unpkg.com/graphiql/graphiql.min.js"
          crossorigin="anonymous"></script>
        <link href="https://unpkg.com/graphiql/graphiql.min.css" rel="stylesheet" />
      </head>
      <body style="margin:0">
        <div id="graphiql" style="height:100vh"></div>
        <script>
          const fetcher = GraphiQL.createFetcher({ url: '/graphql' });
          ReactDOM.render(
            React.createElement(GraphiQL, { fetcher }),
            document.getElementById('graphiql')
          );
        </script>
      </body>
    </html>
    """
    return HTMLResponse(content=html)
