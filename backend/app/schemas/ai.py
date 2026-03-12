from __future__ import annotations

from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str | None = None
    messages: list[ChatMessage]


class ChatChoiceMessage(BaseModel):
    role: str
    content: str


class ChatChoice(BaseModel):
    index: int
    message: ChatChoiceMessage


class ChatResponse(BaseModel):
    id: str
    object: str
    choices: list[ChatChoice]


class RecommendationItem(BaseModel):
    id: int
    name: str


class RecommendRequest(BaseModel):
    prompt: str | None = None
    preferences: dict | None = None
    messages: list[ChatMessage] | None = None


class RecommendResponse(BaseModel):
    recommendations: list[RecommendationItem]
    input: dict
