from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.core.database import get_db
from app.core.dependencies import require_admin, require_super_admin, get_user_department_ids
from app.schemas.user import UserCreate, UserUpdate, UserOut
from app.services.user_service import create_user, get_users, get_user, update_user, get_user_by_email
from app.services.audit_service import log_action
from app.models.user import User
from app.models.department import Department, UserDepartmentAccess

router = APIRouter(prefix="/users", tags=["users"])


async def _serialize_user_departments(db: AsyncSession, user_id: int) -> list[dict]:
    result = await db.execute(
        select(Department)
        .join(UserDepartmentAccess, UserDepartmentAccess.department_id == Department.id)
        .where(UserDepartmentAccess.user_id == user_id)
        .order_by(Department.name)
    )
    return [
        {"id": dept.id, "company_id": dept.company_id, "name": dept.name, "slug": dept.slug}
        for dept in result.scalars().all()
    ]


async def _user_out(db: AsyncSession, user: User) -> UserOut:
    departments = await _serialize_user_departments(db, user.id)
    return UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        company_id=user.company_id,
        company_name=user.company.name if user.company else None,
        department_ids=[dept["id"] for dept in departments],
        departments=departments,
        is_active=user.is_active,
        created_at=user.created_at,
    )


async def _replace_department_grants(
    db: AsyncSession,
    user_id: int,
    company_id: int | None,
    department_ids: list[int],
    granted_by: int | None,
) -> None:
    await db.execute(delete(UserDepartmentAccess).where(UserDepartmentAccess.user_id == user_id))
    if company_id is None or not department_ids:
        return
    requested = sorted({int(i) for i in department_ids})
    result = await db.execute(
        select(Department.id).where(
            Department.company_id == company_id,
            Department.id.in_(requested),
            Department.is_active == True,
        )
    )
    valid_ids = sorted({row[0] for row in result.all()})
    if set(valid_ids) != set(requested):
        raise HTTPException(status_code=400, detail="One or more departments do not belong to this organization")
    for department_id in valid_ids:
        db.add(UserDepartmentAccess(user_id=user_id, department_id=department_id, granted_by=granted_by))


async def _department_ids_or_default(
    db: AsyncSession,
    company_id: int | None,
    requested_department_ids: list[int],
) -> list[int]:
    if requested_department_ids or company_id is None:
        return requested_department_ids
    result = await db.execute(
        select(Department.id)
        .where(
            Department.company_id == company_id,
            Department.slug == "general",
            Department.is_active == True,
        )
        .limit(1)
    )
    rows = result.all()
    return [int(rows[0][0])] if rows else []


@router.get("", response_model=list[UserOut])
async def list_users(company_id: int | None = Query(None), current_user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    # Admins can only see their company's users; super_admin can see all
    if current_user.role != "super_admin" and company_id != current_user.company_id:
        company_id = current_user.company_id
    if current_user.role == "super_admin":
        users = await get_users(db, company_id=company_id)
    else:
        allowed_departments = await get_user_department_ids(db, current_user, company_id)
        if not allowed_departments:
            return []
        result = await db.execute(
            select(User)
            .join(UserDepartmentAccess, UserDepartmentAccess.user_id == User.id)
            .where(User.company_id == company_id, UserDepartmentAccess.department_id.in_(allowed_departments))
            .distinct()
            .order_by(User.full_name)
        )
        users = list(result.scalars().all())
    result = []
    for u in users:
        result.append(await _user_out(db, u))
    return result

@router.post("", response_model=UserOut, status_code=201)
async def create_new_user(data: UserCreate, current_user: User = Depends(require_super_admin), db: AsyncSession = Depends(get_db)):
    if data.role not in ("user", "admin", "super_admin"):
        raise HTTPException(status_code=400, detail="Invalid role")
    existing = await get_user_by_email(db, data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    company_id = data.company_id
    user = await create_user(db, email=data.email, full_name=data.full_name, password=data.password, role=data.role, company_id=company_id)
    department_ids = data.department_ids
    if data.role != "super_admin":
        department_ids = await _department_ids_or_default(db, company_id, data.department_ids)
    await _replace_department_grants(db, user.id, company_id, department_ids, current_user.id)
    await db.commit()
    await db.refresh(user)
    await log_action(db, action="create_user", user_id=current_user.id, company_id=company_id, resource_type="user", resource_id=user.id)
    return await _user_out(db, user)

@router.patch("/{user_id}", response_model=UserOut)
async def update_existing_user(user_id: int, data: UserUpdate, current_user: User = Depends(require_super_admin), db: AsyncSession = Depends(get_db)):
    updates = data.model_dump(exclude_unset=True)
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if "role" in updates and updates["role"] not in ("user", "admin", "super_admin"):
        raise HTTPException(status_code=400, detail="Invalid role")

    department_ids = updates.pop("department_ids", None)
    user = await update_user(db, user_id, **updates)
    if department_ids is not None:
        await _replace_department_grants(db, user.id, user.company_id, department_ids, current_user.id)
        await db.commit()
        await db.refresh(user)
    return await _user_out(db, user)
