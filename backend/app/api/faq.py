from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.dependencies import (
    require_knowledge_admin,
    ensure_company_access,
    ensure_department_access,
    resolve_department_scope,
)
from app.core.security import get_current_user
from app.schemas.faq import FAQCreate, FAQUpdate, FAQOut
from app.models.faq import FAQItem
from app.models.user import User
from app.services.audit_service import log_action

router = APIRouter(prefix="/faq", tags=["faq"])

@router.get("/{company_id}", response_model=list[FAQOut])
async def list_faq(company_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    ensure_company_access(current_user, company_id)
    department_ids = await resolve_department_scope(db, current_user, company_id)
    if not department_ids:
        return []
    query = select(FAQItem).where(FAQItem.company_id == company_id)
    query = query.where(FAQItem.department_id.in_(department_ids))
    if current_user.role not in ("super_admin", "admin"):
        query = query.where(FAQItem.is_published == True)
    query = query.order_by(FAQItem.sort_order, FAQItem.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())

@router.post("/{company_id}", response_model=FAQOut, status_code=201)
async def create_faq(company_id: int, data: FAQCreate, current_user: User = Depends(require_knowledge_admin), db: AsyncSession = Depends(get_db)):
    ensure_company_access(current_user, company_id)
    if data.department_id is None:
        raise HTTPException(status_code=400, detail="Department is required")
    await ensure_department_access(db, current_user, company_id, data.department_id)
    item = FAQItem(
        company_id=company_id,
        department_id=data.department_id,
        visibility=data.visibility,
        question=data.question,
        answer=data.answer,
        category=data.category,
        is_published=data.is_published,
        created_by=current_user.id,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    await log_action(db, action="create_faq", user_id=current_user.id, company_id=company_id, resource_type="faq", resource_id=item.id)
    return item

@router.patch("/{company_id}/{faq_id}", response_model=FAQOut)
async def update_faq(company_id: int, faq_id: int, data: FAQUpdate, current_user: User = Depends(require_knowledge_admin), db: AsyncSession = Depends(get_db)):
    ensure_company_access(current_user, company_id)
    result = await db.execute(select(FAQItem).where(FAQItem.id == faq_id, FAQItem.company_id == company_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="FAQ item not found")
    await ensure_department_access(db, current_user, company_id, item.department_id)
    updates = data.model_dump(exclude_unset=True)
    if "department_id" in updates and updates["department_id"] != item.department_id:
        await ensure_department_access(db, current_user, company_id, updates["department_id"])
    for key, value in updates.items():
        setattr(item, key, value)
    await db.commit()
    await db.refresh(item)
    return item

@router.delete("/{company_id}/{faq_id}", status_code=204)
async def delete_faq(company_id: int, faq_id: int, current_user: User = Depends(require_knowledge_admin), db: AsyncSession = Depends(get_db)):
    ensure_company_access(current_user, company_id)
    result = await db.execute(select(FAQItem).where(FAQItem.id == faq_id, FAQItem.company_id == company_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="FAQ item not found")
    await ensure_department_access(db, current_user, company_id, item.department_id)
    await db.delete(item)
    await db.commit()
