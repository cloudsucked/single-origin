from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.config import settings
from app.db import init_db, seed_db
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


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Single Origin reference API used for AppSec labs. "
        "Includes REST, GraphQL, AI, and form-based flows intentionally designed "
        "for validation, hardening, and detection exercises."
    ),
    openapi_tags=OPENAPI_TAGS,
)

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
