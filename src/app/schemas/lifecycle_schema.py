from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any, List # Added List
from datetime import datetime # Added datetime

class UserOnboardRequest(BaseModel):
    username: str = Field(..., example="newigauser")
    email: EmailStr = Field(..., example="newigauser@example.com")
    first_name: Optional[str] = Field(None, example="New")
    last_name: Optional[str] = Field(None, example="User")
    password: str = Field(..., example="StrongPassword123!") # Initial password for IGA system
    tenant_id: int # App's internal tenant_id to find IGA context (e.g., org_oid)
    iga_role: Optional[str] = Field(None, example="standard_user") # Conceptual role name in IGA
    # Additional attributes for IGA can be added here
    extra_iga_attributes: Optional[Dict[str, Any]] = None

class UserOnboardResponse(BaseModel):
    message: str
    app_user_id: Optional[int] = None # ID of the user in our app's DB, if created/linked
    iga_user_id: Optional[str] = None # ID of the user in the IGA system (e.g., OID)
    status: str # e.g., "success", "failed"

class PrivilegeSessionRequest(BaseModel):
    # app_username: str = Field(..., example="app_user_for_pam") # Username known to our app
    # Instead of app_username, let's use the user_id from the authenticated user for clarity
    # The mapping to PAM username can happen in the service/router if needed.
    # tenant_id: int # App's internal tenant_id, can be derived from current_user
    target_asset_identifier: str = Field(..., example="prod-server-01_or_asset_id_from_pam") # Name or ID of the asset in PAM
    pam_username: Optional[str] = Field(None, example="pam_system_user") # Optional: specific username in PAM if different from app user's mapping

class PrivilegeSessionResponse(BaseModel):
    message: str
    session_url: Optional[str] = None
    status: str # e.g., "success", "failed"
    error_detail: Optional[str] = None

class UserOffboardRequest(BaseModel):
    app_username: str = Field(..., example="user_to_offboard") # Username in our application
    tenant_id: int # App's internal tenant_id where this user resides
    # Options for offboarding depth could be added, e.g.,
    # "deprovision_from_iga": bool = True
    # "deprovision_from_pam": bool = True
    # "deactivate_local_account": bool = True

class UserOffboardResponse(BaseModel):
    message: str
    app_username: str
    iga_status: str # e.g., "deprovisioned", "not_found", "failed", "skipped"
    pam_status: str # e.g., "deprovisioned", "not_found", "failed", "skipped"
    local_app_status: str # e.g., "deactivated", "deleted", "not_found", "failed"

class AccessReviewUser(BaseModel):
    iga_user_identifier: str # e.g., username from IGA, or OID
    app_username: Optional[str] = None # If linked to a local app user
    roles: List[str] # List of role names or identifiers from IGA

class AccessReviewResponse(BaseModel):
    tenant_id: int
    tenant_name: str
    users_and_roles: List[AccessReviewUser]
    review_timestamp: datetime
    message: Optional[str] = "Data retrieved for manual review."
