from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any # Added Dict, Any
import json # For handling config_json

from src.app.models import tenant as tenant_model
from src.app.schemas import tenant_schema
from src.app.services.iga_client import IgaClient # Import IgaClient
from src.app.core.config import settings # To check if IGA integration is enabled

def create_tenant(db: Session, tenant: tenant_schema.TenantCreate) -> tenant_model.Tenant:
    """
    Create a new tenant in the database and provision it in the IGA system.
    """
    # First, create in local DB to get an ID, but don't commit yet if IGA call is critical path
    # Or, commit first and handle IGA failure by marking tenant as 'provisioning_failed' or trying to delete

    # For simplicity, let's create in local DB first and commit.
    # If IGA fails, we'll update the tenant's config_json with an error or mark it.

    db_tenant = tenant_model.Tenant(
        name=tenant.name,
        config_json=tenant.config_json if tenant.config_json else {} # Ensure config_json is at least an empty dict
    )
    db.add(db_tenant)
    db.commit()
    db.refresh(db_tenant)

    iga_provisioned_successfully = False
    iga_error_message = None
    iga_org_details: Optional[Dict[str, Any]] = None

    # Only attempt IGA provisioning if IGA_API_URL is configured
    if settings.IGA_API_URL and settings.IGA_API_KEY:
        try:
            iga_client = IgaClient() # Uses settings from environment
            # Conceptual: Use tenant name as org name. Details could be passed or default.
            print(f"Attempting to provision tenant '{db_tenant.name}' in IGA system...") # Replace with logging

            # The create_organization method is conceptual.
            # It might need more specific details based on the IGA tool.
            # For midPoint, org_details might include parent OID if not top-level.
            # For Syncope, this would be `create_domain(domain_name=db_tenant.name)`
            # Let's assume create_organization handles this abstraction for now.
            iga_org_response = iga_client.create_organization(org_name=db_tenant.name)

            print(f"IGA provisioning response for '{db_tenant.name}': {iga_org_response}") # Replace with logging

            # Store IGA-specific info if available (e.g., org OID from midPoint)
            # This depends on the actual response structure of iga_client.create_organization
            if isinstance(iga_org_response, dict) and iga_org_response.get("oid"): # Example for midPoint OID
                iga_org_details = {"iga_org_oid": iga_org_response.get("oid")}
            elif isinstance(iga_org_response, dict) and iga_org_response.get("key"): # Example for Syncope key
                iga_org_details = {"iga_domain_key": iga_org_response.get("key")}
            else:
                iga_org_details = {"iga_provisioning_status": "success_no_id_returned"}

            db_tenant.config_json.update({ # type: ignore # Pylance might complain about dict|None
                "iga_provisioning": "success",
                ** (iga_org_details if iga_org_details else {})
            })
            iga_provisioned_successfully = True

        except Exception as e:
            print(f"Error provisioning tenant '{db_tenant.name}' in IGA: {e}") # Replace with proper logging
            iga_error_message = str(e)
            db_tenant.config_json.update({ # type: ignore
                "iga_provisioning": "failed",
                "iga_error": iga_error_message
            })
    else:
        print(f"IGA settings not configured. Skipping IGA provisioning for tenant '{db_tenant.name}'.") # Replace with logging
        db_tenant.config_json.update({"iga_provisioning": "skipped_due_to_config"}) # type: ignore

    # Commit changes to config_json (status of IGA provisioning)
    db.commit()
    db.refresh(db_tenant)

    # Optional: If IGA provisioning failed critically, you might choose to delete the local tenant record
    # or implement a retry mechanism. For now, we just mark it.
    # if not iga_provisioned_successfully and settings.IGA_API_URL:
    #     # This is a design decision. Deleting local record if IGA fails.
    #     # db.delete(db_tenant)
    #     # db.commit()
    #     # raise Exception(f"Failed to provision tenant in IGA: {iga_error_message}") # Or a custom exception
    #     pass


    return db_tenant

def get_tenant(db: Session, tenant_id: int) -> Optional[tenant_model.Tenant]:
    """
    Get a single tenant by ID.
    """
    return db.query(tenant_model.Tenant).filter(tenant_model.Tenant.id == tenant_id).first()

