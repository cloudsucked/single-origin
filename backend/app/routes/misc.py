from __future__ import annotations

import json

from fastapi import APIRouter, File, Query, Request, Response as FastAPIResponse, UploadFile
from fastapi.responses import JSONResponse, PlainTextResponse, Response

from app.config import settings
from app.db import get_conn
from app.schemas.products import SearchResponse
from app.services.complexity import COMPLEXITY_HEADER, score_search_query
from app.services.jwt import issue_token
from app.services.passwords import verify_password
from app.services.repository import get_user_by_email, public_user_dict

router = APIRouter(tags=["misc"])


@router.get(
    "/debug/headers",
    summary="Echo incoming request headers for mTLS managed-transform validation",
)
async def debug_headers(request: Request) -> dict[str, object]:
    """Return the full set of headers the origin received, unmodified.

    Used by Implement mTLS Task 8 to verify that Cloudflare's Managed Transform
    is forwarding the `Cf-Client-Cert-*` headers to the origin. No authentication
    or authorization; read-only; available on all four lab hostnames.

    Headers are returned in the order the ASGI server presents them, with
    original casing preserved via `request.headers.raw`. Values are not
    redacted — this endpoint is a debugging tool for lab pods, not a
    production endpoint.
    """
    raw_headers = [
        (key.decode("latin-1"), value.decode("latin-1"))
        for key, value in request.headers.raw
    ]
    return {
        "method": request.method,
        "path": request.url.path,
        "headers": [{"name": name, "value": value} for name, value in raw_headers],
    }


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


@router.post(
    "/api/v2/auth",
    response_model=None,
    summary="Alt-auth v2: JSON {username, password}",
)
async def auth_v2(payload: dict) -> dict[str, object] | JSONResponse:
    """Alt-auth JSON login for Traffic Detections custom detection locations.

    Body shape: `{"username": "...", "password": "..."}`. Returns 200 + JWT
    on success, 401 `{error: invalid_credentials}` on failure. The endpoint
    is deliberately non-standard (v2 namespace, JSON rather than form) so
    Traffic Detections Task 4 can teach `lookup_json_string(...)` detection
    locations against it.
    """
    username = payload.get("username") if isinstance(payload, dict) else None
    password = payload.get("password") if isinstance(payload, dict) else None
    if not username or not password:
        return JSONResponse({"error": "missing_credentials"}, status_code=400)
    user = get_user_by_email(username)
    if not user or not verify_password(password, user["password"]):
        return JSONResponse({"error": "invalid_credentials"}, status_code=401)
    user_dict = public_user_dict(user)
    return {"version": "v2", "token": issue_token(user_dict), "user": user_dict}


@router.post(
    "/api/mobile/login",
    response_model=None,
    summary="Alt-auth mobile: JSON {email, password}",
)
async def mobile_login(payload: dict) -> dict[str, object] | JSONResponse:
    """Alt-auth JSON login for Traffic Detections custom detection locations.

    Body shape: `{"email": "...", "password": "..."}`. Returns 200 + JWT
    on success, 401 `{error: invalid_credentials}` on failure. Field name
    is `email` (not `username`) deliberately — Traffic Detections Task 4
    Step 3b configures two separate detection locations to show learners
    how the `lookup_json_string` key differs between the two endpoints.
    """
    email = payload.get("email") if isinstance(payload, dict) else None
    password = payload.get("password") if isinstance(payload, dict) else None
    if not email or not password:
        return JSONResponse({"error": "missing_credentials"}, status_code=400)
    user = get_user_by_email(email)
    if not user or not verify_password(password, user["password"]):
        return JSONResponse({"error": "invalid_credentials"}, status_code=401)
    user_dict = public_user_dict(user)
    return {"version": "mobile", "token": issue_token(user_dict), "user": user_dict}


@router.post("/api/v1/track")
async def track(payload: dict):
    return {"tracked": True, "payload": payload}


