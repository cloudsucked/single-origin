from __future__ import annotations

import uuid

import httpx

from app.config import settings

SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


async def verify_turnstile_token(
    token: str,
    remote_ip: str | None = None,
    expected_action: str | None = None,
) -> dict:
    if not settings.turnstile_secret_key:
        return {
            "success": False,
            "error-codes": ["missing-secret-key"],
            "message": "TURNSTILE_SECRET_KEY is not configured",
        }

    payload = {
        "secret": settings.turnstile_secret_key,
        "response": token,
        "idempotency_key": str(uuid.uuid4()),
    }
    if remote_ip:
        payload["remoteip"] = remote_ip

    async with httpx.AsyncClient(timeout=8.0) as client:
        response = await client.post(SITEVERIFY_URL, json=payload)
        response.raise_for_status()
        result = response.json()

    if expected_action and result.get("action") not in (None, expected_action):
        result["success"] = False
        result["error-codes"] = [*(result.get("error-codes") or []), "action-mismatch"]

    expected_hostname = settings.turnstile_expected_hostname
    if expected_hostname and result.get("hostname") not in (
        expected_hostname,
        f"www.{expected_hostname}",
    ):
        result["success"] = False
        result["error-codes"] = [*(result.get("error-codes") or []), "hostname-mismatch"]

    return result
