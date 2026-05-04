from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, RedirectResponse

from app.config import settings
from app.db import init_db, seed_db
from app.openapi_compat import to_cloudflare_compatible
from app.routes.account import router as account_router
from app.routes.admin import router as admin_router
from app.routes.ai import router as ai_router
from app.routes.auth import form_router as auth_form_router
from app.routes.auth import router as auth_router
from app.routes.cart import router as cart_router
from app.routes.checkout import form_router as checkout_form_router
from app.routes.contact import form_router as contact_form_router
from app.routes.contact import router as contact_router
from app.routes.misc import router as misc_router
from app.routes.orders import router as orders_router
from app.routes.products import router as products_router
from app.routes.graphql import router as graphql_router
from app.routes.sensors import router as sensors_router
from app.routes.subscriptions import router as subscriptions_router
from app.routes.turnstile import router as turnstile_router
from app.routes.wholesale import router as wholesale_router

OPENAPI_TAGS = [
    {"name": "auth", "description": "Token issuance, registration, refresh, and JWKS endpoints."},
    {"name": "auth-forms", "description": "Form-based login and registration handlers used by the web UI."},
    {"name": "checkout-forms", "description": "Form-based checkout submission (Turnstile, Bot Management, Advanced Rate Limiting surface)."},
    {"name": "contact", "description": "Contact form APIs and form post handlers."},
    {"name": "turnstile", "description": "Turnstile verification and challenge simulation endpoints."},
    {"name": "products", "description": "Catalog and product detail endpoints."},
    {"name": "cart", "description": "Cart retrieval and mutation endpoints."},
    {"name": "orders", "description": "Customer order placement, returns, and listing endpoints."},
    {"name": "account", "description": "Account profile, subscription, and order history endpoints."},
    {"name": "admin", "description": "Admin portal APIs for dashboard and management operations."},
    {"name": "subscriptions", "description": "Subscription lifecycle and shipment endpoints."},
    {"name": "wholesale", "description": "Wholesale inventory, order, and invoicing endpoints."},
    {"name": "sensors", "description": "Synthetic event and telemetry ingestion endpoints for lab exercises."},
    {"name": "ai", "description": "AI chat and recommendation endpoints used for Firewall for AI exercises."},
    {"name": "misc", "description": "Search, upload, scripts, and miscellaneous support endpoints."},
    {"name": "graphql", "description": "GraphQL and GraphiQL endpoints for API Shield depth and payload testing."},
]


# Placeholder used when no real public URL is available (dev shells, the
# committed openapi.json artifact, etc.). Cloudflare requires an absolute URL
# but does not require it to resolve at upload time, so the placeholder keeps
# the spec structurally valid for offline tooling. The HTTP `/openapi.json`
# route substitutes the real hostname when handling a request — see
# `openapi_endpoint` below.
DEFAULT_API_PUBLIC_URL = "https://api.lab.sxplab.com"

OPENAPI_URL = "/openapi.json"
DOCS_URL = "/docs"
REDOC_URL = "/redoc"


# Disable FastAPI's built-in OpenAPI / Swagger UI / ReDoc routes so we can
# register our own. We still serve all three URLs at the same paths the
# defaults use, but the `/openapi.json` handler now resolves the public
# server URL with a three-step fallback chain (env var → request Host →
# hard-coded placeholder) and the docs HTML is rewired to that endpoint.
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Single Origin reference API used for AppSec labs. "
        "Includes REST, GraphQL, AI, and form-based flows intentionally designed "
        "for validation, hardening, and detection exercises."
    ),
    openapi_tags=OPENAPI_TAGS,
    openapi_url=None,
    docs_url=None,
    redoc_url=None,
)


def _build_openapi(server_url: str) -> dict:
    """Build the OpenAPI document with the given absolute server URL.

    Always returns a Cloudflare API Shield-compatible OAS 3.0.3 document.
    See ``app.openapi_compat`` for the conversion details. The result is
    deterministic for a given ``(route set, server_url)`` pair, which keeps
    the committed ``docs/openapi/single-origin.openapi.json`` artifact
    stable against the CI drift check.
    """
    raw = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=OPENAPI_TAGS,
    )
    return to_cloudflare_compatible(raw, server_url=server_url)


