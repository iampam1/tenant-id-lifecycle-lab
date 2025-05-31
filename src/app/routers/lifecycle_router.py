from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any

from src.app.core import dependencies
from src.app.services import tenant_service, auth_service, iga_client as iga_client_service # Renamed for clarity
from src.app.schemas import lifecycle_schema, user_schema # Added user_schema
from src.app.models import user as user_model
from src.app.core.config import settings
from src.app.services import pam_client as pam_client_service # Added
from src.app.models import audit_log as audit_log_model # For AuditLog
from datetime import datetime # For AuditLog timestamp


router = APIRouter()

@router.post(
    "/onboard",
    response_model=lifecycle_schema.UserOnboardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Onboard a new user into the IGA system and optionally the local app"
)
async def onboard_new_user(
    onboard_request: lifecycle_schema.UserOnboardRequest,
    db: Session = Depends(dependencies.get_db),
    current_user: user_model.User = Depends(dependencies.get_current_user) # Authenticated user performing action
):
    """
    Onboard a new user:
    1. Verifies the calling user's tenant and permissions (conceptual for now).
    2. Retrieves IGA context (e.g., org_oid) for the specified tenant_id.
    3. Creates the user in the IGA system.
    4. (Optional/Conceptual) Creates a corresponding user in the local application database or links if exists.
    5. (Conceptual) Assigns a specified role in IGA.
    """

    # 1. Authorization Check (Simplified)
    # Ensure current_user belongs to the tenant_id they are trying to onboard for,
    # or is a super_admin.
    if current_user.tenant_id != onboard_request.tenant_id:
        # TODO: Add super_admin role check here to allow overriding
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to onboard users for this tenant."
        )

    # 2. Retrieve IGA context for the tenant
    db_tenant = tenant_service.get_tenant(db, tenant_id=onboard_request.tenant_id)
    if not db_tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant with ID {onboard_request.tenant_id} not found."
        )

    iga_org_identifier = None
    if db_tenant.config_json:
        iga_org_identifier = db_tenant.config_json.get("iga_org_oid") or db_tenant.config_json.get("iga_domain_key")

    if not (settings.IGA_API_URL and settings.IGA_API_KEY and iga_org_identifier):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"IGA system not configured or IGA identifier missing for tenant {db_tenant.name}."
        )

    # 3. Create user in IGA
    iga_client = iga_client_service.IgaClient()

    # Construct user_data payload for IGA. This is highly IGA-specific.
    # Example for midPoint (conceptual - needs actual attribute names from midPoint schema):
    iga_user_payload = {
        "name": onboard_request.username, # midPoint's 'name' is often the username/login
        "givenName": onboard_request.first_name,
        "familyName": onboard_request.last_name,
        "emailAddress": onboard_request.email,
        "credentials": { # This structure is very midPoint specific for password
            "password": {
                "value": onboard_request.password
            }
        },
        "parentOrgRef": [{"oid": iga_org_identifier, "type": "OrgType"}] # Link to tenant's org in midPoint
        # Add other attributes from onboard_request.extra_iga_attributes if provided
    }
    if onboard_request.extra_iga_attributes:
        iga_user_payload.update(onboard_request.extra_iga_attributes)

    try:
        print(f"Attempting to create user '{onboard_request.username}' in IGA for tenant '{db_tenant.name}' (IGA ID: {iga_org_identifier})") # Logging
        created_iga_user = iga_client.create_user(
            user_data=iga_user_payload,
            tenant_context=str(iga_org_identifier) # Pass as string, IgaClient might use it differently
        )
        iga_user_id_from_response = created_iga_user.get("oid") # Example for midPoint OID
        if not iga_user_id_from_response and created_iga_user.get("key"): # Example for Syncope key
             iga_user_id_from_response = created_iga_user.get("key")

        print(f"IGA user creation response: {created_iga_user}") # Logging
    except Exception as e:
        # Log detailed error e
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, # Error communicating with IGA
            detail=f"Failed to create user in IGA system: {e}"
        )

    # 4. (Optional) Create or link user in local app DB
    app_user_id: Optional[int] = None
    # Check if user already exists in local DB by email within this tenant
    local_user = auth_service.get_user_by_email(db, email=onboard_request.email, tenant_id=db_tenant.id)
    if local_user:
        app_user_id = local_user.id
        # TODO: Potentially update local user with IGA ID or sync status
        print(f"User {onboard_request.email} already exists in local DB for tenant {db_tenant.id}. Linking IGA ID.")
    else:
        # Create a corresponding local user (e.g. if they don't self-register to the app)
        # This local user might have a different password or no password if IGA is master
        try:
            # For local app user, we might not want to store the IGA password,
            # or store a placeholder/ unusable hash if auth is delegated to IGA.
            # Here, we create with the same password for simplicity of example.
            # In a real scenario, this local user might be for app-level roles, not direct login.
            user_to_create_locally = user_schema.UserCreate(
                email=onboard_request.email,
                username=onboard_request.username, # Ensure this username is unique within tenant if different from email
                password=onboard_request.password, # Or a generated complex password
                tenant_id=db_tenant.id,
                is_active=True # Or based on IGA status
            )
            # Check for username conflict before creating
            if auth_service.get_user_by_username(db, username=user_to_create_locally.username, tenant_id=db_tenant.id):
                print(f"Warning: Username '{user_to_create_locally.username}' already exists for tenant {db_tenant.id}, user not created locally with this username.")
            else:
                new_local_user = auth_service.create_app_user(db, user_in=user_to_create_locally)
                app_user_id = new_local_user.id
                print(f"Created corresponding local user with ID: {app_user_id}")
        except ValueError as ve: # Catch duplicate email/username from create_app_user
             print(f"Skipping local user creation due to conflict or error: {ve}")


    # 5. (Conceptual) Assign role in IGA
    if onboard_request.iga_role and iga_user_id_from_response:
        try:
            # The role_identifier for assign_role_to_user needs to be the IGA system's ID for that role.
            # This might require looking up role "standard_user" in IGA to get its OID/key.
            # For now, assuming onboard_request.iga_role is the direct identifier.
            print(f"Attempting to assign role '{onboard_request.iga_role}' to IGA user '{iga_user_id_from_response}'") # Logging
            role_assigned = iga_client.assign_role_to_user(
                user_identifier=str(iga_user_id_from_response),
                role_identifier=onboard_request.iga_role,
                tenant_context=str(iga_org_identifier)
            )
            if not role_assigned:
                print(f"Warning: Failed to assign role '{onboard_request.iga_role}' in IGA.") # Logging
        except Exception as e:
            print(f"Error assigning role in IGA: {e}") # Logging, but don't fail the whole onboarding for this conceptual step

    return lifecycle_schema.UserOnboardResponse(
        message="User onboarding process initiated successfully.",
        app_user_id=app_user_id,
        iga_user_id=str(iga_user_id_from_response) if iga_user_id_from_response else None,
        status="success"
    )

