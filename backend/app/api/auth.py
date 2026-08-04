from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.auth import LoginRequest, TokenResponse, UserBrief
from app.services.auth_service import authenticate_user, create_token_for_user
from app.services.audit_service import log_action
from app.core.security import get_current_user
from app.core.rate_limit import login_rate_limiter, login_rate_limit_key
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


def _brief_departments(user: User) -> tuple[list[int], list[dict]]:
    departments = []
    for access in user.department_access or []:
        dept = access.department
        if dept and dept.is_active:
            departments.append({"id": dept.id, "company_id": dept.company_id, "name": dept.name, "slug": dept.slug})
    departments.sort(key=lambda item: item["name"])
    return [dept["id"] for dept in departments], departments

@router.post("/login", response_model=TokenResponse)
async def login(request: Request, form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    rate_key = login_rate_limit_key(request, form.username)
    retry_after = login_rate_limiter.retry_after(rate_key)
    if retry_after:
        raise HTTPException(
            status_code=429,
            detail="Too many login attempts. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )

    user = await authenticate_user(db, form.username, form.password)
    if not user:
        login_rate_limiter.record_failure(rate_key)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    login_rate_limiter.record_success(rate_key)
    token_data = await create_token_for_user(user)
    await log_action(db, action="login", user_id=user.id, company_id=user.company_id)
    company_name = None
    if user.company:
        company_name = user.company.name
    department_ids, departments = _brief_departments(user)
    return TokenResponse(
        access_token=token_data["access_token"],
        user=UserBrief(
            id=user.id, email=user.email, full_name=user.full_name,
            role=user.role, company_id=user.company_id, company_name=company_name,
            department_ids=department_ids, departments=departments,
        )
    )

@router.get("/me", response_model=UserBrief)
async def get_me(current_user: User = Depends(get_current_user)):
    company_name = None
    if current_user.company:
        company_name = current_user.company.name
    department_ids, departments = _brief_departments(current_user)
    return UserBrief(
        id=current_user.id, email=current_user.email, full_name=current_user.full_name,
        role=current_user.role, company_id=current_user.company_id, company_name=company_name,
        department_ids=department_ids, departments=departments,
    )
