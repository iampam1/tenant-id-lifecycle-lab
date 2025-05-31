# API Usage Guide - Phase 6: Tenant Management & Authentication

This guide explains how to use the API endpoints implemented in Phase 6, covering tenant creation, tenant admin registration, login, and creating users within a tenant.

**Base URL**: Assume the application is running locally at `http://localhost:8000`. All endpoint paths are prefixed with `/api/v1` (as defined by `settings.API_V1_STR`).

## 1. Register a New Tenant and its First Administrator

This is the first step to get started with a new tenant.

-   **Endpoint**: `POST /api/v1/auth/register`
-   **Method**: `POST`
-   **Request Body** (`TenantAdminRegisterRequest` schema):
    ```json
    {
        "email": "first_admin@example.com",
        "username": "firstadmin",
        "password": "SecurePassword123!",
        "tenant_name": "OmegaCorp"
    }
    ```
-   **Success Response** (HTTP 201 Created, `UserRead` schema):
    ```json
    {
        "email": "first_admin@example.com",
        "username": "firstadmin",
        "is_active": true,
        "id": 1, // User ID
        "tenant_id": 1, // Tenant ID for OmegaCorp
        "created_at": "YYYY-MM-DDTHH:MM:SS.ffffff+00:00"
    }
    ```
-   **Error Responses**:
    -   HTTP 400: If tenant name already exists, or user email/username constraints are violated (e.g., email globally unique).
    -   HTTP 500: Internal server error.

## 2. Log In to Get an Access Token

Once an administrator (or any user) is created, they can log in.

-   **Endpoint**: `POST /api/v1/auth/login`
-   **Method**: `POST`
-   **Request Body** (OAuth2PasswordRequestForm - sent as `application/x-www-form-urlencoded`):
    -   `username`: The user's email address (e.g., `first_admin@example.com`)
    -   `password`: The user's password (e.g., `SecurePassword123!`)
    *Example with `curl`*:
    ```bash
    curl -X POST "http://localhost:8000/api/v1/auth/login"          -H "Content-Type: application/x-www-form-urlencoded"          -d "username=first_admin@example.com&password=SecurePassword123!"
    ```
-   **Success Response** (HTTP 200 OK, `Token` schema):
    ```json
    {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", // Actual JWT
        "token_type": "bearer"
    }
    ```
-   **Error Responses**:
    -   HTTP 401: Incorrect email or password.
    -   HTTP 400: User is inactive.

## 3. Accessing Protected Endpoints (Tenant Management)

Once you have an `access_token`, you must include it in the `Authorization` header for protected endpoints.

**Header Format**: `Authorization: Bearer <your_access_token>`

### 3.1. Create a New Tenant (as an already authenticated user)

While `/auth/register` creates the first tenant and its admin, this endpoint would be used if, for example, a super-admin is creating more tenants. (Current implementation allows any authenticated user - requires RBAC refinement).

-   **Endpoint**: `POST /api/v1/tenants/`
-   **Method**: `POST`
-   **Headers**: `Authorization: Bearer <token>`
-   **Request Body** (`TenantCreate` schema):
    ```json
    {
        "name": "BetaSolutions",
        "config_json": {"info": "Another tenant"}
    }
    ```
-   **Success Response** (HTTP 201 Created, `TenantRead` schema).
-   **Error Responses**:
    -   HTTP 400: Tenant name already exists.
    -   HTTP 401: Authentication required/invalid token.

### 3.2. List All Tenants

-   **Endpoint**: `GET /api/v1/tenants/`
-   **Method**: `GET`
-   **Headers**: `Authorization: Bearer <token>`
-   **Query Parameters (Optional)**: `skip` (int, default 0), `limit` (int, default 100).
-   **Success Response** (HTTP 200 OK, `List[TenantRead]` schema).
-   **Error Responses**:
    -   HTTP 401: Authentication required/invalid token.

### 3.3. Get a Specific Tenant

-   **Endpoint**: `GET /api/v1/tenants/{tenant_id}`
-   **Method**: `GET`
-   **Headers**: `Authorization: Bearer <token>`
-   **Success Response** (HTTP 200 OK, `TenantRead` schema).
-   **Error Responses**:
    -   HTTP 401: Authentication required/invalid token.
    -   HTTP 404: Tenant not found.
    -   (Future) HTTP 403: If user not authorized for this tenant.