# Remove the old test endpoint
# @router.get("/lifecycle/test") ...

@router.post(
    "/offboard",
    response_model=lifecycle_schema.UserOffboardResponse,
    summary="Offboard a user from IGA, PAM, and the local application"
)
async def offboard_user_endpoint(
    offboard_request: lifecycle_schema.UserOffboardRequest,
    db: Session = Depends(dependencies.get_db),
    current_user: user_model.User = Depends(dependencies.get_current_user) # Authenticated user performing action
):
    """
    Offboard a user:
    1. Verifies the calling user's permissions (conceptual for now).
    2. De-provisions the user from the IGA system.
    3. (Optional) De-provisions the user from the PAM system.
    4. Deactivates or deletes the user in the local application database.
    5. Logs the action in audit_logs.
    """
    iga_status = "skipped"
    pam_status = "skipped"
    local_app_status = "skipped"

    # Authorization Check (Simplified)
    # Current user should be admin of the tenant specified in offboard_request.tenant_id, or super_admin
    if current_user.tenant_id != offboard_request.tenant_id:
        # TODO: Add super_admin role check here to allow overriding
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to offboard users for this tenant."
        )

    # Fetch the local user to be offboarded to get their details (e.g., IGA ID if stored)
    user_to_offboard = auth_service.get_user_by_username(
        db, username=offboard_request.app_username, tenant_id=offboard_request.tenant_id
    )
    if not user_to_offboard:
        local_app_status = "not_found"
        # Still proceed to attempt IGA/PAM deprovisioning if IGA username might be different
        # or if we want to ensure cleanup based on provided username.
        # For now, if local user not found, assume we can't get IGA/PAM identifiers easily.
        # This logic might need refinement based on how IGA/PAM user IDs are mapped/stored.
        # Let's assume offboard_request.app_username is the identifier in IGA/PAM as well for simplicity.
        print(f"Local user '{offboard_request.app_username}' not found in tenant '{offboard_request.tenant_id}'. IGA/PAM deprovisioning might rely on this username directly.")
        # raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User '{offboard_request.app_username}' not found in tenant '{offboard_request.tenant_id}'.")


    # Retrieve IGA context for the tenant
    db_tenant = tenant_service.get_tenant(db, tenant_id=offboard_request.tenant_id)
    if not db_tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, # Should not happen if user was found in this tenant
            detail=f"Tenant with ID {offboard_request.tenant_id} not found."
        )

    iga_org_identifier = None
    if db_tenant.config_json:
        iga_org_identifier = db_tenant.config_json.get("iga_org_oid") or db_tenant.config_json.get("iga_domain_key")

    # 1. De-provision from IGA
    if settings.IGA_API_URL and settings.IGA_API_KEY and iga_org_identifier:
        iga_client = iga_client_service.IgaClient()
        # The user identifier for IGA might be different from app_username (e.g., an OID)
        # This needs a way to map app_username to IGA user identifier.
        # For now, assume app_username is usable or IGA can find by it within tenant context.
        # A more robust way: store IGA user ID in local user model during onboarding.
        iga_user_identifier_to_delete = offboard_request.app_username # Placeholder

        try:
            print(f"Attempting to de-provision user '{iga_user_identifier_to_delete}' from IGA for tenant context '{iga_org_identifier}'") # Logging
            deleted_in_iga = iga_client.delete_user(
                user_identifier=iga_user_identifier_to_delete,
                tenant_context=str(iga_org_identifier)
            )
            iga_status = "deprovisioned" if deleted_in_iga else "not_found_in_iga"
        except Exception as e:
            print(f"Error de-provisioning user '{iga_user_identifier_to_delete}' from IGA: {e}") # Logging
            iga_status = f"failed: {str(e)}"
    else:
        iga_status = "skipped_due_to_config" if not (settings.IGA_API_URL and settings.IGA_API_KEY) else "skipped_no_iga_context_for_tenant"

    # 2. (Optional) De-provision from PAM
    # PAM username might be same as app_username or mapped.
    pam_username_to_delete = offboard_request.app_username # Placeholder
    if settings.PAM_API_URL and settings.PAM_API_TOKEN:
        pam_client = pam_client_service.PamClient()
        try:
            print(f"Attempting to de-provision user '{pam_username_to_delete}' from PAM.") # Logging
            deleted_in_pam = pam_client.delete_user(pam_user_identifier=pam_username_to_delete)
            pam_status = "deprovisioned" if deleted_in_pam else "not_found_in_pam"
        except Exception as e:
            print(f"Error de-provisioning user '{pam_username_to_delete}' from PAM: {e}") # Logging
            pam_status = f"failed: {str(e)}"
    else:
        pam_status = "skipped_due_to_config"


    # 3. Deactivate or delete local application user
    if user_to_offboard:
        try:
            user_to_offboard.is_active = False
            # Or db.delete(user_to_offboard) if full deletion is required
            db.add(user_to_offboard)
            db.commit()
            local_app_status = "deactivated"
        except Exception as e:
            db.rollback()
            print(f"Error deactivating local user '{user_to_offboard.username}': {e}") # Logging
            local_app_status = f"failed_to_deactivate: {str(e)}"
    elif local_app_status == "skipped": # If not "not_found" already
        local_app_status = "not_found"


    # 4. Log action
    audit_entry = audit_log_model.AuditLog(
        tenant_id=current_user.tenant_id, # The tenant of the admin performing the action
        user_id=current_user.id,
        action_type="user_offboard_attempt",
        details={
            "offboarded_app_username": offboard_request.app_username,
            "offboarded_tenant_id": offboard_request.tenant_id,
            "iga_status": iga_status,
            "pam_status": pam_status,
            "local_app_status": local_app_status
        },
        timestamp=datetime.utcnow()
    )
    db.add(audit_entry)
    db.commit()

    return lifecycle_schema.UserOffboardResponse(
        message="User offboarding process completed.",
        app_username=offboard_request.app_username,
        iga_status=iga_status,
        pam_status=pam_status,
        local_app_status=local_app_status
    )

