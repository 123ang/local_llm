"""
Script to create two companies and load their data:
1. UUM - loads uum_db.sql
2. Kedah Investment - loads investment CSV (after processing)
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from app.core.database import async_session, engine
from app.core.config import settings
from app.models.company import Company
from app.models.dataset import Dataset, DatasetImport
from app.services.company_service import create_company
from app.ingestion.sql_importer import (
    parse_sql_dump,
    build_pg_create_sql,
    build_pg_insert_sql,
    make_unique_table_name,
)
import pandas as pd
import re
from datetime import datetime, date


def _safe_table_name(company_id: int, name: str) -> str:
    clean = re.sub(r'[^a-z0-9_]', '_', name.lower().strip())
    return f"c{company_id}_{clean}"


async def get_existing_table_names(company_id: int, db: AsyncSession) -> set[str]:
    """Get all existing table names for a company."""
    result = await db.execute(
        select(Dataset.table_name).where(Dataset.company_id == company_id)
    )
    return {row[0] for row in result.all()}


async def create_companies(db: AsyncSession):
    """Create the two companies."""
    print("Creating companies...")
    
    # Check if companies already exist
    result = await db.execute(select(Company).where(Company.name == "UUM"))
    uum_company = result.scalar_one_or_none()
    if not uum_company:
        result = await db.execute(select(Company).where(Company.name == "UUM utlc"))
        uum_company = result.scalar_one_or_none()
        if uum_company:
            uum_company.name = "UUM"
            await db.commit()
            await db.refresh(uum_company)
            print("[OK] Renamed company UUM utlc -> UUM")
    if not uum_company:
        uum_company = await create_company(db, name="UUM", description="UUM database company")
        print(f"[OK] Created company: {uum_company.name} (ID: {uum_company.id})")
    else:
        print(f"[OK] Company already exists: {uum_company.name} (ID: {uum_company.id})")
    
    result = await db.execute(select(Company).where(Company.name == "Kedah Investment"))
    kedah_company = result.scalar_one_or_none()
    
    if not kedah_company:
        kedah_company = await create_company(db, name="Kedah Investment", description="Kedah approved investment data")
        print(f"[OK] Created company: {kedah_company.name} (ID: {kedah_company.id})")
    else:
        print(f"[OK] Company already exists: {kedah_company.name} (ID: {kedah_company.id})")
    
    return uum_company, kedah_company


async def load_uum_sql(company: Company, db: AsyncSession):
    """Load uum_db.sql into the UUM company."""
    print(f"\nLoading uum_db.sql for company: {company.name}...")
    
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
            
            # Insert data
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
            error_count += 1
    
    print(f"\n[OK] UUM SQL import complete: {created_count} tables created, {error_count} errors")


async def load_investment_csv(company: Company, db: AsyncSession):
    """Load investment CSV into the Kedah Investment company."""
    print(f"\nLoading investment CSV for company: {company.name}...")
    
    investment_dir = Path(__file__).parent
    csv_file = investment_dir / "output" / "approved_investment_llm_ready.csv"
    
    if not csv_file.exists():
        print(f"[ERROR] {csv_file} not found!")
        print("   Please run build_llm_ready_csv_v_2.py first to generate the CSV.")
        return
    
    print(f"Reading CSV file: {csv_file}")
    df = pd.read_csv(csv_file)
    print(f"  Found {len(df)} rows")
    
    table_name = _safe_table_name(company.id, "approved_investment_llm_ready")
    
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
    
    # Create table
    create_sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" (id SERIAL PRIMARY KEY, {", ".join(col_defs)})'
    async with engine.begin() as conn:
        await conn.execute(text(create_sql))
    
    print(f"  Created table: {table_name}")
    
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
                    try:
                        record[s["name"]] = int(record[s["name"]])
                    except (ValueError, TypeError):
                        record[s["name"]] = None
            records.append(record)
        
        batch_size = 500
        async with engine.begin() as conn:
            for i in range(0, len(records), batch_size):
                batch = records[i : i + batch_size]
                await conn.execute(text(insert_sql), batch)
        row_count = len(records)
    
    # Create dataset record
    dataset = Dataset(
        company_id=company.id,
        table_name=table_name,
        display_name="Approved Investment LLM Ready",
        description="Kedah approved investment data - LLM ready format",
        columns_schema=schema_list,
        row_count=row_count,
        source="csv_upload",
        created_by=1,  # System user
    )
    db.add(dataset)
    await db.commit()
    await db.refresh(dataset)
    
    # Create import record
    imp = DatasetImport(
        dataset_id=dataset.id,
        company_id=company.id,
        filename=csv_file.name,
        file_path=str(csv_file),
        row_count=row_count,
        mode="replace",
        status="completed",
        imported_by=1,
    )
    db.add(imp)
    await db.commit()
    
    print(f"[OK] Investment CSV import complete: {row_count} rows loaded into {table_name}")


async def main():
    """Main function to create companies and load data."""
    print("=" * 60)
    print("Company Setup and Data Loading Script")
    print("=" * 60)
    
    async with async_session() as db:
        # Create companies
        uum_company, kedah_company = await create_companies(db)
        
        # Load UUM SQL data
        await load_uum_sql(uum_company, db)
        
        # Load Investment CSV data
        await load_investment_csv(kedah_company, db)
    
    print("\n" + "=" * 60)
    print("[OK] Setup complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