### 3.4. Update a Tenant

-   **Endpoint**: `PUT /api/v1/tenants/{tenant_id}`
-   **Method**: `PUT`
-   **Headers**: `Authorization: Bearer <token>`
-   **Request Body** (`TenantUpdate` schema):
    ```json
    {
        "name": "OmegaCorp International",
        "config_json": {"status": "active", "tier": "gold"}
    }
    ```
-   **Success Response** (HTTP 200 OK, `TenantRead` schema).
-   **Error Responses**:
    -   HTTP 400: New tenant name conflicts with another tenant.
    -   HTTP 401: Authentication required/invalid token.
    -   HTTP 404: Tenant not found.
    -   (Future) HTTP 403: If user not authorized for this tenant.

### 3.5. Delete a Tenant

-   **Endpoint**: `DELETE /api/v1/tenants/{tenant_id}`
-   **Method**: `DELETE`
-   **Headers**: `Authorization: Bearer <token>`
-   **Success Response**: HTTP 204 No Content.
-   **Error Responses**:
    -   HTTP 401: Authentication required/invalid token.
    -   HTTP 404: Tenant not found.
    -   (Future) HTTP 403: If user not authorized for this tenant.

## 4. Create a New User within a Tenant

This is typically performed by an authenticated tenant administrator for their own tenant.

-   **Endpoint**: `POST /api/v1/users/`
-   **Method**: `POST`
-   **Headers**: `Authorization: Bearer <token>` (Token of the tenant admin)
-   **Request Body** (`UserCreate` schema):
    ```json
    {
        "email": "new_user@omegacorp.com",
        "username": "newbie",
        "password": "PasswordForAll123",
        "is_active": true
        // "tenant_id" can be omitted if current admin is creating for their own tenant.
        // If current admin is super_admin, they might specify a tenant_id.
        // Example: "tenant_id": 1 (for OmegaCorp)
    }
    ```
-   **Success Response** (HTTP 201 Created, `UserRead` schema):
    ```json
    {
        "email": "new_user@omegacorp.com",
        "username": "newbie",
        "is_active": true,
        "id": 2, // New User ID
        "tenant_id": 1, // Tenant ID for OmegaCorp
        "created_at": "YYYY-MM-DDTHH:MM:SS.ffffff+00:00"
    }
    ```
-   **Error Responses**:
    -   HTTP 400: Duplicate email/username within the tenant, or other validation errors.
    -   HTTP 401: Authentication required/invalid token.
    -   HTTP 403: If the authenticated user is not authorized to create users for the target tenant (e.g., trying to create for a different tenant and not being a super_admin).

## Conceptual Testing Notes

-   **Registration & Login**:
    1.  Register a new tenant admin (e.g., for "TenantA"). Verify 201.
    2.  Attempt to register the same tenant admin or tenant name. Verify 400.
    3.  Log in with the new admin credentials. Verify 200 and token received.
    4.  Attempt login with incorrect credentials. Verify 401.
-   **Tenant CRUD (with token)**:
    1.  Using the admin's token, try to GET tenant details for "TenantA". Verify 200.
    2.  Try to list tenants. Verify 200.
    3.  (If super_admin implemented) Try to create another tenant "TenantB". Verify 201.
    4.  Update "TenantA". Verify 200.
    5.  Delete "TenantA" (or "TenantB"). Verify 204.
-   **User Creation (with token)**:
    1.  As admin of "TenantA", create a new user within "TenantA". Verify 201.
    2.  Attempt to create a user with a duplicate email/username within "TenantA". Verify 400.
    3.  (If logic implemented) Attempt to create a user for "TenantB" as admin of "TenantA". Verify 403.
-   **Token Expiration**:
    -   If possible, manually shorten token expiry in settings for testing.
    -   Wait for token to expire, then try accessing a protected endpoint. Verify 401.
-   **Input Validation**: Test with invalid request bodies (missing fields, incorrect types, fields not meeting length constraints) for all POST/PUT endpoints. Verify appropriate 422 Unprocessable Entity or 400 Bad Request errors.

This guide provides a starting point for interacting with and testing the APIs developed in Phase 6.
