# Tenant Identity Lifecycle Lab

This project aims to build a Python-based, web-hosted, tenant-oriented identity lifecycle lab using free and open-source IGA/PAM tools and AI agents.

## Goals

- Demonstrate a comprehensive understanding of identity lifecycle management concepts.
- Implement core IGA and PAM functionalities.
- Showcase multi-tenancy in an identity context.
- Leverage AI tools for development assistance.
- Deploy the application to a free cloud hosting platform.

## Tech Stack (Initial Plan - Subject to Refinement)

- **IGA Engine:** (To be decided: midPoint or Apache Syncope)
- **PAM Engine:** (To be decided: JumpServer or Teleport)
- **Database:** PostgreSQL
- **Web Framework:** FastAPI
- **Hosting Platform:** (To be decided: Fly.io, Render.com, or Railway.app)
- **AI Agent Usage:** GitHub Copilot, ChatGPT

## Running the Application (Skeleton - Phase 5)

The FastAPI application skeleton is now set up. To run it locally:

1.  **Ensure Prerequisites are Met:**
    *   Python 3.10+ installed.
    *   A virtual environment created and activated (e.g., `python3 -m venv venv; source venv/bin/activate`).
    *   Dependencies installed: `pip install -r requirements.txt`.
    *   A PostgreSQL server is running and accessible.

2.  **Set Up Environment Variables:**
    *   Copy the `.env.example` file to a new file named `.env`:
        ```bash
        cp .env.example .env
        ```
    *   Edit the `.env` file and fill in the required values, especially:
        *   `SECRET_KEY`: Generate a strong secret key (e.g., using `openssl rand -hex 32`).
        *   `DATABASE_URL`: Ensure this points to your running PostgreSQL instance and the `app_db` database with the correct user and password (e.g., `postgresql://app_user:app_user_password@localhost:5432/app_db`).
        *   Other variables like `IGA_API_URL`, `PAM_API_TOKEN` can remain commented out or set to dummy values for now as they are not yet used by the skeleton app.

3.  **Apply Database Migrations (Conceptual First Time):**
    *   Although we haven't fully implemented models to the point of generating a perfect first migration from autodetect, the Alembic setup is in place.
    *   Conceptually, you would run:
        ```bash
        # Ensure your DATABASE_URL in .env is correct and also reflected in alembic.ini's sqlalchemy.url
        # (or that alembic.ini loads it from the environment if configured to do so)
        # alembic upgrade head
        ```
    *   This step would create the tables in your `app_db` based on the migrations. For now, you might need to create them manually using `src/db/initial_schema.sql` if you want to test DB connectivity with the current skeleton, or wait until models are fully fleshed out for Alembic autogenerate to work perfectly.
    *   **Note**: The `0001_create_base_tables.py.example` migration is a *conceptual example*. A real first migration would be generated after models are fully defined and `env.py` correctly imports them all, then running `alembic revision --autogenerate -m "initial_schema"` followed by `alembic upgrade head`.

4.  **Run the FastAPI Application:**
    Navigate to the root of the project directory (where `src` and `alembic.ini` are located).
    Use Uvicorn to run the application:
    ```bash
    uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
    ```
    *   `--reload`: Enables auto-reloading when code changes (useful for development).
    *   `--host 0.0.0.0`: Makes the server accessible from your local network.
    *   `--port 8000`: Specifies the port to run on.

5.  **Access the Application:**
    *   **API Root**: Open your browser or use `curl` to access `http://localhost:8000/`. You should see a welcome message.
    *   **OpenAPI Documentation (Swagger UI)**: Navigate to `http://localhost:8000/api/v1/docs`. You should see the auto-generated API documentation, including the test endpoints from each router (e.g., `/api/v1/auth/test`, `/api/v1/tenants/test`).
    *   **ReDoc**: Alternative documentation at `http://localhost:8000/api/v1/redoc`.

This setup provides a basic but functional FastAPI application structure, ready for further development of features in subsequent phases.
