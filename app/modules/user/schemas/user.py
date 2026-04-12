from pydantic import BaseModel, EmailStr, Field
from pydantic.functional_validators import BeforeValidator
from enum import Enum
from typing import Optional, Annotated
import datetime
import uuid


class Role(str, Enum):
    ADMIN = "admin"
    SME = "sme"
    USER = "user"


def _role_from_orm(v):
    if hasattr(v, "name"):
        return Role(v.name) if v.name else v
    return v


class UserBase(BaseModel):
    name: str
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(min_length=8)

    class Config:
        from_attributes = True


class UserSchema(UserBase):
    id: uuid.UUID

    class Config:
        from_attributes = True


class UserOut(UserBase):
    id: uuid.UUID
    name: str
    email: EmailStr
    is_active: bool
    is_verified: bool
    role: Annotated[Role, BeforeValidator(_role_from_orm)]
    last_login_at: Optional[datetime.datetime] = None
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True


class UpdateProfile(BaseModel):
    name: Optional[str] = None
    old_password: Optional[str] = None
    password: Optional[str] = None


class UpdateUser(BaseModel):
    name: Optional[str] = None
    role: Optional[Role] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
