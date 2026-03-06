import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr

from app.enums.role import UserRole


class UserBase(BaseModel):
    email: EmailStr
    role: UserRole = UserRole.OPERATOR
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[UserRole] = None
