from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserBrief"


class UserBrief(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    company_id: int | None = None
    company_name: str | None = None
    department_ids: list[int] = []
    departments: list[dict] = []

    model_config = {"from_attributes": True}
