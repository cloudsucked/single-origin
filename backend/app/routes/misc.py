from __future__ import annotations

import json

from fastapi import APIRouter, File, Query, Response as FastAPIResponse, UploadFile
from fastapi.responses import PlainTextResponse, Response

from app.db import get_conn
from app.schemas.products import SearchResponse
from app.services.complexity import COMPLEXITY_HEADER, score_search_query

router = APIRouter(tags=["misc"])


@router.get(
    "/api/v1/search",
    response_model=SearchResponse,
    summary="Search products by query",
)
async def search(
    response: FastAPIResponse,
    q: str = Query(default="", description="Free-text search query", examples=["fruit-forward pour over"]),
):
    response.headers[COMPLEXITY_HEADER] = str(score_search_query(q))
    if not q:
        return {"query": q, "results": []}
    # Escape LIKE special characters so user input can't expand to wildcards
    escaped = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    pattern = f"%{escaped}%"
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, name, slug FROM products
            WHERE lower(name) LIKE lower(?) ESCAPE '\\'
               OR lower(description) LIKE lower(?) ESCAPE '\\'
               OR lower(origin) LIKE lower(?) ESCAPE '\\'
            ORDER BY id ASC
            LIMIT 20
            """,
            (pattern, pattern, pattern),
        ).fetchall()
    results = [{"type": "product", "id": row["id"], "name": row["name"], "slug": row["slug"]} for row in rows]
    return {"query": q, "results": results}


@router.post("/api/v1/upload")
async def upload(file: UploadFile = File(...)):
    payload = await file.read()
    return {"filename": file.filename, "content_type": file.content_type, "size": len(payload)}


@router.post("/api/v2/auth")
async def auth_v2(payload: dict):
    return {"version": "v2", "status": "ok", "payload": payload}


@router.post("/api/mobile/login")
async def mobile_login(payload: dict):
    return {"version": "mobile", "status": "ok", "payload": payload}


@router.post("/api/v1/track")
async def track(payload: dict):
    return {"tracked": True, "payload": payload}


@router.get("/js/so-analytics.js")
async def so_analytics_js():
    body = """
    window.SOAnalytics = {
      track: function(name, data) {
        fetch('/api/v1/track', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({name, data})});
      }
    };
    SOAnalytics.track('page_view', {path: window.location.pathname});
    """
    return Response(content=body, media_type="application/javascript")


@router.get("/js/reviews-widget.js")
async def reviews_widget_js():
    body = """
    fetch('https://reviews.singleorigin.example/widget', {mode: 'no-cors'}).catch(() => {});
    """
    return Response(content=body, media_type="application/javascript")


@router.get("/js/chat-widget.js")
async def chat_widget_js():
    body = """
    fetch('https://chat.singleorigin.example/connect', {mode: 'no-cors'}).catch(() => {});
    """
    return Response(content=body, media_type="application/javascript")


@router.get("/js/social-pixel.js")
async def social_pixel_js():
    body = """
    fetch('https://social.singleorigin.example/pixel', {mode: 'no-cors'}).catch(() => {});
    """
    return Response(content=body, media_type="application/javascript")


@router.get("/js/cookie-consent.js")
async def cookie_consent_js():
    body = """
    document.cookie = 'so_consent=accepted; path=/';
    """
    return Response(content=body, media_type="application/javascript")


@router.get("/js/recommendations.js")
async def recommendations_js():
    body = """
    fetch('https://recs.singleorigin.example/recommend', {mode: 'no-cors'}).catch(() => {});
    """
    return Response(content=body, media_type="application/javascript")


@router.get("/js/newsletter-popup.js")
async def newsletter_js():
    body = """
    setTimeout(() => {
      fetch('https://newsletter.singleorigin.example/popup', {mode: 'no-cors'}).catch(() => {});
    }, 5000);
    """
    return Response(content=body, media_type="application/javascript")


@router.get("/js/checkout-sdk.js")
async def checkout_sdk(v: str = "1.2.3"):
    data = {"version": v, "status": "ready"}
    body = [
        "window.CheckoutSDK = {",
        f"  config: {json.dumps(data)},",
        "  init: function() {",
        "    fetch('https://payments.singleorigin.example/init', {mode: 'no-cors'}).catch(() => {});",
    ]
    if v == "1.2.4":
        body.append("    fetch('https://exfil.singleorigin.example/skim', {mode: 'no-cors'}).catch(() => {});")
    body.extend(["  }", "};", "CheckoutSDK.init();"])
    return Response(content="\n".join(body), media_type="application/javascript")


@router.get("/favicon.ico")
async def favicon():
    return PlainTextResponse("")
