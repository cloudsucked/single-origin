from __future__ import annotations

from fastapi import APIRouter, Body, Response

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
    return RecommendResponse(
        recommendations=[
            RecommendationItem(id=1, name="Yirgacheffe Reserve"),
            RecommendationItem(id=7, name="House Espresso Blend"),
        ],
        input=payload_dict,
    )
