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

app = FastAPI(title=settings.app_name, version=settings.app_version)

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
