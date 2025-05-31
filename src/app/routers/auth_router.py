from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm # For login form
from sqlalchemy.orm import Session
from typing import Any

from src.app.core import dependencies, security
from src.app.services import auth_service
from src.app.schemas import user_schema, token_schema, tenant_schema # Added tenant_schema for registration
from src.app.core.config import settings # For token expiry if not using default from security
from pydantic import Field # For TenantAdminRegisterRequest

router = APIRouter()

@router.post("/login", response_model=token_schema.Token)
async def login_for_access_token(
    db: Session = Depends(dependencies.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    Username field in the form is treated as email.
    """
    # For login, form_data.username is expected to be the user's email
    user = auth_service.authenticate_user(
        db, username_is_email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, # Or 403 Forbidden
            detail="Inactive user",
        )

    access_token = security.create_access_token(
        subject=user.email # Using email as subject for the token
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }

# This schema is for the /register endpoint payload
class TenantAdminRegisterRequest(user_schema.UserRegister):
    tenant_name: str = Field(..., min_length=3, max_length=100, example="New Tenant Inc")


@router.post("/register", response_model=user_schema.UserRead, status_code=status.HTTP_201_CREATED)
async def register_new_tenant_admin(
    registration_data: TenantAdminRegisterRequest,
    db: Session = Depends(dependencies.get_db)
):
    """
    Register a new tenant and its first administrator.
    """
    try:
        # Extract user registration part and tenant name
        user_reg_schema = user_schema.UserRegister(
            email=registration_data.email,
            username=registration_data.username,
            password=registration_data.password
        )
        tenant_name = registration_data.tenant_name

        created_admin_user = auth_service.register_tenant_admin_and_tenant(
            db=db,
            user_reg_schema=user_reg_schema,
            tenant_name=tenant_name
        )
        # TODO: Assign a "tenant_admin" role to this user.
        # This would involve:
        # 1. Getting or creating the "tenant_admin" role for the new_tenant.id.
        # 2. Associating this role with created_admin_user via the user_roles table.
        # For now, returning the user. Role assignment is a later step.

        return created_admin_user
    except ValueError as e:
        # Catch business logic errors from the service layer
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        # Catch any other unexpected errors
        # Log this error properly in a real application
        print(f"Unexpected error during registration: {e}") # Replace with proper logging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during registration.",
        )

# Remove the old test endpoint
# @router.get("/auth/test") ...
