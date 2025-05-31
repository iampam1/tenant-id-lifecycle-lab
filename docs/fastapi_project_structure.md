# FastAPI Project Structure

This document outlines the directory structure for the FastAPI web application, as per the project issue (Phase 5.1, Step 2). This structure aims to organize the codebase logically for maintainability and scalability.

## Root Application Directory: `src/app/`

-   **`main.py`**: The entry point of the FastAPI application. Initializes the FastAPI app instance, includes routers, and configures middleware.

-   **`core/`**: Core application logic and utilities.
    -   `config.py`: Pydantic-based settings management (loading from environment variables).
    -   `security.py`: Authentication-related utilities (e.g., password hashing, JWT creation/verification - to be developed in Phase 6).
    -   `dependencies.py`: Common FastAPI dependencies, like database session management (`get_db`).

-   **`db/`**: Database-related modules.
    -   `session.py`: SQLAlchemy database engine and session setup (`SessionLocal`).
    -   `migrations/`: (Already created for Alembic) Contains Alembic migration scripts and configuration (`env.py`).
    -   `initial_schema.sql`: (Already created) Reference SQL for the initial schema.

-   **`models/`**: SQLAlchemy ORM models.
    -   `base.py`: Defines the declarative base (`Base`) for all models.
    -   `tenant.py`: `Tenant` model.
    -   `user.py`: `User` model (application users).
    -   `role.py`: `Role` model (application roles).
    -   `access_request.py`: (Placeholder for later) Model for access requests, if needed directly by the app.
    -   `audit_log.py`: (Placeholder, based on `audit_logs` table) Model for audit logs.
    -   *(Other models as needed)*

-   **`schemas/`**: Pydantic schemas for data validation and serialization (request/response models).
    -   `tenant_schema.py`: Schemas related to tenant operations (e.g., `TenantCreate`, `TenantRead`).
    -   `user_schema.py`: Schemas for user operations.
    -   `role_schema.py`: Schemas for role operations.
    -   `token_schema.py`: Schemas for JWT tokens (e.g., `Token`, `TokenData` - for Phase 6).
    -   *(Other schemas as needed)*

-   **`routers/`**: FastAPI routers, defining API endpoints.
    -   `auth_router.py`: Endpoints for authentication (login, registration - for Phase 6).
    -   `tenant_router.py`: Endpoints for tenant management.
    -   `user_router.py`: Endpoints for managing application users.
    -   `lifecycle_router.py`: Endpoints for identity lifecycle operations (onboarding, offboarding, privilege elevation - for Phase 7).

-   **`services/`**: Business logic layer, interacting with the database and external services (IGA/PAM).
    -   `auth_service.py`: Logic for user authentication.
    -   `tenant_service.py`: Logic for tenant operations.
    -   `user_service.py`: Logic for application user operations.
    -   `iga_client.py`: Client for interacting with the IGA engine's API (for Phase 7).
    -   `pam_client.py`: Client for interacting with the PAM engine's API (for Phase 7).

-   **`templates/`**: (For Phase 8) Jinja2 templates if server-rendered HTML pages are used.
-   **`static/`**: (For Phase 8) Static files (CSS, JS, images).

-   **`__init__.py`**: Makes `app` a Python package.

## Other Project Directories (already created or standard)

-   **`src/cli/`**: Command-line interface scripts (if any).
-   **`src/tests/`**: Pytest tests.
-   **`docs/`**: Project documentation.
-   **`third_party/`**: Documentation/notes for third-party tools like midPoint, JumpServer.
-   **`.env.example`**: Example environment variables file.
-   **`alembic.ini`**: Alembic configuration file.
-   **`requirements.txt`**: Python package dependencies.
-   **`Dockerfile`**: (For Phase 9) For containerizing the application.
