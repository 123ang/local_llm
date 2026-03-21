"""Fix and re-import UUM SQL data with type conversion."""
import asyncio
import sys
from pathlib import Path

backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from app.core.database import async_session, engine
from app.models.company import Company
from app.models.dataset import Dataset, DatasetImport
from app.ingestion.sql_importer import (
    parse_sql_dump,
    build_pg_create_sql,
    build_pg_insert_sql,
    make_unique_table_name,
)
import re
from datetime import datetime, date

UUM_COMPANY_NAME = "UUM"


def _safe_table_name(company_id: int, name: str) -> str:
    clean = re.sub(r'[^a-z0-9_]', '_', name.lower().strip())
    return f"c{company_id}_{clean}"


async def get_existing_table_names(company_id: int, db: AsyncSession) -> set[str]:
    """Get all existing table names for a company."""
    result = await db.execute(
        select(Dataset.table_name).where(Dataset.company_id == company_id)
    )
    return {row[0] for row in result.all()}


async def fix_uum_import():
    """Re-import UUM SQL with proper type conversion."""
    print("=" * 60)
    print("Fixing UUM SQL Import")
    print("=" * 60)
    
    async with async_session() as db:
        from app.services.company_service import create_company

        result = await db.execute(select(Company).where(Company.name == UUM_COMPANY_NAME))
        company = result.scalar_one_or_none()
        if not company:
            result = await db.execute(select(Company).where(Company.name == "UUM utlc"))
            company = result.scalar_one_or_none()
            if company:
                company.name = UUM_COMPANY_NAME
                if not company.description:
                    company.description = "UUM database"
                await db.commit()
                await db.refresh(company)
                print(f"[OK] Renamed legacy company to: {company.name} (ID: {company.id})")
        if not company:
            company = await create_company(
                db, name=UUM_COMPANY_NAME, description="UUM database"
            )
            print(f"[OK] Created company: {company.name} (ID: {company.id})")
        else:
            print(f"Found company: {company.name} (ID: {company.id})")
        
        # Delete existing datasets for this company
        result = await db.execute(
            select(Dataset).where(Dataset.company_id == company.id)
        )
        existing_datasets = result.scalars().all()
        for ds in existing_datasets:
            # Drop the table
            try:
                async with engine.begin() as conn:
                    await conn.execute(text(f'DROP TABLE IF EXISTS "{ds.table_name}"'))
                print(f"  Dropped table: {ds.table_name}")
            except Exception as e:
                print(f"  Warning: Could not drop {ds.table_name}: {e}")
            # Delete dataset record
            await db.delete(ds)
        await db.commit()
        print("  Cleared existing datasets")
        
        # Load SQL file
        sql_file = Path(__file__).parent.parent / "uum_db.sql"
        if not sql_file.exists():
            print(f"[ERROR] {sql_file} not found!")
            return
        
        print(f"Reading SQL file: {sql_file}")
        with open(sql_file, "r", encoding="utf-8", errors="replace") as f:
            sql_content = f.read()
        
        parsed_tables = parse_sql_dump(sql_content)
        if not parsed_tables:
            print("[ERROR] No tables found in SQL file!")
            return
        
        print(f"Found {len(parsed_tables)} tables to import")
        
        existing = await get_existing_table_names(company.id, db)
        used_names: set[str] = set(existing)
        created_count = 0
        error_count = 0
        
        for pt in parsed_tables:
            desired = _safe_table_name(company.id, pt.original_name)
            pg_name = make_unique_table_name(desired, used_names)
            used_names.add(pg_name)
            
            print(f"  Processing table: {pt.original_name} -> {pg_name} ({pt.row_count} rows)")
            
            try:
                # Create table
                create_sql = build_pg_create_sql(pt, pg_name)
                async with engine.begin() as conn:
                    await conn.execute(text(create_sql))
                
                # Insert data with type conversion
                row_count = 0
                if pt.insert_values:
                    insert_sql, records = build_pg_insert_sql(pt, pg_name)
                    if records:
                        # Convert values to appropriate types based on column types
                        skip_pk = any(
                            c.is_primary_key and c.pg_type in ("SERIAL", "BIGSERIAL")
                            for c in pt.columns
                        )
                        if skip_pk:
                            pk_names = {c.name for c in pt.columns if c.is_primary_key}
                            insert_cols = [c for c in pt.columns if c.name not in pk_names]
                        else:
                            insert_cols = list(pt.columns)
                        
                        # Create a mapping of column names to types for conversion
                        col_type_map = {col.name: col.pg_type for col in insert_cols}
                        
                        # Convert record values to proper types
                        converted_records = []
                        for record in records:
                            converted_record = {}
                            for col_name, val in record.items():
                                if val is None or val == "" or (isinstance(val, str) and val.upper() == "NULL"):
                                    converted_record[col_name] = None
                                else:
                                    pg_type = col_type_map.get(col_name, "TEXT")
                                    # Convert based on PostgreSQL type
                                    if pg_type in ("INTEGER", "SMALLINT", "BIGINT", "SERIAL", "BIGSERIAL"):
                                        try:
                                            # Try to convert string to int
                                            if isinstance(val, str):
                                                # Remove quotes if present
                                                val = val.strip().strip("'\"")
                                            converted_record[col_name] = int(float(val)) if val else None
                                        except (ValueError, TypeError):
                                            # If conversion fails, keep as string (might be a valid string representation)
                                            converted_record[col_name] = str(val) if val else None
                                    elif pg_type in ("REAL", "DOUBLE PRECISION", "NUMERIC", "DECIMAL"):
                                        try:
                                            if isinstance(val, str):
                                                val = val.strip().strip("'\"")
                                            converted_record[col_name] = float(val) if val else None
                                        except (ValueError, TypeError):
                                            converted_record[col_name] = None
                                    elif pg_type == "BOOLEAN":
                                        if isinstance(val, str):
                                            val_lower = val.strip().lower()
                                            converted_record[col_name] = val_lower in ("true", "1", "yes", "t")
                                        else:
                                            converted_record[col_name] = bool(val) if val else None
                                    elif pg_type in ("TIMESTAMP", "DATE"):
                                        # Parse datetime strings
                                        if isinstance(val, str):
                                            val = val.strip().strip("'\"")
                                            try:
                                                from datetime import datetime
                                                # Try common formats
                                                for fmt in [
                                                    "%Y-%m-%d %H:%M:%S",
                                                    "%Y-%m-%d %H:%M:%S.%f",
                                                    "%Y-%m-%d",
                                                    "%Y/%m/%d %H:%M:%S",
                                                    "%Y/%m/%d",
                                                ]:
                                                    try:
                                                        converted_record[col_name] = datetime.strptime(val, fmt)
                                                        break
                                                    except ValueError:
                                                        continue
                                                else:
                                                    # If no format matched, try pandas parser
                                                    import pandas as pd
                                                    converted_record[col_name] = pd.to_datetime(val)
                                            except Exception:
                                                converted_record[col_name] = None
                                        elif isinstance(val, (datetime, date)):
                                            converted_record[col_name] = val
                                        else:
                                            converted_record[col_name] = None
                                    else:
                                        # TEXT, VARCHAR, etc. - keep as string but clean it
                                        if isinstance(val, str):
                                            converted_record[col_name] = val.strip().strip("'\"")
                                        else:
                                            converted_record[col_name] = str(val) if val else None
                            converted_records.append(converted_record)
                        
                        # Ensure NOT NULL columns have defaults where needed (e.g. truncated parse)
                        default_ts = datetime(2026, 1, 21, 6, 36, 11)
                        for rec in converted_records:
                            if rec.get("imported_at") is None:
                                rec["imported_at"] = default_ts
                        
                        batch_size = 500
                        async with engine.begin() as conn:
                            for i in range(0, len(converted_records), batch_size):
                                batch = converted_records[i : i + batch_size]
                                await conn.execute(text(insert_sql), batch)
                        row_count = len(converted_records)
                
                # Create dataset record
                schema_list = [
                    {"name": c.name, "type": c.original_type or c.pg_type, "nullable": c.nullable}
                    for c in pt.columns
                ]
                
                dataset = Dataset(
                    company_id=company.id,
                    table_name=pg_name,
                    display_name=pt.original_name,
                    description=f"Imported from uum_db.sql",
                    columns_schema=schema_list,
                    row_count=row_count,
                    source="sql_upload",
                    created_by=1,  # System user
                )
                db.add(dataset)
                await db.commit()
                await db.refresh(dataset)
                
                # Create import record
                imp = DatasetImport(
                    dataset_id=dataset.id,
                    company_id=company.id,
                    filename="uum_db.sql",
                    file_path=str(sql_file),
                    row_count=row_count,
                    mode="replace",
                    status="completed",
                    imported_by=1,
                )
                db.add(imp)
                await db.commit()
                
                print(f"    [OK] Created table {pg_name} with {row_count} rows")
                created_count += 1
                
            except Exception as e:
                print(f"    [ERROR] Error processing {pt.original_name}: {e}")
                import traceback
                traceback.print_exc()
                error_count += 1
        
        print(f"\n[OK] UUM SQL import complete: {created_count} tables created, {error_count} errors")


if __name__ == "__main__":
    asyncio.run(fix_uum_import())
