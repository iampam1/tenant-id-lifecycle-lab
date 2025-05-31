from sqlalchemy.orm import Session
from typing import Optional

from src.app.models import user as user_model
from src.app.models import tenant as tenant_model # Needed for tenant creation during registration
from src.app.schemas import user_schema
from src.app.schemas import tenant_schema # Needed for tenant creation
from src.app.core.security import get_password_hash, verify_password
from src.app.services import tenant_service # To create tenant during registration

def authenticate_user(db: Session, username_is_email: str, password: str) -> Optional[user_model.User]:
    """
    Authenticate a user by email and password.
    We are assuming the 'username' field provided for login is the user's email,
    as email is more likely to be globally unique for initial login.
    """
    user = db.query(user_model.User).filter(user_model.User.email == username_is_email).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def get_user_by_username(db: Session, username: str, tenant_id: Optional[int] = None) -> Optional[user_model.User]:
    """
    Get a user by username, optionally within a specific tenant.
    """
    query = db.query(user_model.User).filter(user_model.User.username == username)
    if tenant_id is not None:
        query = query.filter(user_model.User.tenant_id == tenant_id)
    return query.first()

def get_user_by_email(db: Session, email: str, tenant_id: Optional[int] = None) -> Optional[user_model.User]:
    """
    Get a user by email, optionally within a specific tenant.
    """
    query = db.query(user_model.User).filter(user_model.User.email == email)
    if tenant_id is not None:
        query = query.filter(user_model.User.tenant_id == tenant_id)
    return query.first()


def create_app_user(db: Session, user_in: user_schema.UserCreate) -> user_model.User:
    """
    Create a new application user (e.g., by an admin for a tenant).
    Ensures tenant_id is provided.
    """
    if user_in.tenant_id is None:
        raise ValueError("tenant_id must be provided to create an application user.")

    db_tenant = tenant_service.get_tenant(db, tenant_id=user_in.tenant_id)
    if not db_tenant:
        raise ValueError(f"Tenant with id {user_in.tenant_id} not found.")

    existing_user_email = get_user_by_email(db, email=user_in.email, tenant_id=user_in.tenant_id)
    if existing_user_email:
        raise ValueError(f"User with email {user_in.email} already exists in this tenant.")
    existing_user_username = get_user_by_username(db, username=user_in.username, tenant_id=user_in.tenant_id)
    if existing_user_username:
        raise ValueError(f"User with username {user_in.username} already exists in this tenant.")

    hashed_password = get_password_hash(user_in.password)
    db_user = user_model.User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=hashed_password,
        tenant_id=user_in.tenant_id,
        is_active=user_in.is_active if user_in.is_active is not None else True,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def register_tenant_admin_and_tenant(
    db: Session,
    user_reg_schema: user_schema.UserRegister,
    tenant_name: str # Tenant name provided during registration
) -> user_model.User:
    """
    Register a new tenant admin and create the tenant itself.
    This is typically for the first admin of a new tenant.
    """
    existing_tenant = tenant_service.get_tenant_by_name(db, name=tenant_name)
    if existing_tenant:
        raise ValueError(f"Tenant with name '{tenant_name}' already exists.")

    tenant_create_schema = tenant_schema.TenantCreate(name=tenant_name)
    try:
        new_tenant = tenant_service.create_tenant(db, tenant=tenant_create_schema)
    except Exception as e:
        db.rollback()
        raise ValueError(f"Could not create tenant: {e}")

    globally_existing_user_email = db.query(user_model.User).filter(user_model.User.email == user_reg_schema.email).first()
    if globally_existing_user_email:
        db.rollback()
        # Attempt to delete the tenant that was just created if user email is not unique globally
        # This is a basic cleanup. Consider more robust transaction patterns for production.
        try:
            tenant_to_delete_on_error = db.query(tenant_model.Tenant).filter(tenant_model.Tenant.id == new_tenant.id).first()
            if tenant_to_delete_on_error:
                db.delete(tenant_to_delete_on_error)
                db.commit() # Commit the deletion of the tenant
        except Exception as cleanup_exc:
            # Log this cleanup error, but the original error is more important to the user
            print(f"Critical: Failed to cleanup tenant '{new_tenant.name}' after user registration email conflict. Error: {cleanup_exc}") # Replace with proper logging
        raise ValueError(f"User with email {user_reg_schema.email} already exists in the system.")

    hashed_password = get_password_hash(user_reg_schema.password)
    db_user = user_model.User(
        email=user_reg_schema.email,
        username=user_reg_schema.username,
        hashed_password=hashed_password,
        tenant_id=new_tenant.id,
        is_active=True
    )

    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        # db.refresh(new_tenant) # new_tenant is already committed and its state is final here.
    except Exception as e:
        db.rollback()
        # Attempt to delete the tenant if user creation fails
        try:
            tenant_to_delete_on_error = db.query(tenant_model.Tenant).filter(tenant_model.Tenant.id == new_tenant.id).first()
            if tenant_to_delete_on_error:
                db.delete(tenant_to_delete_on_error)
                db.commit()
        except Exception as cleanup_exc:
            print(f"Critical: Failed to cleanup tenant '{new_tenant.name}' after user creation failure. Error: {cleanup_exc}") # Replace with proper logging
        raise ValueError(f"Could not create tenant admin user: {e}")

    return db_user
