from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import JSONResponse

from app.config import settings
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest
from app.schemas.common import ErrorResponse
from app.services.jwt import build_jwks, issue_token
from app.services.passwords import verify_password
from app.services.repository import create_user, get_user_by_email
from app.services.turnstile import verify_turnstile_token

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
form_router = APIRouter(tags=["auth-forms"])

# Session cookie lifetime for the so_session fixture cookie. Lab-only; the real
# auth token is still returned in the JSON body so existing clients keep working.
SESSION_COOKIE_MAX_AGE = 60 * 60 * 8  # 8 hours


def _to_user_dict(user: dict) -> dict:
    return {"id": user["id"], "email": user["email"], "name": user["name"], "role": user["role"]}


def _auth_response(token: str, user_dict: dict) -> JSONResponse:
    """Return the auth JSON body and set the `so_session` fixture cookie.

    The JWT stays in the JSON body so existing clients (and the SvelteKit
    frontend) continue to work. The cookie is purely for Cloudflare Page Shield
    Cookie Monitor observability — it is HTTP-only, SameSite=Lax, and set on
    every successful login/register flow (API and form).
    """
    response = JSONResponse({"token": token, "user": user_dict})
    response.set_cookie(
        key="so_session",
        value=token,
        max_age=SESSION_COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        path="/",
    )
    return response


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
    return _auth_response(issue_token(user_dict), user_dict)


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
    return _auth_response(issue_token(user_dict), user_dict)


@router.post("/refresh")
async def refresh_token() -> dict:
    return {"token": "refresh-not-implemented-in-mvp"}


@router.get("/.well-known/jwks.json")
async def jwks() -> dict:
    return build_jwks()


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
                {"error": "turnstile_verification_failed", "codes": verification.get("error-codes", [])},
                status_code=403,
            )

    user = get_user_by_email(email)
    if not user or not verify_password(password, user["password"]):
        return JSONResponse({"error": "invalid_credentials"}, status_code=401)

    user_dict = _to_user_dict(user)
    return _auth_response(issue_token(user_dict), user_dict)


@form_router.post(
    "/admin",
    response_model=AuthResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid credentials."},
        403: {"model": ErrorResponse, "description": "Authenticated user lacks admin role."},
    },
    summary="Admin console form login (credential-stuffing surface)",
)
async def admin_form_login(
    username: str = Form(...),
    password: str = Form(...),
):
    """Form-encoded admin login at `/admin` for Bot Management exercises.

    Implement Bot Management Task 7 exercises credential stuffing against
    this endpoint. The form uses `username` rather than `email` so Traffic
    Detections' custom detection location for `/admin` reads from
    `http.request.body.form["username"][0]` (matching the course guide).

    Behavior:
      - 401 on unknown user or wrong password.
      - 403 if the user authenticates but is not an admin.
      - 200 + JWT + so_session cookie on success.

    There is no origin-side rate limiting — Cloudflare Bot Management and
    Advanced Rate Limiting are the enforcement layers the lab configures.
    """
    user = get_user_by_email(username)
    if not user or not verify_password(password, user["password"]):
        return JSONResponse({"error": "invalid_credentials"}, status_code=401)
    if user.get("role") != "admin":
        return JSONResponse({"error": "not_admin"}, status_code=403)
    user_dict = _to_user_dict(user)
    return _auth_response(issue_token(user_dict), user_dict)


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
                {"error": "turnstile_verification_failed", "codes": verification.get("error-codes", [])},
                status_code=403,
            )

    if get_user_by_email(email):
        return JSONResponse({"error": "email_already_exists"}, status_code=409)

    user_dict = create_user(email=email, password=password, name=name)
    return _auth_response(issue_token(user_dict), user_dict)
