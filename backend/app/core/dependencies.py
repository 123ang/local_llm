from fastapi import Depends, HTTPException
from app.core.security import get_current_user


def require_admin(current_user=Depends(get_current_user)):
    if current_user.role not in ("super_admin", "admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def require_super_admin(current_user=Depends(get_current_user)):
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin access required")
    return current_user


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
