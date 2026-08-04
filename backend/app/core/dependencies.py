from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.department import Department, UserDepartmentAccess


def require_admin(current_user=Depends(get_current_user)):
    if current_user.role not in ("super_admin", "admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def require_super_admin(current_user=Depends(get_current_user)):
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin access required")
    return current_user


def role_can_curate_knowledge(current_user) -> bool:
    return getattr(current_user, "role", None) == "admin"


def require_knowledge_admin(current_user=Depends(get_current_user)):
    if not role_can_curate_knowledge(current_user):
        raise HTTPException(status_code=403, detail="Department admin access required")
    return current_user


def _unique_sorted_ints(values: list[int] | tuple[int, ...] | set[int] | None) -> list[int]:
    return sorted({int(value) for value in (values or []) if value is not None})


def filter_requested_department_ids(
    current_user,
    requested_department_ids: list[int] | None,
    granted_department_ids: list[int],
) -> list[int]:
    granted = set(_unique_sorted_ints(granted_department_ids))
    requested = _unique_sorted_ints(requested_department_ids)
    if not requested:
        return sorted(granted)
    missing = set(requested) - granted
    if missing:
        raise HTTPException(status_code=403, detail="Department access denied")
    return requested


def ensure_company_access(current_user, company_id: int | None) -> None:
    """Enforce tenant isolation for routes that accept a company_id path/query value."""
    if current_user.role == "super_admin":
        return
    if company_id is None or current_user.company_id != company_id:
        raise HTTPException(status_code=403, detail="Company access denied")


def ensure_company_admin_access(current_user, company_id: int | None) -> None:
    """Tenant isolation + admin role for company-scoped writes."""
    if current_user.role not in ("super_admin", "admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    ensure_company_access(current_user, company_id)


async def get_user_department_ids(
    db: AsyncSession,
    current_user,
    company_id: int | None = None,
) -> list[int]:
    if company_id is None:
        company_id = current_user.company_id
    if company_id is None:
        return []

    result = await db.execute(
        select(UserDepartmentAccess.department_id)
        .join(Department, Department.id == UserDepartmentAccess.department_id)
        .where(
            UserDepartmentAccess.user_id == current_user.id,
            Department.company_id == company_id,
            Department.is_active == True,
        )
    )
    department_ids = _unique_sorted_ints([row[0] for row in result.all()])
    if department_ids or getattr(current_user, "role", None) != "admin":
        return department_ids

    result = await db.execute(
        select(Department).where(
            Department.company_id == company_id,
            Department.slug == "general",
            Department.is_active == True,
        )
    )
    department = result.scalar_one_or_none()
    if not department:
        department = Department(
            company_id=company_id,
            name="General",
            slug="general",
            description="Default department",
            is_active=True,
        )
        db.add(department)
        await db.flush()

    db.add(
        UserDepartmentAccess(
            user_id=current_user.id,
            department_id=department.id,
            granted_by=current_user.id,
        )
    )
    await db.commit()
    return [department.id]


async def resolve_department_scope(
    db: AsyncSession,
    current_user,
    company_id: int | None,
    requested_department_ids: list[int] | None = None,
) -> list[int]:
    ensure_company_access(current_user, company_id)
    if company_id is None:
        return []

    if current_user.role == "super_admin":
        query = select(Department.id).where(Department.company_id == company_id, Department.is_active == True)
        if requested_department_ids:
            query = query.where(Department.id.in_(_unique_sorted_ints(requested_department_ids)))
        result = await db.execute(query)
        return _unique_sorted_ints([row[0] for row in result.all()])

    granted_department_ids = await get_user_department_ids(db, current_user, company_id)
    return filter_requested_department_ids(current_user, requested_department_ids, granted_department_ids)


async def ensure_department_access(
    db: AsyncSession,
    current_user,
    company_id: int | None,
    department_id: int | None,
) -> None:
    if department_id is None:
        raise HTTPException(status_code=400, detail="Department is required")
    allowed = await resolve_department_scope(db, current_user, company_id, [department_id])
    if department_id not in allowed:
        raise HTTPException(status_code=403, detail="Department access denied")


async def require_department_admin_access(
    company_id: int,
    department_id: int,
    current_user=Depends(require_knowledge_admin),
    db: AsyncSession = Depends(get_db),
):
    ensure_company_access(current_user, company_id)
    await ensure_department_access(db, current_user, company_id, department_id)
    return current_user
