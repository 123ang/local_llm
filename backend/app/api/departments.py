import re

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import (
    ensure_company_access,
    get_user_department_ids,
    require_admin,
    require_super_admin,
    resolve_department_scope,
)
from app.models.department import Department, UserDepartmentAccess
from app.models.user import User
from app.schemas.department import DepartmentCreate, DepartmentOut, DepartmentUpdate, UserDepartmentGrantUpdate
from app.services.audit_service import log_action

router = APIRouter(prefix="/departments", tags=["departments"])


def _slugify(name: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", name.lower().strip())
    return re.sub(r"[\s_]+", "-", slug).strip("-") or "department"


async def _unique_slug(db: AsyncSession, company_id: int, name: str) -> str:
    base_slug = _slugify(name)
    slug = base_slug
    counter = 1
    while True:
        result = await db.execute(
            select(Department).where(Department.company_id == company_id, Department.slug == slug)
        )
        if not result.scalar_one_or_none():
            return slug
        counter += 1
        slug = f"{base_slug}-{counter}"


async def _get_department_ids_for_company(db: AsyncSession, company_id: int, ids: list[int]) -> list[int]:
    if not ids:
        return []
    result = await db.execute(
        select(Department.id).where(
            Department.company_id == company_id,
            Department.id.in_(sorted({int(i) for i in ids})),
            Department.is_active == True,
        )
    )
    return sorted({row[0] for row in result.all()})


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


@router.get("", response_model=list[DepartmentOut])
async def list_departments(
    company_id: int | None = Query(None),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != "super_admin":
        company_id = current_user.company_id
    if company_id is None:
        return []
    ensure_company_access(current_user, company_id)
    query = select(Department).where(Department.company_id == company_id).order_by(Department.name)
    if current_user.role != "super_admin":
        allowed_ids = await get_user_department_ids(db, current_user, company_id)
        if not allowed_ids:
            return []
        query = query.where(Department.id.in_(allowed_ids))
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("", response_model=DepartmentOut, status_code=201)
async def create_department(
    data: DepartmentCreate,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    slug = await _unique_slug(db, data.company_id, data.name)
    department = Department(
        company_id=data.company_id,
        name=data.name,
        slug=slug,
        description=data.description,
    )
    db.add(department)
    await db.commit()
    await db.refresh(department)
    await log_action(
        db,
        action="create_department",
        user_id=current_user.id,
        company_id=data.company_id,
        resource_type="department",
        resource_id=department.id,
    )
    return department


@router.patch("/{department_id}", response_model=DepartmentOut)
async def update_department(
    department_id: int,
    data: DepartmentUpdate,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Department).where(Department.id == department_id))
    department = result.scalar_one_or_none()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    updates = data.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(department, key, value)
    await db.commit()
    await db.refresh(department)
    return department


@router.get("/users/{user_id}/grants")
async def get_user_department_grants(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    ensure_company_access(current_user, target_user.company_id)
    if current_user.role != "super_admin":
        admin_scope = set(await resolve_department_scope(db, current_user, target_user.company_id))
        target_scope = set(await get_user_department_ids(db, target_user, target_user.company_id))
        if not admin_scope.intersection(target_scope):
            raise HTTPException(status_code=403, detail="User is outside your department scope")
    departments = await _serialize_user_departments(db, user_id)
    return {"user_id": user_id, "department_ids": [d["id"] for d in departments], "departments": departments}


@router.put("/users/{user_id}/grants")
async def replace_user_department_grants(
    user_id: int,
    data: UserDepartmentGrantUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    if target_user.company_id is None:
        raise HTTPException(status_code=400, detail="User must belong to an organization before granting departments")
    ensure_company_access(current_user, target_user.company_id)

    requested_ids = sorted({int(i) for i in data.department_ids})
    valid_ids = await _get_department_ids_for_company(db, target_user.company_id, requested_ids)
    if set(valid_ids) != set(requested_ids):
        raise HTTPException(status_code=400, detail="One or more departments do not belong to this organization")

    if current_user.role == "super_admin":
        await db.execute(delete(UserDepartmentAccess).where(UserDepartmentAccess.user_id == target_user.id))
        controlled_ids = valid_ids
    else:
        controlled_ids = await resolve_department_scope(db, current_user, target_user.company_id)
        if set(valid_ids) - set(controlled_ids):
            raise HTTPException(status_code=403, detail="Cannot grant departments outside your scope")
        await db.execute(
            delete(UserDepartmentAccess).where(
                UserDepartmentAccess.user_id == target_user.id,
                UserDepartmentAccess.department_id.in_(controlled_ids),
            )
        )

    for department_id in valid_ids:
        db.add(
            UserDepartmentAccess(
                user_id=target_user.id,
                department_id=department_id,
                granted_by=current_user.id,
            )
        )
    await db.commit()
    await log_action(
        db,
        action="replace_user_department_grants",
        user_id=current_user.id,
        company_id=target_user.company_id,
        resource_type="user",
        resource_id=target_user.id,
        details={"department_ids": valid_ids, "controlled_department_ids": controlled_ids},
    )
    departments = await _serialize_user_departments(db, target_user.id)
    return {"user_id": target_user.id, "department_ids": [d["id"] for d in departments], "departments": departments}
