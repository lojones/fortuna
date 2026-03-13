from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserInDB(UserBase):
    id: str
    role: Literal["admin", "user"]
    status: Literal["pending", "active", "suspended"]
    created_at: datetime
    updated_at: datetime
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None


class UserPublic(BaseModel):
    id: str
    username: str
    email: str
    role: str
    status: str
    created_at: datetime


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class RegisterResponse(BaseModel):
    message: str
    user: UserPublic


class AdminUserUpdate(BaseModel):
    status: Optional[Literal["active", "suspended"]] = None
    role: Optional[Literal["admin", "user"]] = None


class RoleUpdate(BaseModel):
    role: Literal["admin", "user"]
