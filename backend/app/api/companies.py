from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import require_super_admin
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyOut
from app.services.company_service import create_company, get_companies, get_company, update_company
from app.services.audit_service import log_action
from app.models.user import User

router = APIRouter(prefix="/companies", tags=["companies"])

@router.get("", response_model=list[CompanyOut])
async def list_companies(current_user: User = Depends(require_super_admin), db: AsyncSession = Depends(get_db)):
    return await get_companies(db, include_inactive=True)

@router.post("", response_model=CompanyOut, status_code=201)
async def create_new_company(data: CompanyCreate, current_user: User = Depends(require_super_admin), db: AsyncSession = Depends(get_db)):
    company = await create_company(db, name=data.name, description=data.description)
    await log_action(db, action="create_company", user_id=current_user.id, resource_type="company", resource_id=company.id)
    return company

@router.get("/{company_id}", response_model=CompanyOut)
async def get_single_company(company_id: int, current_user: User = Depends(require_super_admin), db: AsyncSession = Depends(get_db)):
    company = await get_company(db, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

@router.patch("/{company_id}", response_model=CompanyOut)
async def update_existing_company(company_id: int, data: CompanyUpdate, current_user: User = Depends(require_super_admin), db: AsyncSession = Depends(get_db)):
    updates = data.model_dump(exclude_unset=True)
    company = await update_company(db, company_id, **updates)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    await log_action(db, action="update_company", user_id=current_user.id, resource_type="company", resource_id=company.id, details=updates)
    return company
