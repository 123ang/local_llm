from fastapi import Depends
from app.core.security import get_current_user


def require_admin(current_user=Depends(get_current_user)):
    if current_user.role not in ("super_admin", "admin"):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def require_super_admin(current_user=Depends(get_current_user)):
    if current_user.role != "super_admin":
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Super admin access required")
    return current_user
