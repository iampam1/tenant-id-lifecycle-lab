from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from src.app.core import dependencies
from src.app.services import tenant_service
from src.app.schemas import tenant_schema
from src.app.models import user as user_model # Import user_model for current_user type hint

router = APIRouter()

@router.post(
    "/",
    response_model=tenant_schema.TenantRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tenant"
)
async def create_new_tenant(
    tenant_in: tenant_schema.TenantCreate,
    db: Session = Depends(dependencies.get_db),
    current_user: user_model.User = Depends(dependencies.get_current_user) # Protected
):
    """
    Create a new tenant. Requires authentication.
    - **name**: Each tenant must have a unique name.
    - **config_json**: Optional JSON blob for tenant-specific configurations.
    (Note: Currently, any authenticated user can create a tenant.
     Role-based access control for this can be added later, e.g. only super_admins)
    """
    db_tenant = tenant_service.get_tenant_by_name(db, name=tenant_in.name)
    if db_tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tenant with name '{tenant_in.name}' already exists."
        )
    created_tenant = tenant_service.create_tenant(db=db, tenant=tenant_in)
    return created_tenant

@router.get(
    "/",
    response_model=List[tenant_schema.TenantRead],
    summary="List all tenants"
)
async def list_all_tenants(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(dependencies.get_db),
    current_user: user_model.User = Depends(dependencies.get_current_user) # Protected
):
    """
    Retrieve a list of all tenants with pagination. Requires authentication.
    (Note: Currently lists all tenants. For tenant admins, this might be restricted
     to their own tenant or based on roles.)
    """
    tenants = tenant_service.get_tenants(db=db, skip=skip, limit=limit)
    return tenants

@router.get(
    "/{tenant_id}",
    response_model=tenant_schema.TenantRead,
    summary="Get a specific tenant by ID"
)
async def get_specific_tenant(
    tenant_id: int,
    db: Session = Depends(dependencies.get_db),
    current_user: user_model.User = Depends(dependencies.get_current_user) # Protected
):
    """
    Retrieve details for a specific tenant by its ID. Requires authentication.
    (Note: Access might be restricted based on user's tenant_id vs requested tenant_id,
     or by roles, e.g., tenant admin can only see their own tenant.)
    """
    db_tenant = tenant_service.get_tenant(db, tenant_id=tenant_id)
    if db_tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    # Example of basic tenant access control:
    # if current_user.tenant_id != tenant_id and not current_user.is_superuser: # Assuming is_superuser flag
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this tenant")
    return db_tenant

@router.put(
    "/{tenant_id}",
    response_model=tenant_schema.TenantRead,
    summary="Update a tenant"
)
async def update_existing_tenant(
    tenant_id: int,
    tenant_in: tenant_schema.TenantUpdate,
    db: Session = Depends(dependencies.get_db),
    current_user: user_model.User = Depends(dependencies.get_current_user) # Protected
):
    """
    Update an existing tenant's information. Requires authentication.
    Only provided fields will be updated.
    (Note: Access control similar to GET /{tenant_id} should apply)
    """
    db_tenant = tenant_service.get_tenant(db, tenant_id=tenant_id)
    if not db_tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    # Example access control
    # if current_user.tenant_id != tenant_id and not current_user.is_superuser:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this tenant")

    if tenant_in.name and tenant_in.name != db_tenant.name:
        existing_tenant_with_new_name = tenant_service.get_tenant_by_name(db, name=tenant_in.name)
        if existing_tenant_with_new_name and existing_tenant_with_new_name.id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tenant name '{tenant_in.name}' already in use by another tenant."
            )
    updated_tenant = tenant_service.update_tenant(db=db, tenant_id=tenant_id, tenant_update=tenant_in)
    return updated_tenant

@router.delete(
    "/{tenant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a tenant"
)
async def delete_existing_tenant(
    tenant_id: int,
    db: Session = Depends(dependencies.get_db),
    current_user: user_model.User = Depends(dependencies.get_current_user) # Protected
):
    """
    Delete a tenant. Requires authentication.
    (Conceptual: only deletes from app DB. IGA/PAM cleanup is later.)
    (Note: Access control similar to GET /{tenant_id} should apply)
    """
    db_tenant = tenant_service.get_tenant(db, tenant_id=tenant_id)
    if not db_tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    # Example access control
    # if current_user.tenant_id != tenant_id and not current_user.is_superuser:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this tenant")

    tenant_service.delete_tenant(db=db, tenant_id=tenant_id)
    return None
