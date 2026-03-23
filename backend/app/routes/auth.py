from __future__ import annotations

import base64
from datetime import UTC, datetime, timedelta
from functools import lru_cache

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

_LAB_KEY_ID = "lab-static-key-v1"


@lru_cache(maxsize=1)
def _get_lab_private_key() -> str:
    """Return the lab RSA private key PEM, normalising \\n escape sequences."""
    raw = settings.lab_jwt_private_key
    if not raw:
        return ""
    # Env vars delivered via Terraform store newlines as literal \n sequences
    return raw.replace("\\n", "\n")


def _lab_mode() -> bool:
    return bool(_get_lab_private_key())


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
    if _lab_mode():
        return jwt.encode(
            claims,
            _get_lab_private_key(),
            algorithm="RS256",
            headers={"kid": _LAB_KEY_ID},
        )
    return jwt.encode(claims, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def _to_user_dict(user: dict) -> dict:
    return {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
    }


def _int_to_base64url(n: int) -> str:
    length = (n.bit_length() + 7) // 8
    return base64.urlsafe_b64encode(n.to_bytes(length, "big")).rstrip(b"=").decode()


@router.get("/.well-known/jwks.json")
async def jwks() -> dict:
    """Return the JWKS for the active signing key.

    In lab mode (LAB_JWT_PRIVATE_KEY set) this serves the RSA public key so
    Cloudflare API Shield JWT Validation can verify lab tokens. In dev/prod mode
    with HS256, JWKS is not applicable and an empty key set is returned.
    """
    if not _lab_mode():
        return {"keys": []}

    from cryptography.hazmat.primitives.serialization import load_pem_private_key  # type: ignore[import]
    from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers  # type: ignore[import]

    private_key = load_pem_private_key(_get_lab_private_key().encode(), password=None)
    pub_numbers: RSAPublicNumbers = private_key.public_key().public_numbers()  # type: ignore[assignment,union-attr]
    return {
        "keys": [
            {
                "kty": "RSA",
                "use": "sig",
                "alg": "RS256",
                "kid": _LAB_KEY_ID,
                "n": _int_to_base64url(pub_numbers.n),
                "e": _int_to_base64url(pub_numbers.e),
            }
        ]
    }


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
