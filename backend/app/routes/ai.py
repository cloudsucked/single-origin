from __future__ import annotations

import httpx
from fastapi import APIRouter, Body, HTTPException, Response

from app.config import settings
from app.schemas.ai import (
    ChatChoice,
    ChatChoiceMessage,
    ChatRequest,
    ChatResponse,
    RecommendRequest,
    RecommendResponse,
    RecommendationItem,
)
from app.services.complexity import COMPLEXITY_HEADER, score_ai_payload

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])


async def _proxy_to_ai_gateway(payload_dict: dict) -> dict:
    """Forward a chat payload to Cloudflare AI Gateway.

    Returns the gateway JSON body. Raises HTTPException(502, ...) with a
    structured error body on any upstream failure so the learner sees the
    problem in Security Events / AI Gateway logs rather than a silent
    fallback to a canned response.
    """
    if not settings.ai_gateway_url:
        raise HTTPException(
            status_code=502,
            detail={"error": "ai_gateway_url_missing", "message": "AI_GATEWAY_ENABLED=true but AI_GATEWAY_URL is empty"},
        )

    headers = {
        "content-type": "application/json",
        # Cloudflare AI Gateway authorization header
        "cf-aig-authorization": f"Bearer {settings.ai_gateway_token}",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            upstream = await http_client.post(
                settings.ai_gateway_url,
                headers=headers,
                json=payload_dict,
            )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail={"error": "ai_gateway_unreachable", "message": str(exc)},
        ) from exc

    if upstream.status_code >= 400:
        body: dict
        try:
            body = upstream.json()
        except ValueError:
            body = {"raw": upstream.text[:400]}
        raise HTTPException(
            status_code=502,
            detail={
                "error": "ai_gateway_upstream_error",
                "status": upstream.status_code,
                "body": body,
            },
        )

    return upstream.json()


@router.post("/chat")
async def ai_chat(
    response: Response,
    payload: ChatRequest = Body(
        ...,
        examples=[
            {
                "model": "brew-assistant-v1",
                "messages": [{"role": "user", "content": "Recommend a fruity pour-over coffee."}],
            }
        ],
    ),
) -> ChatResponse:
    payload_dict = payload.model_dump()
    response.headers[COMPLEXITY_HEADER] = str(score_ai_payload(payload_dict))

    if settings.ai_gateway_enabled:
        # Force the gateway model (otherwise the lab-exposed `brew-assistant-v1`
        # alias would confuse Workers AI).
        gateway_payload = dict(payload_dict)
        gateway_payload["model"] = settings.ai_model
        upstream_body = await _proxy_to_ai_gateway(gateway_payload)

        # Workers AI / OpenAI-compatible response surface — normalize into the
        # ChatResponse shape so downstream consumers don't need to branch.
        choices_source = upstream_body.get("choices") or []
        if choices_source:
            first = choices_source[0]
            msg = first.get("message") or {}
            content = msg.get("content") or ""
            role = msg.get("role") or "assistant"
        else:
            # Workers AI non-OpenAI shape: `{"result": {"response": "..."}}`.
            result = upstream_body.get("result") or {}
            content = result.get("response") or upstream_body.get("response") or ""
            role = "assistant"

        return ChatResponse(
            id=upstream_body.get("id", "chatcmpl-so-proxy"),
            object=upstream_body.get("object", "chat.completion"),
            choices=[
                ChatChoice(
                    index=0,
                    message=ChatChoiceMessage(role=role, content=content),
                )
            ],
        )

    # Canned lab response (default; AI Gateway disabled).
    prompt = ""
    messages = payload.messages
    if messages:
        prompt = messages[-1].content

    return ChatResponse(
        id="chatcmpl-so-1",
        object="chat.completion",
        choices=[
            ChatChoice(
                index=0,
                message=ChatChoiceMessage(
                    role="assistant",
                    content=f"For '{prompt[:80]}', try Yirgacheffe Reserve for bright fruit notes.",
                ),
            )
        ],
    )


@router.post("/recommend")
async def ai_recommend(
    response: Response,
    payload: RecommendRequest = Body(
        ...,
        examples=[
            {
                "prompt": "I want chocolate-forward espresso beans",
                "preferences": {"roast": "dark", "method": "espresso"},
            }
        ],
    ),
) -> RecommendResponse:
    payload_dict = payload.model_dump(exclude_none=True)
    response.headers[COMPLEXITY_HEADER] = str(score_ai_payload(payload_dict))

    if settings.ai_gateway_enabled:
        # Turn the recommend prompt into a chat-shape message so AI Gateway
        # (which speaks OpenAI-compat by default) receives a familiar body.
        gateway_payload = {
            "model": settings.ai_model,
            "messages": [
                {
                    "role": "system",
                    "content": "You recommend specialty coffee products by id and name. "
                    "Return JSON that contains a `recommendations` array of {id, name}.",
                },
                {
                    "role": "user",
                    "content": str(payload_dict.get("prompt") or payload_dict),
                },
            ],
        }
        upstream_body = await _proxy_to_ai_gateway(gateway_payload)

        # We don't try to parse the LLM's JSON back into recommendation rows;
        # for AI Security for Apps the lab cares that prompt + response round-
        # trip through the gateway, not that the recs are well-formed. Return
        # a placeholder set so the schema stays satisfied and include the
        # upstream text under `input.gateway_response` for verification.
        choices_source = upstream_body.get("choices") or []
        gateway_text = ""
        if choices_source:
            msg = choices_source[0].get("message") or {}
            gateway_text = msg.get("content") or ""
        else:
            result = upstream_body.get("result") or {}
            gateway_text = result.get("response") or upstream_body.get("response") or ""

        return RecommendResponse(
            recommendations=[
                RecommendationItem(id=1, name="Yirgacheffe Reserve"),
                RecommendationItem(id=7, name="House Espresso Blend"),
            ],
            input={**payload_dict, "gateway_response": gateway_text},
        )

    # Canned lab response (default; AI Gateway disabled).
    return RecommendResponse(
        recommendations=[
            RecommendationItem(id=1, name="Yirgacheffe Reserve"),
            RecommendationItem(id=7, name="House Espresso Blend"),
        ],
        input=payload_dict,
    )
