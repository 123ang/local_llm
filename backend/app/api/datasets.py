import uuid
import re
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.core.database import get_db, engine
from app.core.database_roles import dataset_write_transaction, grant_text_to_sql_select
from app.core.dependencies import require_admin, ensure_company_access, ensure_company_admin_access
from app.core.errors import correlation_id_from_request, public_error_detail
from app.core.logger import logger
from app.core.security import get_current_user
from app.core.config import settings
from app.ingestion.sql_importer import (
    SQLImportLimits,
    SQLImportValidationError,
    build_pg_create_sql,
    build_pg_insert_sql,
    make_unique_table_name,
    parse_sql_dump,
    read_sql_upload,
)
from app.schemas.dataset import DatasetCreateManual, DatasetOut, DatasetImportOut, CSVPreviewOut, SQLPreviewOut, SQLTablePreview
from app.models.dataset import Dataset, DatasetImport
from app.models.user import User
from app.services.audit_service import log_action
from pathlib import Path

router = APIRouter(prefix="/datasets", tags=["datasets"])

TYPE_MAP = {
    "text": "TEXT",
    "integer": "INTEGER",
    "float": "DOUBLE PRECISION",
    "boolean": "BOOLEAN",
    "date": "DATE",
    "timestamp": "TIMESTAMP",
}


def _sql_import_limits() -> SQLImportLimits:
    return SQLImportLimits(
        max_tables=settings.MAX_SQL_IMPORT_TABLES,
        max_columns_per_table=settings.MAX_SQL_IMPORT_COLUMNS_PER_TABLE,
        max_total_rows=settings.MAX_SQL_IMPORT_ROWS,
    )


def _safe_upload_name(filename: str) -> str:
    basename = Path(filename).name
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", basename)
    return cleaned[:200] or "upload.sql"

def _safe_identifier(name: str) -> str:
    clean = re.sub(r'[^a-z0-9_]', '_', name.lower().strip())
    clean = re.sub(r'_+', '_', clean).strip('_')
    if not clean or clean[0].isdigit():
        clean = f"col_{clean or 'field'}"
    return clean[:63]


def _safe_table_name(company_id: int, name: str) -> str:
    return f"c{company_id}_{_safe_identifier(name)}"


def _quote_identifier(identifier: str) -> str:
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,62}", identifier):
        raise HTTPException(status_code=400, detail=f"Invalid SQL identifier: {identifier}")
    return f'"{identifier}"'


