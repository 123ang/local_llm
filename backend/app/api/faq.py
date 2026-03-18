from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.dependencies import require_admin
from app.core.security import get_current_user
from app.schemas.faq import FAQCreate, FAQUpdate, FAQOut
from app.models.faq import FAQItem
from app.models.user import User
from app.services.audit_service import log_action

router = APIRouter(prefix="/faq", tags=["faq"])

@router.get("/{company_id}", response_model=list[FAQOut])
async def list_faq(company_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    query = select(FAQItem).where(FAQItem.company_id == company_id)
    if current_user.role not in ("super_admin", "admin"):
        query = query.where(FAQItem.is_published == True)
    query = query.order_by(FAQItem.sort_order, FAQItem.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())

@router.post("/{company_id}", response_model=FAQOut, status_code=201)
async def create_faq(company_id: int, data: FAQCreate, current_user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    item = FAQItem(company_id=company_id, question=data.question, answer=data.answer, category=data.category, is_published=data.is_published, created_by=current_user.id)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    await log_action(db, action="create_faq", user_id=current_user.id, company_id=company_id, resource_type="faq", resource_id=item.id)
    return item

@router.patch("/{company_id}/{faq_id}", response_model=FAQOut)
async def update_faq(company_id: int, faq_id: int, data: FAQUpdate, current_user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FAQItem).where(FAQItem.id == faq_id, FAQItem.company_id == company_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="FAQ item not found")
    updates = data.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(item, key, value)
    await db.commit()
    await db.refresh(item)
    return item

@router.delete("/{company_id}/{faq_id}", status_code=204)
async def delete_faq(company_id: int, faq_id: int, current_user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FAQItem).where(FAQItem.id == faq_id, FAQItem.company_id == company_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="FAQ item not found")
    await db.delete(item)
    await db.commit()
