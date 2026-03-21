"""Verify that data was imported correctly."""
import asyncio
import sys
from pathlib import Path

backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from sqlalchemy import text, select
from app.core.database import async_session
from app.models.company import Company
from app.models.dataset import Dataset


async def verify():
    """Verify imported data."""
    print("=" * 60)
    print("Verifying Data Import")
    print("=" * 60)
    
    async with async_session() as db:
        # Check UUM company
        result = await db.execute(select(Company).where(Company.name == "UUM"))
        uum_company = result.scalar_one_or_none()
        if uum_company:
            print(f"\n[UUM] Company ID: {uum_company.id}")
            result = await db.execute(
                select(Dataset).where(Dataset.company_id == uum_company.id)
            )
            datasets = result.scalars().all()
            for ds in datasets:
                async with async_session() as conn:
                    count_result = await conn.execute(text(f'SELECT COUNT(*) FROM "{ds.table_name}"'))
                    count = count_result.scalar()
                    print(f"  - {ds.display_name} ({ds.table_name}): {count} rows")
        else:
            print("\n[ERROR] UUM company not found!")
        
        # Check Kedah Investment company
        result = await db.execute(select(Company).where(Company.name == "Kedah Investment"))
        kedah_company = result.scalar_one_or_none()
        if kedah_company:
            print(f"\n[Kedah Investment] Company ID: {kedah_company.id}")
            result = await db.execute(
                select(Dataset).where(Dataset.company_id == kedah_company.id)
            )
            datasets = result.scalars().all()
            for ds in datasets:
                async with async_session() as conn:
                    count_result = await conn.execute(text(f'SELECT COUNT(*) FROM "{ds.table_name}"'))
                    count = count_result.scalar()
                    print(f"  - {ds.display_name} ({ds.table_name}): {count} rows")
        else:
            print("\n[ERROR] Kedah Investment company not found!")
    
    print("\n" + "=" * 60)
    print("[OK] Verification complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(verify())
