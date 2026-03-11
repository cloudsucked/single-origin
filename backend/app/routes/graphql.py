from __future__ import annotations

from fastapi import APIRouter, Response
from fastapi.responses import HTMLResponse

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
async def graphql_query(payload: dict, response: Response):
    response.headers[COMPLEXITY_HEADER] = str(score_graphql(payload))
    query = str(payload.get("query", ""))
    if "products" in query:
        products = list_products()[:20]
        return {
            "data": {
                "products": [
                    {"id": str(p["id"]), "name": p["name"], "slug": p["slug"]} for p in products
                ]
            }
        }
    if "product" in query:
        products = list_products()[:1]
        p = products[0] if products else {"id": 1, "name": "N/A", "slug": "n-a"}
        return {"data": {"product": {"id": str(p["id"]), "name": p["name"], "slug": p["slug"]}}}
    return {"data": {}, "errors": [{"message": "Unsupported query in MVP GraphQL handler"}]}
