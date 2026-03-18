from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.user import User
from app.core.security import hash_password

async def create_user(db: AsyncSession, email: str, full_name: str, password: str, role: str = "user", company_id: int | None = None) -> User:
    user = User(
        email=email,
        full_name=full_name,
        hashed_password=hash_password(password),
        role=role,
        company_id=company_id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

async def get_user(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(
        select(User).options(selectinload(User.company)).where(User.id == user_id)
    )
    return result.scalar_one_or_none()

async def get_users(db: AsyncSession, company_id: int | None = None) -> list:
    query = select(User).options(selectinload(User.company))
    if company_id:
        query = query.where(User.company_id == company_id)
    query = query.order_by(User.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())

async def update_user(db: AsyncSession, user_id: int, **kwargs) -> User | None:
    user = await get_user(db, user_id)
    if not user:
        return None
    for key, value in kwargs.items():
        if value is not None and hasattr(user, key):
            setattr(user, key, value)
    await db.commit()
    await db.refresh(user)
    return user

async def ensure_super_admin(db: AsyncSession, email: str, password: str):
    """Create super admin if it doesn't exist (called on startup)."""
    existing = await get_user_by_email(db, email)
    if existing:
        return existing
    return await create_user(db, email=email, full_name="Super Admin", password=password, role="super_admin")