def _dedupe_identifiers(names: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    result: list[str] = []
    for name in names:
        base = _safe_identifier(name)
        count = seen.get(base, 0)
        seen[base] = count + 1
        result.append(base if count == 0 else f"{base}_{count + 1}")
    return result

@router.get("/{company_id}", response_model=list[DatasetOut])
async def list_datasets(company_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    ensure_company_access(current_user, company_id)
    result = await db.execute(select(Dataset).where(Dataset.company_id == company_id).order_by(Dataset.created_at.desc()))
    return list(result.scalars().all())

@router.post("/{company_id}/manual", response_model=DatasetOut, status_code=201)
async def create_manual_table(company_id: int, data: DatasetCreateManual, current_user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    ensure_company_admin_access(current_user, company_id)
    if not data.columns:
        raise HTTPException(status_code=400, detail="At least one column is required")
    table_name = _safe_table_name(company_id, data.display_name)
    cols = []
    schema_list = []
    safe_names = _dedupe_identifiers([col.name for col in data.columns])
    for col, safe_name in zip(data.columns, safe_names):
        pg_type = TYPE_MAP.get(col.type, "TEXT")
        null = "" if col.nullable else " NOT NULL"
        cols.append(f'{_quote_identifier(safe_name)} {pg_type}{null}')
        schema_list.append({"name": safe_name, "type": col.type, "nullable": col.nullable, "original_name": col.name})
    
    col_defs = ", ".join(cols)
    create_sql = f'CREATE TABLE IF NOT EXISTS {_quote_identifier(table_name)} (id SERIAL PRIMARY KEY, {col_defs})'
    
    async with dataset_write_transaction() as conn:
        await conn.execute(text(create_sql))
        await grant_text_to_sql_select(conn, table_name)
    
    dataset = Dataset(
        company_id=company_id, table_name=table_name, display_name=data.display_name,
        description=data.description, columns_schema=schema_list, source="manual",
        created_by=current_user.id,
    )
    db.add(dataset)
    await db.commit()
    await db.refresh(dataset)
    await log_action(db, action="create_dataset", user_id=current_user.id, company_id=company_id, resource_type="dataset", resource_id=dataset.id)
    return dataset

@router.post("/{company_id}/upload-table", response_model=DatasetOut, status_code=201)
async def upload_table_and_data(
    company_id: int,
    file: UploadFile = File(...),
    display_name: str = Form(...),
    description: str = Form(""),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Upload CSV → auto-create table from columns → insert data."""
    ensure_company_admin_access(current_user, company_id)
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    company_dir = Path(settings.UPLOAD_DIR) / "companies" / str(company_id) / "csv"
    company_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = company_dir / safe_name
    
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    df = pd.read_csv(file_path)
    table_name = _safe_table_name(company_id, display_name)
    
    # Infer schema from pandas dtypes
    schema_list = []
    col_defs = []
    safe_df_columns = _dedupe_identifiers([str(col_name) for col_name in df.columns])
    for col_name, safe_col in zip(df.columns, safe_df_columns):
        dtype = str(df[col_name].dtype)
        if "int" in dtype:
            pg_type, col_type = "INTEGER", "integer"
        elif "float" in dtype:
            pg_type, col_type = "DOUBLE PRECISION", "float"
        elif "bool" in dtype:
            pg_type, col_type = "BOOLEAN", "boolean"
        elif "datetime" in dtype:
            pg_type, col_type = "TIMESTAMP", "timestamp"
        else:
            pg_type, col_type = "TEXT", "text"
        col_defs.append(f'{_quote_identifier(safe_col)} {pg_type}')
        schema_list.append({"name": safe_col, "type": col_type, "nullable": True, "original_name": col_name})
    
    create_sql = f'CREATE TABLE IF NOT EXISTS {_quote_identifier(table_name)} (id SERIAL PRIMARY KEY, {", ".join(col_defs)})'

    row_count = 0
    insert_sql = None
    records = []
    if not df.empty:
        safe_cols = [s["name"] for s in schema_list]
        col_names = ", ".join(_quote_identifier(c) for c in safe_cols)
        placeholders = ", ".join(f":{c}" for c in safe_cols)
        insert_sql = f'INSERT INTO {_quote_identifier(table_name)} ({col_names}) VALUES ({placeholders})'

        for _, row in df.iterrows():
            record = {}
            for i, s in enumerate(schema_list):
                val = row[df.columns[i]]
                record[s["name"]] = None if pd.isna(val) else val
                if s["type"] == "integer" and record[s["name"]] is not None:
                    record[s["name"]] = int(record[s["name"]])
            records.append(record)
        row_count = len(records)

    async with dataset_write_transaction() as conn:
        await conn.execute(text(create_sql))
        if insert_sql and records:
            await conn.execute(text(insert_sql), records)
        await grant_text_to_sql_select(conn, table_name)
    
    dataset = Dataset(
        company_id=company_id, table_name=table_name, display_name=display_name,
        description=description, columns_schema=schema_list, row_count=row_count,
        source="csv_upload", created_by=current_user.id,
    )
    db.add(dataset)
    
    imp = DatasetImport(
        dataset_id=0, company_id=company_id, filename=file.filename,
        file_path=str(file_path), row_count=row_count, mode="replace",
        status="completed",  imported_by=current_user.id,
    )
    
    await db.commit()
    await db.refresh(dataset)
    imp.dataset_id = dataset.id
    db.add(imp)
    await db.commit()
    
    await log_action(db, action="upload_table", user_id=current_user.id, company_id=company_id, resource_type="dataset", resource_id=dataset.id, details={"rows": row_count})
    return dataset

@router.post("/{company_id}/{dataset_id}/upload-data", response_model=DatasetImportOut, status_code=201)
async def upload_data_to_existing(
    company_id: int, dataset_id: int,
    file: UploadFile = File(...),
    mode: str = Form("append"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Upload CSV data into an existing table."""
    ensure_company_admin_access(current_user, company_id)
    if mode not in ("append", "replace"):
        raise HTTPException(status_code=400, detail="mode must be append or replace")
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id, Dataset.company_id == company_id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    company_dir = Path(settings.UPLOAD_DIR) / "companies" / str(company_id) / "csv"
    company_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = company_dir / safe_name
    
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    df = pd.read_csv(file_path)
    
    schema = dataset.columns_schema or []
    safe_cols = [s["name"] for s in schema]
    col_names = ", ".join(_quote_identifier(c) for c in safe_cols)
    placeholders = ", ".join(f":{c}" for c in safe_cols)
    insert_sql = f'INSERT INTO {_quote_identifier(dataset.table_name)} ({col_names}) VALUES ({placeholders})'
    
    records = []
    for _, row in df.iterrows():
        record = {}
        for i, s in enumerate(schema):
            original = s.get("original_name", s["name"])
            val = row.get(original, row.iloc[i] if i < len(row) else None)
            record[s["name"]] = None if pd.isna(val) else val
            if s["type"] == "integer" and record[s["name"]] is not None:
                record[s["name"]] = int(record[s["name"]])
        records.append(record)
    
    async with dataset_write_transaction() as conn:
        if mode == "replace":
            await conn.execute(text(f'DELETE FROM {_quote_identifier(dataset.table_name)}'))
        if records:
            await conn.execute(text(insert_sql), records)
        count_result = await conn.execute(text(f'SELECT COUNT(*) FROM {_quote_identifier(dataset.table_name)}'))
        dataset.row_count = count_result.scalar()
    
    imp = DatasetImport(
        dataset_id=dataset.id, company_id=company_id, filename=file.filename,
        file_path=str(file_path), row_count=len(records), mode=mode,
        status="completed", imported_by=current_user.id,
    )
    db.add(imp)
    await db.commit()
    await db.refresh(imp)
    return imp

@router.get("/{company_id}/{dataset_id}/rows")
async def get_dataset_rows(
    company_id: int,
    dataset_id: int,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Fetch rows from a dataset table for viewing."""
    ensure_company_admin_access(current_user, company_id)
    limit = max(1, min(limit, 500))
    offset = max(0, offset)
    result = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.company_id == company_id)
    )
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    schema = dataset.columns_schema or []
    col_names = [s["name"] for s in schema]
    if not col_names:
        return {"columns": [], "rows": [], "total": 0}

    col_list = ", ".join(_quote_identifier(c) for c in col_names)
    # Use id for stable ordering
    sql = f'SELECT id, {col_list} FROM {_quote_identifier(dataset.table_name)} ORDER BY id LIMIT :limit OFFSET :offset'
    count_sql = f'SELECT COUNT(*) FROM {_quote_identifier(dataset.table_name)}'

    async with engine.connect() as conn:
        rows_result = await conn.execute(text(sql), {"limit": limit, "offset": offset})
        rows = rows_result.fetchall()
        count_result = await conn.execute(text(count_sql))
        total = count_result.scalar() or 0

    columns = ["id"] + col_names
    data = [dict(zip(columns, row)) for row in rows]
    return {"columns": col_names, "rows": data, "total": total}


@router.post("/{company_id}/preview-csv", response_model=CSVPreviewOut)
async def preview_csv(company_id: int, file: UploadFile = File(...), current_user: User = Depends(require_admin)):
    """Preview a CSV file before importing."""
    ensure_company_admin_access(current_user, company_id)
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    df = pd.read_csv(file.file, nrows=100)
    return CSVPreviewOut(
        columns=list(df.columns),
        dtypes={col: str(df[col].dtype) for col in df.columns},
        row_count=len(df),
        preview_rows=df.head(10).fillna("").to_dict(orient="records"),
    )


# ── SQL import endpoints ─────────────────────────────────────────────

async def _existing_table_names(company_id: int, db: AsyncSession) -> set[str]:
    """Collect all table_name values already registered for this company."""
    result = await db.execute(
        select(Dataset.table_name).where(Dataset.company_id == company_id)
    )
    return {row[0] for row in result.all()}


@router.post("/{company_id}/preview-sql", response_model=SQLPreviewOut)
async def preview_sql(
    company_id: int,
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Parse a SQL dump and return a preview of tables + data it contains."""
    ensure_company_admin_access(current_user, company_id)
    if not file.filename or not file.filename.lower().endswith(".sql"):
        raise HTTPException(status_code=400, detail="Only .sql files are allowed")

    try:
        raw_bytes = await read_sql_upload(file, settings.MAX_SQL_UPLOAD_BYTES)
        parsed_tables = parse_sql_dump(
            raw_bytes.decode("utf-8", errors="replace"),
            limits=_sql_import_limits(),
        )
    except SQLImportValidationError as exc:
        correlation_id = correlation_id_from_request(request)
        logger.warning(
            "SQL preview rejected correlation_id=%s reason=%s",
            correlation_id,
            exc,
        )
        raise HTTPException(
            status_code=400,
            detail=public_error_detail(
                request,
                "The SQL file failed safety validation.",
                exc,
            ),
        ) from exc
    if not parsed_tables:
        raise HTTPException(status_code=400, detail="No CREATE TABLE statements found in the SQL file")

    existing = await _existing_table_names(company_id, db)

    previews: list[SQLTablePreview] = []
    used_names: set[str] = set(existing)
    total_rows = 0

    for pt in parsed_tables:
        desired = _safe_table_name(company_id, pt.original_name)
        is_dup = desired in existing
        target = make_unique_table_name(desired, used_names)
        used_names.add(target)

        cols = [
            {"name": c.name, "type": c.pg_type, "nullable": c.nullable, "original_type": c.original_type}
            for c in pt.columns
        ]
        previews.append(SQLTablePreview(
            original_name=pt.original_name,
            target_name=target,
            columns=cols,
            row_count=pt.row_count,
            preview_rows=pt.preview_rows[:10],
            is_duplicate=is_dup,
        ))
        total_rows += pt.row_count

    return SQLPreviewOut(tables=previews, total_tables=len(previews), total_rows=total_rows)


@router.post("/{company_id}/upload-sql", status_code=201)
async def upload_sql(
    company_id: int,
    request: Request,
    file: UploadFile = File(...),
    display_name: str = Form(...),
    description: str = Form(""),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Import a SQL dump: create tables and insert data, returns list of created datasets."""
    ensure_company_admin_access(current_user, company_id)
    if not file.filename or not file.filename.lower().endswith(".sql"):
        raise HTTPException(status_code=400, detail="Only .sql files are allowed")

    company_dir = Path(settings.UPLOAD_DIR) / "companies" / str(company_id) / "sql"
    company_dir.mkdir(parents=True, exist_ok=True)
    safe_file = f"{uuid.uuid4().hex}_{_safe_upload_name(file.filename)}"
    file_path = company_dir / safe_file

    try:
        raw_bytes = await read_sql_upload(file, settings.MAX_SQL_UPLOAD_BYTES)
        parsed_tables = parse_sql_dump(
            raw_bytes.decode("utf-8", errors="replace"),
            limits=_sql_import_limits(),
        )
    except SQLImportValidationError as exc:
        correlation_id = correlation_id_from_request(request)
        logger.warning(
            "SQL import rejected correlation_id=%s reason=%s",
            correlation_id,
            exc,
        )
        raise HTTPException(
            status_code=400,
            detail=public_error_detail(
                request,
                "The SQL file failed safety validation.",
                exc,
            ),
        ) from exc

    if not parsed_tables:
        raise HTTPException(status_code=400, detail="No CREATE TABLE statements found in the SQL file")

    with open(file_path, "wb") as f:
        f.write(raw_bytes)

    existing = await _existing_table_names(company_id, db)
    used_names: set[str] = set(existing)
    created: list[dict] = []
    errors: list[dict] = []

    for pt in parsed_tables:
        desired = _safe_table_name(company_id, pt.original_name)
        pg_name = make_unique_table_name(desired, used_names)
        used_names.add(pg_name)

        try:
            create_sql = build_pg_create_sql(pt, pg_name)
            insert_sql, records = build_pg_insert_sql(pt, pg_name)
            async with dataset_write_transaction() as conn:
                await conn.execute(text(create_sql))
                if records:
                    batch_size = 500
                    for i in range(0, len(records), batch_size):
                        await conn.execute(text(insert_sql), records[i : i + batch_size])
                await grant_text_to_sql_select(conn, pg_name)
            row_count = len(records)
        except Exception as exc:
            correlation_id = correlation_id_from_request(request)
            logger.exception(
                "SQL table import failed correlation_id=%s table=%s",
                correlation_id,
                pt.original_name,
            )
            errors.append({
                "table": pt.original_name,
                "step": "import_table",
                "correlation_id": correlation_id,
            })
            continue

        table_display = f"{display_name} — {pt.original_name}" if len(parsed_tables) > 1 else display_name
        schema_list = [
            {"name": c.name, "type": c.original_type or c.pg_type, "nullable": c.nullable}
            for c in pt.columns
        ]

        dataset = Dataset(
            company_id=company_id,
            table_name=pg_name,
            display_name=table_display,
            description=description,
            columns_schema=schema_list,
            row_count=row_count,
            source="sql_upload",
            created_by=current_user.id,
        )
        db.add(dataset)
        await db.commit()
        await db.refresh(dataset)

        imp = DatasetImport(
            dataset_id=dataset.id,
            company_id=company_id,
            filename=file.filename,
            file_path=str(file_path),
            row_count=row_count,
            mode="replace",
            status="completed",
            error_message=None,
            imported_by=current_user.id,
        )
        db.add(imp)
        await db.commit()

        await log_action(
            db,
            action="upload_sql",
            user_id=current_user.id,
            company_id=company_id,
            resource_type="dataset",
            resource_id=dataset.id,
            details={"table": pt.original_name, "rows": row_count, "pg_table": pg_name},
        )
        created.append({
            "id": dataset.id,
            "table_name": pg_name,
            "display_name": table_display,
            "original_name": pt.original_name,
            "row_count": row_count,
        })

    if not created and errors:
        raise HTTPException(
            status_code=400,
            detail=public_error_detail(
                request,
                "Failed to import any table. Contact an administrator with the correlation ID.",
            ),
        )

    return {
        "imported_tables": created,
        "total_tables": len(created),
        "errors": errors if errors else None,
    }
