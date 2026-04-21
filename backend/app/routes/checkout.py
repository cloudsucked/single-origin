from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import JSONResponse, RedirectResponse

from app.config import settings
from app.db import get_conn
from app.services.repository import get_order
from app.services.turnstile import verify_turnstile_token

form_router = APIRouter(tags=["checkout-forms"])


@form_router.post(
    "/checkout/submit",
    summary="Submit a checkout form payload (legacy HTML form path)",
)
async def checkout_submit(
    request: Request,
    card_number: str = Form(...),
    card_exp: str = Form(...),
    card_cvv: str = Form(...),
    billing_name: str = Form(...),
    billing_address: str = Form(...),
    billing_city: str = Form(""),
    billing_country: str = Form(""),
    billing_zip: str = Form(""),
    phone: str = Form(""),
    email: str = Form("demo@singleorigin.example"),
    total: float = Form(0.0),
    cf_turnstile_response: str | None = Form(None, alias="cf-turnstile-response"),
):
    """Form-encoded checkout submission.

    Lab surface for API Shield schema validation, Turnstile pre-clearance,
    Bot Management, Security Analytics, and Advanced Rate Limiting exercises.
    The real app is an SPA; this endpoint exists so Cloudflare WAF sees a
    form POST with structured fields at a known path.

    Behavior:
      - If `ENFORCE_TURNSTILE=true`, validates the `cf-turnstile-response`
        token with Siteverify. 400 on missing token, 403 on invalid token.
      - On success, inserts an `orders` row (status=`PROCESSING`), returns a
        303 redirect to `/checkout/confirmation?order_id=<id>` for browser
        navigation. API-first callers that pass `Accept: application/json`
        get a 200 JSON response with the new `order_id` instead.
      - The `card_number` and `card_cvv` fields are intentionally named so
        that API Shield Sensitive Data Detection rules can match on them;
        they are NOT persisted (only `card_last4` is written).
    """
    if settings.enforce_turnstile:
        if not cf_turnstile_response:
            return JSONResponse(
                {"error": "turnstile_verification_required"}, status_code=400
            )
        verification = await verify_turnstile_token(
            token=cf_turnstile_response,
            remote_ip=request.client.host if request.client else None,
            expected_action="checkout",
        )
        if not verification.get("success"):
            return JSONResponse(
                {
                    "error": "turnstile_verification_failed",
                    "codes": verification.get("error-codes", []),
                },
                status_code=403,
            )

    card_last4 = card_number[-4:] if len(card_number) >= 4 else card_number
    billing_summary = ", ".join(
        part
        for part in (billing_address, billing_city, billing_country, billing_zip)
        if part
    )

    with get_conn() as conn:
        cursor = conn.execute(
            """
            INSERT INTO orders (user_email, total, status, billing_address, card_last4, phone)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (email, total, "PROCESSING", billing_summary, card_last4, phone),
        )
        order_id = cursor.lastrowid or 0

    accept = request.headers.get("accept", "").lower()
    if "application/json" in accept:
        order = get_order(order_id)
        return JSONResponse(
            {"status": "placed", "order_id": order_id, "order": order},
            status_code=200,
        )

    # Browser flow: 303 See Other so the follow-up is a GET.
    return RedirectResponse(
        url=f"/checkout/confirmation?order_id={order_id}",
        status_code=303,
    )
