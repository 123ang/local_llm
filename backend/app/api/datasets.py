import os
import uuid
import re
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.core.database import get_db, engine
from app.core.dependencies import require_admin
from app.core.config import settings
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

def _safe_table_name(company_id: int, name: str) -> str:
    clean = re.sub(r'[^a-z0-9_]', '_', name.lower().strip())
    return f"c{company_id}_{clean}"

@router.get("/{company_id}", response_model=list[DatasetOut])
async def list_datasets(company_id: int, current_user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Dataset).where(Dataset.company_id == company_id).order_by(Dataset.created_at.desc()))
    return list(result.scalars().all())

@router.post("/{company_id}/manual", response_model=DatasetOut, status_code=201)
async def create_manual_table(company_id: int, data: DatasetCreateManual, current_user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    table_name = _safe_table_name(company_id, data.display_name)
    cols = []
    schema_list = []
    for col in data.columns:
        pg_type = TYPE_MAP.get(col.type, "TEXT")
        null = "" if col.nullable else " NOT NULL"
        cols.append(f'"{col.name}" {pg_type}{null}')
        schema_list.append({"name": col.name, "type": col.type, "nullable": col.nullable})
    
    col_defs = ", ".join(cols)
    create_sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" (id SERIAL PRIMARY KEY, {col_defs})'
    
    async with engine.begin() as conn:
        await conn.execute(text(create_sql))
    
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
    if not file.filename.endswith(".csv"):
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
    for col_name in df.columns:
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
        safe_col = re.sub(r'[^a-z0-9_]', '_', col_name.lower().strip())
        col_defs.append(f'"{safe_col}" {pg_type}')
        schema_list.append({"name": safe_col, "type": col_type, "nullable": True, "original_name": col_name})
    
    create_sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" (id SERIAL PRIMARY KEY, {", ".join(col_defs)})'
    async with engine.begin() as conn:
        await conn.execute(text(create_sql))
    
    # Insert data
    row_count = 0
    if not df.empty:
        safe_cols = [s["name"] for s in schema_list]
        col_names = ", ".join(f'"{c}"' for c in safe_cols)
        placeholders = ", ".join(f":{c}" for c in safe_cols)
        insert_sql = f'INSERT INTO "{table_name}" ({col_names}) VALUES ({placeholders})'
        
        records = []
        for _, row in df.iterrows():
            record = {}
            for i, s in enumerate(schema_list):
                val = row[df.columns[i]]
                record[s["name"]] = None if pd.isna(val) else val
                if s["type"] == "integer" and record[s["name"]] is not None:
                    record[s["name"]] = int(record[s["name"]])
            records.append(record)
        
        async with engine.begin() as conn:
            await conn.execute(text(insert_sql), records)
        row_count = len(records)
    
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
    
    if mode == "replace":
        async with engine.begin() as conn:
            await conn.execute(text(f'DELETE FROM "{dataset.table_name}"'))
    
    schema = dataset.columns_schema or []
    safe_cols = [s["name"] for s in schema]
    col_names = ", ".join(f'"{c}"' for c in safe_cols)
    placeholders = ", ".join(f":{c}" for c in safe_cols)
    insert_sql = f'INSERT INTO "{dataset.table_name}" ({col_names}) VALUES ({placeholders})'
    
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
    
    async with engine.begin() as conn:
        await conn.execute(text(insert_sql), records)
    
    # Update row count
    async with engine.begin() as conn:
        count_result = await conn.execute(text(f'SELECT COUNT(*) FROM "{dataset.table_name}"'))
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

    col_list = ", ".join(f'"{c}"' for c in col_names)
    # Use id for stable ordering
    sql = f'SELECT id, {col_list} FROM "{dataset.table_name}" ORDER BY id LIMIT :limit OFFSET :offset'
    count_sql = f'SELECT COUNT(*) FROM "{dataset.table_name}"'

    async with engine.begin() as conn:
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
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Parse a SQL dump and return a preview of tables + data it contains."""
    if not file.filename or not file.filename.lower().endswith(".sql"):
        raise HTTPException(status_code=400, detail="Only .sql files are allowed")

    from app.ingestion.sql_importer import parse_sql_dump, make_unique_table_name

    raw = (await file.read()).decode("utf-8", errors="replace")
    parsed_tables = parse_sql_dump(raw)
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
    file: UploadFile = File(...),
    display_name: str = Form(...),
    description: str = Form(""),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Import a SQL dump: create tables and insert data, returns list of created datasets."""
    if not file.filename or not file.filename.lower().endswith(".sql"):
        raise HTTPException(status_code=400, detail="Only .sql files are allowed")

    from app.ingestion.sql_importer import (
        parse_sql_dump,
        build_pg_create_sql,
        build_pg_insert_sql,
        make_unique_table_name,
    )

    company_dir = Path(settings.UPLOAD_DIR) / "companies" / str(company_id) / "sql"
    company_dir.mkdir(parents=True, exist_ok=True)
    safe_file = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = company_dir / safe_file

    raw_bytes = await file.read()
    with open(file_path, "wb") as f:
        f.write(raw_bytes)

    raw = raw_bytes.decode("utf-8", errors="replace")
    parsed_tables = parse_sql_dump(raw)
    if not parsed_tables:
        raise HTTPException(status_code=400, detail="No CREATE TABLE statements found in the SQL file")

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
            async with engine.begin() as conn:
                await conn.execute(text(create_sql))
        except Exception as e:
            errors.append({"table": pt.original_name, "step": "create_table", "error": str(e)})
            continue

        row_count = 0
        if pt.insert_values:
            try:
                insert_sql, records = build_pg_insert_sql(pt, pg_name)
                if records:
                    batch_size = 500
                    async with engine.begin() as conn:
                        for i in range(0, len(records), batch_size):
                            await conn.execute(text(insert_sql), records[i : i + batch_size])
                    row_count = len(records)
            except Exception as e:
                errors.append({"table": pt.original_name, "step": "insert_data", "error": str(e)})

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
            status="completed" if not any(
                e["table"] == pt.original_name for e in errors
            ) else "error",
            error_message=next(
                (e["error"] for e in errors if e["table"] == pt.original_name), None
            ),
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
            detail=f"Failed to import any table. Errors: {errors}",
        )

    return {
        "imported_tables": created,
        "total_tables": len(created),
        "errors": errors if errors else None,
    }