def get_tenant_by_name(db: Session, name: str) -> Optional[tenant_model.Tenant]:
    """
    Get a single tenant by name.
    """
    return db.query(tenant_model.Tenant).filter(tenant_model.Tenant.name == name).first()

def get_tenants(db: Session, skip: int = 0, limit: int = 100) -> List[tenant_model.Tenant]:
    """
    Get a list of tenants with pagination.
    """
    return db.query(tenant_model.Tenant).offset(skip).limit(limit).all()

def update_tenant(
    db: Session, tenant_id: int, tenant_update: tenant_schema.TenantUpdate
) -> Optional[tenant_model.Tenant]:
    """
    Update an existing tenant.
    (IGA update logic for tenant name change, etc., is not covered here yet)
    """
    db_tenant = get_tenant(db, tenant_id)
    if not db_tenant:
        return None

    update_data = tenant_update.dict(exclude_unset=True)

    # If name is being updated, conceptual IGA update might be needed
    # old_name = db_tenant.name
    # new_name = update_data.get("name")
    # if new_name and new_name != old_name and settings.IGA_API_URL:
    #     iga_client = IgaClient()
    #     # iga_client.update_organization(db_tenant.config_json.get("iga_org_oid"), {"name": new_name})
    #     print(f"CONCEPTUAL: Update org name in IGA for tenant {tenant_id} from {old_name} to {new_name}")


    for key, value in update_data.items():
        setattr(db_tenant, key, value)

    db.add(db_tenant)
    db.commit()
    db.refresh(db_tenant)
    return db_tenant

def delete_tenant(db: Session, tenant_id: int) -> Optional[Dict[str, Any]]: # Return type changed
    """
    Delete a tenant from the app's DB and de-provision from the IGA system.
    Returns a dictionary of the deleted tenant's info if successful, else None.
    """
    db_tenant = get_tenant(db, tenant_id)
    if not db_tenant:
        return None

    tenant_name_for_logging = db_tenant.name # Get name before it's potentially invalidated
    iga_org_identifier = None
    if db_tenant.config_json:
        iga_org_identifier = db_tenant.config_json.get("iga_org_oid") or db_tenant.config_json.get("iga_domain_key")


    if settings.IGA_API_URL and settings.IGA_API_KEY and iga_org_identifier:
        try:
            iga_client = IgaClient()
            print(f"Attempting to de-provision tenant '{tenant_name_for_logging}' (IGA ID: {iga_org_identifier}) from IGA system...") # Replace with logging

            # iga_client.delete_organization expects the IGA-specific identifier (OID or key)
            iga_client.delete_organization(org_identifier=str(iga_org_identifier)) # Ensure it's string
            print(f"IGA de-provisioning for tenant '{tenant_name_for_logging}' successful.") # Replace with logging
        except Exception as e:
            # Log the error, but proceed with local deletion.
            # Or, make this a hard failure if IGA de-provisioning is critical.
            print(f"Error de-provisioning tenant '{tenant_name_for_logging}' from IGA: {e}. Proceeding with local deletion.") # Replace with logging
            # Optionally, update tenant status instead of allowing local delete if IGA fails
            # db_tenant.config_json["iga_deprovisioning_error"] = str(e)
            # db.commit()
            # raise Exception(f"Failed to deprovision tenant from IGA: {e}") # Or a custom exception
            pass # Current: log and proceed with local delete
    elif settings.IGA_API_URL and settings.IGA_API_KEY and not iga_org_identifier:
        print(f"No IGA identifier found for tenant '{tenant_name_for_logging}'. Skipping IGA de-provisioning.")
    else:
        print(f"IGA settings not configured or no IGA identifier. Skipping IGA de-provisioning for tenant '{tenant_name_for_logging}'.")


    deleted_tenant_info = {"id": db_tenant.id, "name": db_tenant.name, "config_json": db_tenant.config_json}
    db.delete(db_tenant)
    db.commit()

    return deleted_tenant_info
