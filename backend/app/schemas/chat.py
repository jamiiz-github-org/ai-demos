from typing import Literal
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    assistant_type: Literal["website", "property", "document"] = "document"
    session_id: str | None = None
    history: list[ChatMessage] = Field(default_factory=list)
    # For document assistant — which uploaded namespace to query
    namespace_override: str | None = None


class ChatResponse(BaseModel):
    answer: str
    assistant_type: str
    session_id: str | None = None
    sources: list[str] = Field(default_factory=list)
    confidence: Literal["high", "low"] = "high"
    intent: str | None = None
    # Nudge for lead capture
    suggest_booking: bool = False
