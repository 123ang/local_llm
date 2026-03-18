from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.audit import AuditLog

async def log_action(db: AsyncSession, action: str, user_id: int | None = None, company_id: int | None = None,
                     resource_type: str | None = None, resource_id: int | None = None,
                     details: dict | None = None, ip_address: str | None = None):
    entry = AuditLog(
        action=action, user_id=user_id, company_id=company_id,
        resource_type=resource_type, resource_id=resource_id,
        details=details, ip_address=ip_address,
    )
    db.add(entry)
    await db.commit()

async def get_audit_logs(db: AsyncSession, company_id: int | None = None, limit: int = 100, offset: int = 0) -> list:
    query = select(AuditLog)
    if company_id:
        query = query.where(AuditLog.company_id == company_id)
    query = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())
