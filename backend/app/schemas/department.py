from datetime import datetime
from pydantic import BaseModel


class DepartmentCreate(BaseModel):
    company_id: int
    name: str
    description: str | None = None


class DepartmentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class DepartmentOut(BaseModel):
    id: int
    company_id: int
    name: str
    slug: str
    description: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserDepartmentGrantUpdate(BaseModel):
    department_ids: list[int]
