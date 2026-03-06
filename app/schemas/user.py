import uuid
from pydantic import BaseModel, EmailStr
from app.models.user import UserRole
from typing import Optional


class UserBase(BaseModel):
    email: EmailStr
    role: UserRole = UserRole.Operator
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: uuid.UUID

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[UserRole] = None
