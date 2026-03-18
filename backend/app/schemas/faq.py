from pydantic import BaseModel
from datetime import datetime


class FAQCreate(BaseModel):
    question: str
    answer: str
    category: str | None = None
    is_published: bool = True


class FAQUpdate(BaseModel):
    question: str | None = None
    answer: str | None = None
    category: str | None = None
    is_published: bool | None = None
    sort_order: int | None = None


class FAQOut(BaseModel):
    id: int
    company_id: int
    question: str
    answer: str
    category: str | None = None
    is_published: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
