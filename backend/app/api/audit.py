from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import require_admin
from app.schemas.audit import AuditLogOut
from app.services.audit_service import get_audit_logs
from app.models.user import User

router = APIRouter(prefix="/audit", tags=["audit"])

@router.get("", response_model=list[AuditLogOut])
async def list_audit_logs(
    company_id: int | None = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != "super_admin":
        company_id = current_user.company_id
    return await get_audit_logs(db, company_id=company_id, limit=limit, offset=offset)
