from pydantic import BaseModel
from datetime import datetime


class DocumentOut(BaseModel):
    id: int
    company_id: int
    filename: str
    original_name: str
    file_size: int | None = None
    mime_type: str | None = None
    status: str
    page_count: int | None = None
    chunk_count: int
    error_message: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
