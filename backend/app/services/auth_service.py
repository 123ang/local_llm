from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token

async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    result = await db.execute(
        select(User).options(selectinload(User.company)).where(User.email == email)
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    return user

async def create_token_for_user(user: User) -> dict:
    token = create_access_token(data={"sub": str(user.id), "role": user.role, "company_id": user.company_id})
    return {"access_token": token, "token_type": "bearer"}
