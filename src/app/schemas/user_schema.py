from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# --- User Schemas ---

class UserBase(BaseModel):
    email: EmailStr = Field(..., example="admin@example.com")
    username: str = Field(..., min_length=3, max_length=50, example="john_doe")
    is_active: Optional[bool] = True
    # tenant_id will be set based on context (e.g. current authenticated admin's tenant)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, example="SecurePassword123")
    tenant_id: Optional[int] = None # For superadmin creating users in specific tenants
                                    # Or for associating user with current admin's tenant

class UserRegister(BaseModel): # For tenant admin self-registration
    email: EmailStr = Field(..., example="new_admin@example.com")
    username: str = Field(..., min_length=3, max_length=50, example="newtenantadmin")
    password: str = Field(..., min_length=8, example="StrongerPassword456")
    # Tenant name will be part of the registration request for the /auth/register endpoint
    # so the tenant can be created first, then this user associated.

class UserUpdate(BaseModel): # What can be updated?
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=8) # For password change
    is_active: Optional[bool] = None

class UserRead(UserBase):
    id: int
    tenant_id: int # Make tenant_id mandatory for UserRead
    created_at: datetime
    # Exclude hashed_password from response

    class Config:
        orm_mode = True
