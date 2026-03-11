from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.turnstile import verify_turnstile_token

router = APIRouter(prefix="/api/turnstile", tags=["turnstile"])


class TurnstileVerifyRequest(BaseModel):
    token: str
    action: str | None = None


@router.post("/verify")
async def verify_turnstile(payload: TurnstileVerifyRequest):
    result = await verify_turnstile_token(payload.token, expected_action=payload.action)
    if not result.get("success"):
        raise HTTPException(
            status_code=403,
            detail={"error": "turnstile_verification_failed", "codes": result.get("error-codes", [])},
        )
    return {"success": True, "result": result}
