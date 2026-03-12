from __future__ import annotations

from fastapi import APIRouter, Body, Response
from fastapi.responses import HTMLResponse

from app.schemas.graphql import GraphQLError, GraphQLRequest, GraphQLResponse
from app.services.complexity import COMPLEXITY_HEADER, score_graphql
from app.services.repository import list_products

router = APIRouter(prefix="/graphql", tags=["graphql"])


@router.get("")
async def graphiql() -> HTMLResponse:
    html = """
    <!doctype html>
    <html>
      <head><title>GraphiQL</title></head>
      <body>
        <h1>GraphQL Endpoint</h1>
        <p>POST JSON payloads with a <code>query</code> field to this endpoint.</p>
      </body>
    </html>
    """
    return HTMLResponse(content=html)


@router.post("")
async def graphql_query(
    response: Response,
    payload: GraphQLRequest = Body(
        ...,
        examples=[{"query": "query { products { id name slug } }"}],
    ),
) -> GraphQLResponse:
    payload_dict = payload.model_dump(exclude_none=True)
    response.headers[COMPLEXITY_HEADER] = str(score_graphql(payload_dict))
    query = payload.query
    if "products" in query:
        products = list_products()[:20]
        return GraphQLResponse(
            data={
                "products": [
                    {"id": str(p["id"]), "name": p["name"], "slug": p["slug"]} for p in products
                ]
            }
        )
    if "product" in query:
        products = list_products()[:1]
        p = products[0] if products else {"id": 1, "name": "N/A", "slug": "n-a"}
        return GraphQLResponse(data={"product": {"id": str(p["id"]), "name": p["name"], "slug": p["slug"]}})
    return GraphQLResponse(data={}, errors=[GraphQLError(message="Unsupported query in MVP GraphQL handler")])
