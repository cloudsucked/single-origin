from __future__ import annotations

from fastapi import APIRouter, Response

from app.services.complexity import COMPLEXITY_HEADER, score_ai_payload

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])


@router.post("/chat")
async def ai_chat(payload: dict, response: Response):
    response.headers[COMPLEXITY_HEADER] = str(score_ai_payload(payload))

    prompt = ""
    messages = payload.get("messages") if isinstance(payload, dict) else None
    if isinstance(messages, list) and messages:
        last = messages[-1]
        if isinstance(last, dict):
            prompt = str(last.get("content", ""))

    return {
        "id": "chatcmpl-so-1",
        "object": "chat.completion",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": f"For '{prompt[:80]}', try Yirgacheffe Reserve for bright fruit notes.",
                },
            }
        ],
    }


@router.post("/recommend")
async def ai_recommend(payload: dict, response: Response):
    response.headers[COMPLEXITY_HEADER] = str(score_ai_payload(payload))
    return {
        "recommendations": [
            {"id": 1, "name": "Yirgacheffe Reserve"},
            {"id": 7, "name": "House Espresso Blend"},
        ],
        "input": payload,
    }
