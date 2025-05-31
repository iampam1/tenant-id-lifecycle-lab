from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List # For future list users endpoint

from src.app.core import dependencies
from src.app.services import auth_service # Renamed from user_service to auth_service for user creation
from src.app.schemas import user_schema
from src.app.models import user as user_model

router = APIRouter()

@router.post(
    "/", # Assuming prefix /users is set in main.py
    response_model=user_schema.UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user within a tenant"
)
async def create_new_app_user(
    user_in: user_schema.UserCreate, # UserCreate schema expects tenant_id optionally
    db: Session = Depends(dependencies.get_db),
    current_user: user_model.User = Depends(dependencies.get_current_user)
):
    """
    Create a new user. This endpoint is intended for tenant administrators
    to create users within their own tenant, or for a super_admin to create
    users in any tenant.

    - **tenant_id** in `user_in`:
        - If the `current_user` is a tenant admin (not super_admin), this `tenant_id`
          *must* match `current_user.tenant_id`.
        - If `current_user` is a super_admin, they can specify any `tenant_id`.
        - If `tenant_id` is not provided in `user_in`, it defaults to `current_user.tenant_id`.
    """

    # Determine the target tenant_id
    target_tenant_id: int
    if user_in.tenant_id is not None:
        # If tenant_id is provided in the payload
        # A super_admin could specify any tenant_id.
        # A tenant_admin should only be able to specify their own tenant_id.
        # TODO: Implement role check for super_admin vs tenant_admin
        # For now, let's assume if current_user.is_superuser exists, they can do this.
        # if hasattr(current_user, 'is_superuser') and current_user.is_superuser:
        #     target_tenant_id = user_in.tenant_id
        # Elif current_user.tenant_id == user_in.tenant_id:
        #     target_tenant_id = user_in.tenant_id
        # else:
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="Not authorized to create users for the specified tenant_id."
        #     )
        # Simplified logic for now: if user_in.tenant_id is set, use it.
        # Security check: ensure current_user can act on target_tenant_id.
        # For a tenant admin, target_tenant_id MUST be current_user.tenant_id
        if current_user.tenant_id != user_in.tenant_id: # Basic check
             # This should be refined with role checks (e.g. superadmin can override)
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only create users for your own tenant."
            )
        target_tenant_id = user_in.tenant_id
    else:
        # If tenant_id is not in payload, default to current_user's tenant_id
        target_tenant_id = current_user.tenant_id

    # Ensure the UserCreate schema used by the service has the correct tenant_id
    final_user_in = user_schema.UserCreate(
        email=user_in.email,
        username=user_in.username,
        password=user_in.password,
        is_active=user_in.is_active,
        tenant_id=target_tenant_id # Set the determined target_tenant_id
    )

    try:
        created_user = auth_service.create_app_user(db=db, user_in=final_user_in)
        # TODO: Assign default roles to the new user if necessary
        return created_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        # Log this error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the user.",
        )

# Remove the old test endpoint
# @router.get("/users/test") ...

# Future endpoints for user management (GET /users/, GET /users/{id}, PUT, DELETE)
# would also be protected and potentially have role-based access control.

@router.get("/me", response_model=user_schema.UserRead, summary="Get current authenticated user details")
async def read_users_me(
    current_user: user_model.User = Depends(dependencies.get_current_user)
):
    """
    Fetch details for the currently authenticated user.
    """
    return current_user

@router.get(
    "/", # Mounted under /api/v1/users
    response_model=List[user_schema.UserRead],
    summary="List users within the current authenticated user's tenant"
)
async def list_users_in_tenant(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(dependencies.get_db),
    current_user: user_model.User = Depends(dependencies.get_current_user)
):
    """
    Retrieve all users belonging to the current authenticated user's tenant.
    Supports pagination.
    """
    # This service function doesn't exist yet. We need to create it.
    # For now, query directly.
    # users = auth_service.get_users_by_tenant(db, tenant_id=current_user.tenant_id, skip=skip, limit=limit)

    users = db.query(user_model.User)                  .filter(user_model.User.tenant_id == current_user.tenant_id)                  .offset(skip)                  .limit(limit)                  .all()
    return users
