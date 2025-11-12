from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# ========== EXISTING ITEM SCHEMAS ========== #
class ItemBase(BaseModel):
    title: str
    description: Optional[str] = None


class ItemCreate(ItemBase):
    pass


class Item(ItemBase):
    id: int

    class Config:
        orm_mode = True


# ========== AUTH SCHEMAS ========== #
class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str  
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_num: Optional[str] = None
    activated: bool
    is_authenticated: bool
    created_at: datetime

    class Config:
        orm_mode = True


# ========== ACCOUNT SCHEMAS ========== #
class AccountCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_num: Optional[str] = None