def custom_openapi() -> dict:
    """Override of ``app.openapi()`` used by tests and ``scripts/export-openapi.py``.

    Returns a Cloudflare-compatible spec keyed off the env-derived public URL
    (see :meth:`app.config.Settings.derive_api_public_url`) and caches the
    result on ``app.openapi_schema``. The committed OpenAPI artifact and the
    dev-shell tooling both go through this code path, so they are always in
    sync with what production pods serve.

    The HTTP ``/openapi.json`` route (``openapi_endpoint``) bypasses this
    cache so it can also use the request ``Host`` header when the env var
    is not derivable.
    """
    if app.openapi_schema:
        return app.openapi_schema
    server_url = settings.derive_api_public_url() or DEFAULT_API_PUBLIC_URL
    app.openapi_schema = _build_openapi(server_url)
    return app.openapi_schema


app.openapi = custom_openapi


def _resolve_runtime_server_url(request: Request) -> str:
    """Resolve the absolute server URL to advertise in ``/openapi.json``.

    Three-step fallback chain:

    1. ``settings.derive_api_public_url()`` — the env-var path. Production
       lab pods always hit this branch because CML provisions
       ``CHECKOUT_SDK_EXFIL_URL`` with the pod slug embedded.
    2. The inbound request's scheme + host. ``cloudflared`` populates
       ``X-Forwarded-Proto`` / ``X-Forwarded-Host`` correctly, so this
       matches what the learner pasted into Cloudflare API Shield as long
       as Single Origin sits behind any reasonable reverse proxy.
    3. The hard-coded placeholder. Reached only if both above fail (for
       example, a unit test with no Host header).

    The committed OpenAPI artifact uses path 1 (or 3 in the absence of the
    env var during artifact regeneration), so the artifact is deterministic
    and the CI drift check is stable.
    """
    env_url = settings.derive_api_public_url()
    if env_url:
        return env_url

    host = (
        request.headers.get("x-forwarded-host")
        or request.headers.get("host")
        or ""
    ).strip()
    if host:
        scheme = (request.headers.get("x-forwarded-proto") or request.url.scheme or "https").strip()
        return f"{scheme}://{host}"

    return DEFAULT_API_PUBLIC_URL


@app.get(OPENAPI_URL, include_in_schema=False)
async def openapi_endpoint(request: Request) -> JSONResponse:
    """Serve the OpenAPI document with a request-aware ``servers`` array.

    This handler computes the spec on every request rather than caching on
    ``app.openapi_schema`` — the per-request cost is negligible (the spec
    is a few KB and the conversion is pure Python over a deterministic
    structure) and it lets the ``servers`` URL track the request's host in
    deployments where the env-var path does not apply.
    """
    server_url = _resolve_runtime_server_url(request)
    return JSONResponse(_build_openapi(server_url))


@app.get(DOCS_URL, include_in_schema=False)
async def swagger_ui_html() -> object:
    return get_swagger_ui_html(openapi_url=OPENAPI_URL, title=f"{app.title} — Swagger UI")


@app.get(REDOC_URL, include_in_schema=False)
async def redoc_html() -> object:
    return get_redoc_html(openapi_url=OPENAPI_URL, title=f"{app.title} — ReDoc")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin] if settings.cors_origin != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(contact_router)
app.include_router(turnstile_router)
app.include_router(auth_form_router)
app.include_router(contact_form_router)
app.include_router(checkout_form_router)
app.include_router(products_router)
app.include_router(cart_router)
app.include_router(orders_router)
app.include_router(account_router)
app.include_router(admin_router)
app.include_router(subscriptions_router)
app.include_router(wholesale_router)
app.include_router(sensors_router)
app.include_router(ai_router)
app.include_router(misc_router)
app.include_router(graphql_router)


@app.on_event("startup")
async def startup_event() -> None:
    init_db()
    seed_db()


@app.get("/health")
async def health() -> dict:
    return {"status": "healthy", "version": settings.app_version}


@app.get("/api-docs")
async def api_docs_redirect():
    return RedirectResponse(url="/docs")


@app.get("/robots.txt")
async def robots() -> str:
    return "User-agent: *\nDisallow: /admin/\n"
