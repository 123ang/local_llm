import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.company import Company
from app.models.user import User

def _slugify(name: str) -> str:
    slug = re.sub(r'[^\w\s-]', '', name.lower().strip())
    return re.sub(r'[\s_]+', '-', slug)

async def create_company(db: AsyncSession, name: str, description: str | None = None) -> Company:
    slug = _slugify(name)
    # Ensure unique slug
    base_slug = slug
    counter = 1
    while True:
        exists = await db.execute(select(Company).where(Company.slug == slug))
        if not exists.scalar_one_or_none():
            break
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    company = Company(name=name, slug=slug, description=description)
    db.add(company)
    await db.commit()
    await db.refresh(company)
    return company

async def get_companies(db: AsyncSession, include_inactive: bool = False) -> list:
    query = select(Company)
    if not include_inactive:
        query = query.where(Company.is_active == True)
    query = query.order_by(Company.name)
    result = await db.execute(query)
    return list(result.scalars().all())

async def get_company(db: AsyncSession, company_id: int) -> Company | None:
    result = await db.execute(select(Company).where(Company.id == company_id))
    return result.scalar_one_or_none()

async def update_company(db: AsyncSession, company_id: int, **kwargs) -> Company | None:
    company = await get_company(db, company_id)
    if not company:
        return None
    for key, value in kwargs.items():
        if value is not None and hasattr(company, key):
            setattr(company, key, value)
    await db.commit()
    await db.refresh(company)
    return company

async def get_company_stats(db: AsyncSession, company_id: int) -> dict:
    user_count = await db.execute(select(func.count(User.id)).where(User.company_id == company_id))
    return {"user_count": user_count.scalar() or 0}
