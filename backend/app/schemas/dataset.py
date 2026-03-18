from pydantic import BaseModel
from datetime import datetime
from typing import Any


class ColumnDef(BaseModel):
    name: str
    type: str = "text"
    nullable: bool = True


class DatasetCreateManual(BaseModel):
    display_name: str
    description: str | None = None
    columns: list[ColumnDef]


class DatasetOut(BaseModel):
    id: int
    company_id: int
    table_name: str
    display_name: str
    description: str | None = None
    columns_schema: list[dict[str, Any]] | None = None
    row_count: int
    source: str
    status: str
    is_queryable: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DatasetImportOut(BaseModel):
    id: int
    dataset_id: int
    filename: str
    row_count: int
    mode: str
    status: str
    error_message: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CSVPreviewOut(BaseModel):
    columns: list[str]
    dtypes: dict[str, str]
    row_count: int
    preview_rows: list[dict[str, Any]]


class SQLTablePreview(BaseModel):
    original_name: str
    target_name: str
    columns: list[dict[str, Any]]
    row_count: int
    preview_rows: list[dict[str, Any]]
    is_duplicate: bool = False


class SQLPreviewOut(BaseModel):
    tables: list[SQLTablePreview]
    total_tables: int
    total_rows: int
