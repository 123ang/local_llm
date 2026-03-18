from pydantic import BaseModel
from datetime import datetime


class CompanyCreate(BaseModel):
    name: str
    description: str | None = None


class CompanyUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class CompanyOut(BaseModel):
    id: int
    name: str
    slug: str
    description: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CompanyListOut(BaseModel):
    id: int
    name: str
    slug: str
    is_active: bool
    user_count: int = 0

    model_config = {"from_attributes": True}
