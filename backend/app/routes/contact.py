from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import JSONResponse

from app.config import settings
from app.schemas.contact import ContactRequest
from app.services.repository import save_contact
from app.services.turnstile import verify_turnstile_token

router = APIRouter(prefix="/api/v1", tags=["contact"])
form_router = APIRouter(tags=["contact-forms"])


@router.post("/contact")
async def submit_contact(payload: ContactRequest):
    save_contact(payload.name, payload.email, payload.message)
    return {"status": "accepted", "name": payload.name, "email": payload.email}


@form_router.post("/contact/submit")
async def submit_contact_form(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    message: str = Form(...),
    cf_turnstile_response: str | None = Form(None, alias="cf-turnstile-response"),
):
    if settings.enforce_turnstile:
        if not cf_turnstile_response:
            return JSONResponse({"error": "turnstile_verification_required"}, status_code=400)

        verification = await verify_turnstile_token(
            token=cf_turnstile_response,
            remote_ip=request.client.host if request.client else None,
            expected_action="contact",
        )
        if not verification.get("success"):
            return JSONResponse(
                {
                    "error": "turnstile_verification_failed",
                    "codes": verification.get("error-codes", []),
                },
                status_code=403,
            )

    save_contact(name, email, message)
    return {
        "status": "accepted",
        "name": name,
        "email": email,
        "message_preview": message[:80],
    }