@router.get(
    "/review",
    response_model=lifecycle_schema.AccessReviewResponse,
    summary="Retrieve user and role data for access certification review (manual MVP)"
)
async def access_certification_review_data(
    # tenant_id_param: Optional[int] = Query(None, alias="tenantId"), # For superadmin to query specific tenant
    db: Session = Depends(dependencies.get_db),
    current_user: user_model.User = Depends(dependencies.get_current_user) # Authenticated user
):
    """
    Retrieves a list of users and their assigned roles from the IGA system
    for a specific tenant, intended for manual access certification review.

    - For a tenant admin, this will return data for their own tenant.
    - (Future) A super_admin could specify a tenant_id_param to review any tenant.
    """

    target_tenant_id = current_user.tenant_id
    # if current_user.is_superuser and tenant_id_param is not None: # Logic for superadmin
    #     target_tenant_id = tenant_id_param
    # elif not current_user.is_superuser and tenant_id_param is not None and tenant_id_param != current_user.tenant_id:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to review this tenant.")


    db_tenant = tenant_service.get_tenant(db, tenant_id=target_tenant_id)
    if not db_tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant with ID {target_tenant_id} not found."
        )

    iga_org_identifier = None
    if db_tenant.config_json:
        iga_org_identifier = db_tenant.config_json.get("iga_org_oid") or db_tenant.config_json.get("iga_domain_key")

    if not (settings.IGA_API_URL and settings.IGA_API_KEY and iga_org_identifier):
        # Log this: IGA not configured for tenant
        return lifecycle_schema.AccessReviewResponse(
            tenant_id=db_tenant.id,
            tenant_name=db_tenant.name,
            users_and_roles=[],
            review_timestamp=datetime.utcnow(),
            message="IGA system not configured or IGA identifier missing for this tenant. Cannot retrieve review data."
        )

    iga_client = iga_client_service.IgaClient()

    try:
        print(f"Fetching access review data from IGA for tenant '{db_tenant.name}' (IGA ID: {iga_org_identifier})") # Logging
        # The get_users_and_roles_for_tenant method in IgaClient is conceptual.
        # It would need to make appropriate calls to list users in the tenant context (org/domain)
        # and then for each user, get their role assignments.
        # This can be complex and IGA-specific.
        raw_iga_data: List[Dict[str, Any]] = iga_client.get_users_and_roles_for_tenant(
            tenant_context=str(iga_org_identifier)
        )

        # Transform raw_iga_data into AccessReviewUser list
        # This transformation depends on the actual structure returned by IgaClient
        # Example conceptual transformation:
        processed_users_and_roles: List[lifecycle_schema.AccessReviewUser] = []
        for item in raw_iga_data: # Assuming raw_iga_data is a list of dicts like {"user": "name", "roles": ["r1", "r2"]}
            processed_users_and_roles.append(
                lifecycle_schema.AccessReviewUser(
                    iga_user_identifier=item.get("user", "unknown_user_id"),
                    # app_username can be populated if we have a mapping from IGA ID to app username
                    roles=item.get("roles", [])
                )
            )

        return lifecycle_schema.AccessReviewResponse(
            tenant_id=db_tenant.id,
            tenant_name=db_tenant.name,
            users_and_roles=processed_users_and_roles,
            review_timestamp=datetime.utcnow()
        )

    except Exception as e:
        # Log detailed error e
        print(f"Error fetching access review data from IGA: {e}") # Logging
        # Return empty list or error message in response
        return lifecycle_schema.AccessReviewResponse(
            tenant_id=db_tenant.id,
            tenant_name=db_tenant.name,
            users_and_roles=[],
            review_timestamp=datetime.utcnow(),
            message=f"Failed to retrieve access review data from IGA: {str(e)}"
        )

