# API Usage Guide - Phase 7: IGA & PAM Backend Integration (Lifecycle Endpoints)

This guide details how to use the new lifecycle API endpoints implemented in Phase 7. These endpoints interact conceptually with IGA and PAM systems.

**Base URL**: Assume `http://localhost:8000`. All endpoint paths are prefixed with `/api/v1` (e.g., `/api/v1/lifecycle/...`).
**Authentication**: All lifecycle endpoints require a valid JWT Bearer token obtained via the `/api/v1/auth/login` endpoint. Include it in the `Authorization` header.

## 1. Onboard a New User

Provisions a user in the IGA system, optionally creates/links a local app user, and assigns a role in IGA.

-   **Endpoint**: `POST /api/v1/lifecycle/onboard`
-   **Method**: `POST`
-   **Headers**: `Authorization: Bearer <token>`
-   **Request Body** (`UserOnboardRequest` schema):
    ```json
    {
        "username": "iga_user_01",
        "email": "iga_user_01@example.com",
        "first_name": "IGA",
        "last_name": "UserOne",
        "password": "StrongPasswordIGA1!",
        "tenant_id": 1, // The app's internal ID for the target tenant
        "iga_role": "standard_iga_role_name_or_id", // Conceptual role in IGA
        "extra_iga_attributes": {"department": "Sales"}
    }
    ```
-   **Success Response** (HTTP 201 Created, `UserOnboardResponse` schema):
    ```json
    {
        "message": "User onboarding process initiated successfully.",
        "app_user_id": 101, // Optional: ID of the user in our app's DB
        "iga_user_id": "iga-uuid-for-user-01", // Optional: ID from IGA system
        "status": "success"
    }
    ```
-   **Error Responses**:
    -   HTTP 400: IGA not configured for the tenant, or other input validation errors.
    -   HTTP 401: Authentication required/invalid token.
    -   HTTP 403: Authenticated user not authorized for the target tenant.
    -   HTTP 404: Target tenant not found in the app's DB.
    -   HTTP 502: Error communicating with the IGA system.

## 2. Request Privileged Session

Requests a privileged session URL from the PAM system for an authenticated application user to a target asset.

