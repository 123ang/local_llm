from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import require_admin, require_super_admin
from app.core.security import get_current_user
from app.schemas.user import UserCreate, UserUpdate, UserOut
from app.services.user_service import create_user, get_users, get_user, update_user, get_user_by_email
from app.services.audit_service import log_action
from app.models.user import User

router = APIRouter(prefix="/users", tags=["users"])

@router.get("", response_model=list[UserOut])
async def list_users(company_id: int | None = Query(None), current_user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    # Admins can only see their company's users; super_admin can see all
    if current_user.role != "super_admin" and company_id != current_user.company_id:
        company_id = current_user.company_id
    users = await get_users(db, company_id=company_id)
    result = []
    for u in users:
        result.append(UserOut(
            id=u.id, email=u.email, full_name=u.full_name, role=u.role,
            company_id=u.company_id, company_name=u.company.name if u.company else None,
            is_active=u.is_active, created_at=u.created_at,
        ))
    return result

@router.post("", response_model=UserOut, status_code=201)
async def create_new_user(data: UserCreate, current_user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    existing = await get_user_by_email(db, data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    # Admins can only create users for their company
    company_id = data.company_id
    if current_user.role != "super_admin":
        company_id = current_user.company_id
        if data.role in ("super_admin", "admin"):
            raise HTTPException(status_code=403, detail="Cannot create admin users")
    user = await create_user(db, email=data.email, full_name=data.full_name, password=data.password, role=data.role, company_id=company_id)
    await log_action(db, action="create_user", user_id=current_user.id, company_id=company_id, resource_type="user", resource_id=user.id)
    return UserOut(
        id=user.id, email=user.email, full_name=user.full_name, role=user.role,
        company_id=user.company_id, is_active=user.is_active, created_at=user.created_at,
    )

@router.patch("/{user_id}", response_model=UserOut)
async def update_existing_user(user_id: int, data: UserUpdate, current_user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    updates = data.model_dump(exclude_unset=True)
    user = await update_user(db, user_id, **updates)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut(
        id=user.id, email=user.email, full_name=user.full_name, role=user.role,
        company_id=user.company_id, is_active=user.is_active, created_at=user.created_at,
    )
