from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime

# --- Tenant Schemas ---

# Base properties shared by other schemas
class TenantBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100, example="AcmeCorp")
    config_json: Optional[dict[str, Any]] = Field(None, example={"iga_sync_enabled": True, "pam_tier": "premium"})

# Properties to receive on tenant creation
class TenantCreate(TenantBase):
    # For now, config_json might not be set at creation by user directly,
    # or could be optional with defaults.
    # Let's make it optional for the creation schema for simplicity.
    config_json: Optional[dict[str, Any]] = None
    pass

# Properties to receive on tenant update (if needed)
class TenantUpdate(TenantBase):
    name: Optional[str] = Field(None, min_length=3, max_length=100, example="AcmeCorp Inc.")
    config_json: Optional[dict[str, Any]] = None


# Properties to return to client (includes read-only fields like id, created_at)
class TenantRead(TenantBase):
    id: int
    created_at: datetime
    name: str # Overriding to ensure it's not Optional from a merged model
    config_json: Optional[dict[str, Any]] # Ensure it's also here

    class Config:
        orm_mode = True # Enables Pydantic to read data from ORM models
