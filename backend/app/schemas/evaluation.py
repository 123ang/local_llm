from datetime import datetime
from typing import Any
from pydantic import BaseModel


class EvaluationQuestionCreate(BaseModel):
    question: str
    expected_keywords: list[str] = []
    expected_source: str | None = None
    sources: list[str] = ["database", "documents", "faq"]
    ai_insights: bool = False


class EvaluationQuestionUpdate(BaseModel):
    question: str | None = None
    expected_keywords: list[str] | None = None
    expected_source: str | None = None
    sources: list[str] | None = None
    ai_insights: bool | None = None
    is_active: bool | None = None


class EvaluationQuestionOut(BaseModel):
    id: int
    company_id: int
    question: str
    expected_keywords: list[str]
    expected_source: str | None = None
    sources: list[str]
    ai_insights: bool
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class EvaluationRunOut(BaseModel):
    id: int
    question_id: int
    company_id: int
    passed: bool
    answer: str
    sources_used: dict[str, Any] | None = None
    missing_keywords: list[str]
    latency_ms: int | None = None
    model_tier: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