@router.get("/js/so-analytics.js")
async def so_analytics_js():
    body = """
    (function () {
      var existing = (document.cookie.match(/(?:^|; )_so_analytics=([^;]+)/) || [])[1];
      if (!existing) {
        var id = 'ana_' + Math.random().toString(36).slice(2) + '_' + Date.now().toString(36);
        document.cookie = '_so_analytics=' + id + '; path=/; max-age=' + (60 * 60 * 24 * 30) + '; samesite=lax';
      }
    })();
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
    (function () {
      var existing = (document.cookie.match(/(?:^|; )_so_social=([^;]+)/) || [])[1];
      if (!existing) {
        var id = 'soc_' + Math.random().toString(36).slice(2);
        // 1 year expiry typical of third-party social tracking pixels
        document.cookie = '_so_social=' + id + '; path=/; max-age=' + (60 * 60 * 24 * 365) + '; samesite=lax';
      }
    })();
    fetch('https://social.singleorigin.example/pixel', {mode: 'no-cors'}).catch(() => {});
    """
    return Response(content=body, media_type="application/javascript")


@router.get("/js/cookie-consent.js")
async def cookie_consent_js():
    body = """
    (function () {
      var existing = (document.cookie.match(/(?:^|; )so_consent=([^;]+)/) || [])[1];
      if (!existing) {
        document.cookie = 'so_consent=accepted; path=/; max-age=' + (60 * 60 * 24 * 365) + '; samesite=lax';
      }
    })();
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


@router.get("/js/cart.js")
async def cart_js():
    """Seed the `so_cart` first-party cookie for Page Shield Cookie Monitor.

    Reads the SvelteKit-managed cart state from localStorage and mirrors it
    into a base64-encoded cookie. Runs once per page load; no-op if the cookie
    already matches the current cart. Purely lab-only observability surface —
    the real cart state continues to live in localStorage and server-side.
    """
    body = """
    (function () {
      try {
        var raw = localStorage.getItem('so:cart') || '[]';
        var encoded = btoa(unescape(encodeURIComponent(raw)));
        var existing = (document.cookie.match(/(?:^|; )so_cart=([^;]+)/) || [])[1];
        if (existing !== encoded) {
          document.cookie = 'so_cart=' + encoded + '; path=/; max-age=' + (60 * 60 * 24 * 30) + '; samesite=lax';
        }
      } catch (err) { /* swallow: lab fixture, not critical */ }
    })();
    """
    return Response(content=body, media_type="application/javascript")


@router.get("/js/prefs.js")
async def prefs_js():
    """Seed the `so_prefs` first-party cookie for Page Shield Cookie Monitor.

    Stores the learner's display and roast-level preferences as a JSON string.
    Default payload is written on first visit; subsequent visits leave the
    cookie intact so Account Preferences page can continue to update it.
    """
    body = """
    (function () {
      var existing = (document.cookie.match(/(?:^|; )so_prefs=([^;]+)/) || [])[1];
      if (!existing) {
        var prefs = JSON.stringify({roast: 'medium', display: 'grid', currency: 'USD'});
        var encoded = encodeURIComponent(prefs);
        document.cookie = 'so_prefs=' + encoded + '; path=/; max-age=' + (60 * 60 * 24 * 365) + '; samesite=lax';
      }
    })();
    """
    return Response(content=body, media_type="application/javascript")


@router.get("/js/checkout-sdk.js")
async def checkout_sdk(v: str = "1.2.3"):
    """Serve the safe (`v=1.2.3`) or compromised (`v=1.2.4`) checkout SDK.

    Page Shield Task 9 simulates a supply-chain attack by flipping the
    traffic-profile to request `v=1.2.4`, which includes an outbound fetch
    to the exfil URL configured via the `CHECKOUT_SDK_EXFIL_URL` env var
    (defaults to `https://exfil.{SLUG}.sxplab.com/skim` — the `{SLUG}`
    placeholder stays literal in the served JS so lab deployments that
    do not override the env var still produce an observably distinct
    outbound connection).
    """
    data = {"version": v, "status": "ready"}
    body = [
        "window.CheckoutSDK = {",
        f"  config: {json.dumps(data)},",
        "  init: function() {",
        "    fetch('https://payments.singleorigin.example/init', {mode: 'no-cors'}).catch(() => {});",
    ]
    if v == "1.2.4":
        exfil_url = settings.checkout_sdk_exfil_url
        body.append(
            f"    fetch({json.dumps(exfil_url)}, {{mode: 'no-cors'}}).catch(() => {{}});"
        )
    body.extend(["  }", "};", "CheckoutSDK.init();"])
    return Response(content="\n".join(body), media_type="application/javascript")


@router.get("/favicon.ico")
async def favicon():
    return PlainTextResponse("")
