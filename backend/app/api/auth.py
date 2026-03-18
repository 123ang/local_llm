from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.auth import LoginRequest, TokenResponse, UserBrief
from app.services.auth_service import authenticate_user, create_token_for_user
from app.services.audit_service import log_action
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=TokenResponse)
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, form.username, form.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token_data = await create_token_for_user(user)
    await log_action(db, action="login", user_id=user.id, company_id=user.company_id)
    company_name = None
    if user.company:
        company_name = user.company.name
    return TokenResponse(
        access_token=token_data["access_token"],
        user=UserBrief(
            id=user.id, email=user.email, full_name=user.full_name,
            role=user.role, company_id=user.company_id, company_name=company_name,
        )
    )

@router.get("/me", response_model=UserBrief)
async def get_me(current_user: User = Depends(get_current_user)):
    company_name = None
    if current_user.company:
        company_name = current_user.company.name
    return UserBrief(
        id=current_user.id, email=current_user.email, full_name=current_user.full_name,
        role=current_user.role, company_id=current_user.company_id, company_name=company_name,
    )
