from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ConnectorMethod = Literal["GET", "POST"]


class APIConnectorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    department_id: int
    visibility: str = "department"
    method: ConnectorMethod = "GET"
    url: str = ""
    headers: dict[str, str] = Field(default_factory=dict)
    body: str | None = None
    curl_command: str | None = None


class APIConnectorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    department_id: int | None = None
    visibility: str | None = None
    method: ConnectorMethod | None = None
    url: str | None = None
    headers: dict[str, str] | None = None
    body: str | None = None
    curl_command: str | None = None
    status: str | None = None


class APIConnectorOut(BaseModel):
    id: int
    company_id: int
    department_id: int
    visibility: str
    name: str
    description: str | None = None
    method: str
    url: str
    headers: dict[str, str]
    body: str | None = None
    curl_command: str | None = None
    status: str
    last_status_code: int | None = None
    last_response_text: str | None = None
    last_error: str | None = None
    last_synced_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
