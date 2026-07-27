from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
import re


class UserRole:
    ADMIN  = "admin"
    SELLER = "seller"
    BUYER  = "buyer"
    ALL    = ["admin", "seller", "buyer"]


class UserBase(BaseModel):
    username: str
    email: EmailStr
    phone: str
    role: str = "buyer"

    @field_validator("username")
    @classmethod
    def username_valid(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3 or len(v) > 50:
            raise ValueError("Username must be between 3 and 50 characters")
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("Username can only contain letters, numbers, and underscores")
        return v

    @field_validator("phone")
    @classmethod
    def phone_valid(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r"^(05|06|07)[0-9]{8}$", v):
            raise ValueError("Phone number must be exactly 10 digits and start with 05, 06, or 07")
        return v

    @field_validator("role")
    @classmethod
    def role_valid(cls, v: str) -> str:
        if v not in ["admin", "seller", "buyer"]:
            raise ValueError("Role must be admin, seller, or buyer")
        return v


class UserCreate(UserBase):
    password: str

    @field_validator("password")
    @classmethod
    def password_strong(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_strong(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class UserResponse(UserBase):
    id: int
    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
