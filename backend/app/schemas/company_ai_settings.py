from pydantic import BaseModel, Field
from typing import Literal

SourceName = Literal["database", "documents", "faq"]


class CompanyAISettingsOut(BaseModel):
    company_id: int
    default_source_only: bool = True
    ai_insights_allowed: bool = True
    allowed_sources: list[SourceName] = ["database", "documents", "faq"]
    min_document_relevance: float = 0.60
    require_citations: bool = True
    sql_visible_to_admins_only: bool = True

    model_config = {"from_attributes": True}


class CompanyAISettingsUpdate(BaseModel):
    default_source_only: bool | None = None
    ai_insights_allowed: bool | None = None
    allowed_sources: list[SourceName] | None = None
    min_document_relevance: float | None = Field(default=None, ge=0.0, le=1.0)
    require_citations: bool | None = None
    sql_visible_to_admins_only: bool | None = None
