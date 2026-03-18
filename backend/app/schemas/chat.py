from pydantic import BaseModel
from datetime import datetime
from typing import Any


class ChatRequest(BaseModel):
    message: str
    session_id: int | None = None
    company_id: int | None = None
    sources: list[str] | None = None  # subset of ["database", "documents", "faq"]; None = all


class ChatResponse(BaseModel):
    session_id: int
    message: str
    sources: dict[str, Any] | None = None
    sql_generated: str | None = None
    response_time_ms: int | None = None


class ChatSessionOut(BaseModel):
    id: int
    title: str | None = None
    created_at: datetime
    message_count: int = 0

    model_config = {"from_attributes": True}


class ChatMessageOut(BaseModel):
    id: int
    role: str
    content: str
    sources: dict[str, Any] | None = None
    sql_generated: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
