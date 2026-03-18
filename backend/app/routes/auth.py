from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Form, Request
from fastapi.responses import JSONResponse
from jose import jwt

from app.config import settings
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest
from app.schemas.common import ErrorResponse
from app.services.passwords import verify_password
from app.services.repository import create_user, get_user_by_email
from app.services.turnstile import verify_turnstile_token

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
form_router = APIRouter(tags=["auth-forms"])


def _issue_token(user: dict) -> str:
    now = datetime.now(UTC)
    claims = {
        "sub": str(user["id"]),
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "iss": "single-origin",
        "aud": "single-origin-api",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=1)).timestamp()),
    }
    return jwt.encode(claims, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def _to_user_dict(user: dict) -> dict:
    return {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
    }


@router.post(
    "/login",
    response_model=AuthResponse,
    responses={401: {"model": ErrorResponse, "description": "Invalid email or password."}},
    summary="Authenticate with JSON payload",
)
async def login_api(payload: LoginRequest):
    user = get_user_by_email(payload.email)
    if not user or not verify_password(payload.password, user["password"]):
        return JSONResponse({"error": "invalid_credentials"}, status_code=401)
    user_dict = _to_user_dict(user)
    return {"token": _issue_token(user_dict), "user": user_dict}


@router.post(
    "/register",
    response_model=AuthResponse,
    responses={409: {"model": ErrorResponse, "description": "Email already exists."}},
    summary="Register a user with JSON payload",
)
async def register_api(payload: RegisterRequest):
    if get_user_by_email(payload.email):
        return JSONResponse({"error": "email_already_exists"}, status_code=409)
    user_dict = create_user(payload.email, payload.password, payload.name)
    return {"token": _issue_token(user_dict), "user": user_dict}


@router.post("/refresh")
async def refresh_token() -> dict:
    return {"token": "refresh-not-implemented-in-mvp"}


@router.get("/.well-known/jwks.json")
async def jwks() -> dict:
    return {"keys": []}


@form_router.post(
    "/login",
    response_model=AuthResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Turnstile response missing."},
        401: {"model": ErrorResponse, "description": "Invalid email or password."},
        403: {"model": ErrorResponse, "description": "Turnstile verification failed."},
    },
    summary="Authenticate with form payload",
)
async def login_form(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    cf_turnstile_response: str | None = Form(None, alias="cf-turnstile-response"),
):
    if settings.enforce_turnstile:
        if not cf_turnstile_response:
            return JSONResponse({"error": "turnstile_verification_required"}, status_code=400)

        verification = await verify_turnstile_token(
            token=cf_turnstile_response,
            remote_ip=request.client.host if request.client else None,
            expected_action="login",
        )
        if not verification.get("success"):
            return JSONResponse(
                {
                    "error": "turnstile_verification_failed",
                    "codes": verification.get("error-codes", []),
                },
                status_code=403,
            )

    user = get_user_by_email(email)
    if not user or not verify_password(password, user["password"]):
        return JSONResponse({"error": "invalid_credentials"}, status_code=401)

    user_dict = _to_user_dict(user)
    return {"token": _issue_token(user_dict), "user": user_dict}


@form_router.post(
    "/register",
    response_model=AuthResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Turnstile response missing."},
        403: {"model": ErrorResponse, "description": "Turnstile verification failed."},
        409: {"model": ErrorResponse, "description": "Email already exists."},
    },
    summary="Register with form payload",
)
async def register_form(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    name: str = Form(...),
    cf_turnstile_response: str | None = Form(None, alias="cf-turnstile-response"),
):
    if settings.enforce_turnstile:
        if not cf_turnstile_response:
            return JSONResponse({"error": "turnstile_verification_required"}, status_code=400)

        verification = await verify_turnstile_token(
            token=cf_turnstile_response,
            remote_ip=request.client.host if request.client else None,
            expected_action="register",
        )
        if not verification.get("success"):
            return JSONResponse(
                {
                    "error": "turnstile_verification_failed",
                    "codes": verification.get("error-codes", []),
                },
                status_code=403,
            )

    if get_user_by_email(email):
        return JSONResponse({"error": "email_already_exists"}, status_code=409)

    user_dict = create_user(email=email, password=password, name=name)
    return {"token": _issue_token(user_dict), "user": user_dict}