@router.post(
    "/privilege",
    response_model=lifecycle_schema.PrivilegeSessionResponse,
    summary="Request a privileged session to a target asset"
)
async def request_privileged_session_endpoint(
    privilege_request: lifecycle_schema.PrivilegeSessionRequest,
    db: Session = Depends(dependencies.get_db),
    current_user: user_model.User = Depends(dependencies.get_current_user) # Authenticated app user
):
    """
    Request a privileged session (e.g., SSH/RDP) to a target asset via the PAM system.

    - **target_asset_identifier**: The identifier (name or ID) of the asset in the PAM system.
    - **pam_username**: Optional. The username to use within the PAM system. If not provided,
                      defaults to the application username (`current_user.username`).
    """

    # Authorization: Ensure current_user is active (already handled by get_current_user)
    # Further role-based checks could be added here to see if current_user is allowed
    # to request privileged access or access the specific target_asset_identifier.

    # Determine PAM username
    # This mapping could be more sophisticated, e.g., from user's profile or tenant config
    pam_username_to_use = privilege_request.pam_username or current_user.username

    if not (settings.PAM_API_URL and settings.PAM_API_TOKEN):
        # Log this: PAM not configured
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="PAM system integration is not configured."
        )

    pam_client = pam_client_service.PamClient()
    session_url: Optional[str] = None

    try:
        print(f"User '{current_user.username}' (tenant: {current_user.tenant_id}) requesting privileged session for PAM user '{pam_username_to_use}' to asset '{privilege_request.target_asset_identifier}'") # Logging
        session_url = pam_client.request_privileged_session(
            pam_username=pam_username_to_use,
            asset_identifier=privilege_request.target_asset_identifier
            # system_username could be added if PAM API needs it and it's provided
        )

        if session_url:
            # Log successful privilege session request in audit_logs
            audit_entry = audit_log_model.AuditLog(
                tenant_id=current_user.tenant_id,
                user_id=current_user.id,
                action_type="privilege_session_request_success",
                details={
                    "pam_username": pam_username_to_use,
                    "target_asset": privilege_request.target_asset_identifier,
                    "session_url_provided": True # Don't log the URL itself unless necessary & secured
                },
                timestamp=datetime.utcnow()
            )
            db.add(audit_entry)
            db.commit()

            return lifecycle_schema.PrivilegeSessionResponse(
                message="Privileged session requested successfully.",
                session_url=session_url,
                status="success"
            )
        else:
            # Log failed privilege session request in audit_logs
            audit_entry = audit_log_model.AuditLog(
                tenant_id=current_user.tenant_id,
                user_id=current_user.id,
                action_type="privilege_session_request_failed",
                details={
                    "pam_username": pam_username_to_use,
                    "target_asset": privilege_request.target_asset_identifier,
                    "reason": "PAM client did not return a session URL."
                },
                timestamp=datetime.utcnow()
            )
            db.add(audit_entry)
            db.commit()

            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY, # Error communicating with or getting valid response from PAM
                detail="PAM system did not provide a session URL."
            )

    except Exception as e:
        # Log detailed error e
        # Log failed privilege session request in audit_logs due to exception
        audit_entry = audit_log_model.AuditLog(
            tenant_id=current_user.tenant_id,
            user_id=current_user.id, # If current_user is available
            action_type="privilege_session_request_error",
            details={
                "pam_username": pam_username_to_use,
                "target_asset": privilege_request.target_asset_identifier,
                "error": str(e)
            },
            timestamp=datetime.utcnow()
        )
        db.add(audit_entry)
        db.commit() # Commit audit log even on error

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, # Or more specific if e is HTTPError from PAM client
            detail=f"An error occurred while requesting privileged session: {e}"
        )
