from pydantic import BaseModel
from datetime import datetime
from typing import Any


class AuditLogOut(BaseModel):
    id: int
    company_id: int | None = None
    company_name: str | None = None
    organization_name: str | None = None
    user_id: int | None = None
    user_name: str | None = None
    user_email: str | None = None
    actor_label: str | None = None
    action: str
    resource_type: str | None = None
    resource_id: int | None = None
    resource_kind_label: str | None = None
    resource_label: str | None = None
    details: dict[str, Any] | None = None
    ip_address: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