-   **Endpoint**: `POST /api/v1/lifecycle/privilege`
-   **Method**: `POST`
-   **Headers**: `Authorization: Bearer <token>`
-   **Request Body** (`PrivilegeSessionRequest` schema):
    ```json
    {
        "target_asset_identifier": "prod-db-server-01_or_pam_asset_id",
        "pam_username": "pam_admin_for_db_server" // Optional: PAM username if different from app username
    }
    ```
    *(The `tenant_id` for context is derived from the `current_user`'s token).*
-   **Success Response** (HTTP 200 OK, `PrivilegeSessionResponse` schema):
    ```json
    {
        "message": "Privileged session requested successfully.",
        "session_url": "https://pam.example.com/session/xyz123abc", // Example URL from PAM
        "status": "success",
        "error_detail": null
    }
    ```
-   **Error Responses**:
    -   HTTP 401: Authentication required/invalid token.
    -   HTTP 501: PAM system integration not configured.
    -   HTTP 502: PAM system did not provide a session URL or error during communication.
    -   HTTP 500: Other internal server errors.
-   **Auditing**: This action is logged in the application's `audit_logs` table.

## 3. Offboard a User

De-provisions a user from IGA, conceptually from PAM, and deactivates them in the local application.

-   **Endpoint**: `POST /api/v1/lifecycle/offboard`
-   **Method**: `POST`
-   **Headers**: `Authorization: Bearer <token>`
-   **Request Body** (`UserOffboardRequest` schema):
    ```json
    {
        "app_username": "iga_user_01", // Username in our application
        "tenant_id": 1 // The app's internal ID for the tenant this user belongs to
    }
    ```
-   **Success Response** (HTTP 200 OK, `UserOffboardResponse` schema):
    ```json
    {
        "message": "User offboarding process completed.",
        "app_username": "iga_user_01",
        "iga_status": "deprovisioned", // or "not_found_in_iga", "failed: ...", "skipped_..."
        "pam_status": "deprovisioned", // or "not_found_in_pam", "failed: ...", "skipped_..."
        "local_app_status": "deactivated" // or "not_found", "failed_to_deactivate"
    }
    ```
-   **Error Responses**:
    -   HTTP 401: Authentication required/invalid token.
    -   HTTP 403: Authenticated user not authorized for the target tenant.
    -   HTTP 404: Target tenant or user to offboard not found in the app's DB (initial check).
-   **Auditing**: This action and its step-wise outcomes are logged in `audit_logs`.

## 4. Access Certification Review Data (Manual MVP)

Retrieves a list of users and their roles from the IGA system for a tenant, intended for manual review.

-   **Endpoint**: `GET /api/v1/lifecycle/review`
-   **Method**: `GET`
-   **Headers**: `Authorization: Bearer <token>`
-   **Query Parameters**: None (tenant context is derived from the authenticated user's token).
    *(Future: A super_admin might use a `tenantId` query parameter).*
-   **Success Response** (HTTP 200 OK, `AccessReviewResponse` schema):
    ```json
    {
        "tenant_id": 1,
        "tenant_name": "OmegaCorp",
        "users_and_roles": [
            {
                "iga_user_identifier": "iga_user_01",
                "app_username": "user_01_app_mapping", // Optional, if linked
                "roles": ["IGA_Role_A", "IGA_Role_B"]
            },
            {
                "iga_user_identifier": "another_iga_user",
                "app_username": null,
                "roles": ["IGA_Role_A"]
            }
        ],
        "review_timestamp": "YYYY-MM-DDTHH:MM:SS.ffffff+00:00",
        "message": "Data retrieved for manual review."
    }
    ```
    If IGA is not configured for the tenant, `users_and_roles` will be empty and the message will indicate this.
-   **Error Responses**:
    -   HTTP 401: Authentication required/invalid token.
    -   HTTP 404: Tenant associated with the current user not found.
    -   Response with empty `users_and_roles` and an error message if IGA call fails.

## Conceptual Testing Notes for Phase 7

-   **Environment Setup**:
    -   Ensure `IGA_API_URL`, `IGA_API_KEY`, `PAM_API_URL`, `PAM_API_TOKEN` are set in your `.env` file. Since the IGA/PAM clients are conceptual, these can be dummy values, but they must be present for the client instantiation logic to pass if you're not modifying the client's constructor to handle missing settings more gracefully for offline testing.
    -   Have a tenant created (e.g., via `POST /api/v1/auth/register`) and its `config_json` manually updated in the database to include a dummy `iga_org_oid` or `iga_domain_key` if your client logic relies on it for context. Example: `{"iga_org_oid": "dummy_iga_tenant_id_123"}`.
-   **Onboarding**:
    -   Attempt to onboard a user. Check console logs for "CONCEPTUAL" messages from `IgaClient`. Verify response schema.
    -   Test error cases: invalid `tenant_id`, missing IGA config for tenant.
-   **Privilege Elevation**:
    -   Request privileged access. Check console logs for `PamClient` conceptual messages. Verify response schema (especially the dummy URL structure).
    -   Check `audit_logs` table for success/failure entries.
    -   Test with PAM not configured in `.env`.
-   **Offboarding**:
    -   Onboard a user (conceptually). Then attempt to offboard them.
    -   Check console logs for IGA/PAM client conceptual de-provisioning messages.
    -   Verify local user in DB is marked inactive.
    -   Check `audit_logs`.
-   **Access Review**:
    -   Call the review endpoint. Verify console logs from `IgaClient`.
    -   Check response structure. Test with a tenant that has no (or dummy) IGA config in its `config_json`.

These tests will primarily verify the FastAPI application logic, request/response handling, and that the conceptual calls to IGA/PAM clients are being made as expected. Full end-to-end testing would require live IGA/PAM instances and fully implemented clients.
