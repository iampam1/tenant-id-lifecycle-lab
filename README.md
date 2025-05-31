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

## Accessing the User Interface (Phase 8)

A basic web user interface has been implemented to interact with the application.

1.  **Ensure the Application is Running:**
    Follow the steps in "Running the Application (Skeleton - Phase 5)" to start the FastAPI backend. Typically:
    ```bash
    # Ensure .env is configured, DB is up, virtualenv activated, requirements installed
    uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
    ```

2.  **Navigate to the UI Entry Point:**
    Open your web browser and go to:
    **`http://localhost:8000/ui/`**

    This will usually redirect you to the login page: `http://localhost:8000/ui/login`.

3.  **Using the UI:**

    *   **Registration (`/ui/register`)**:
        -   If you are a new user setting up a new tenant, start here.
        -   Provide a Tenant Name, and details for the first Administrator for that tenant (Username, Email, Password).
        -   On successful registration, you'll usually be directed to log in.

    *   **Login (`/ui/login`)**:
        -   Enter the email and password of a registered user (e.g., the tenant admin created during registration).
        -   On successful login, an access token is stored in your browser's `localStorage`, and you should be redirected to the dashboard. The "Login" link in the navbar will change to "Logout".

    *   **Dashboard (`/ui/dashboard`)**:
        -   This is the main landing page after login.
        -   It displays basic information about the logged-in user (Email, Tenant ID).
        -   Provides links to various application functionalities:
            -   Create User in My Tenant
            -   List Users in My Tenant
            -   Onboard New User (to IGA)
            -   Request Privileged Session
            -   Offboard User
            -   Access Review Data (View)

    *   **User Management (`/ui/users`, `/ui/users/create`)**:
        -   List users within your current tenant.
        -   Create new users within your current tenant.

    *   **Lifecycle Actions (`/ui/lifecycle/...`)**:
        -   Access forms for IGA/PAM related actions like Onboarding, Privilege Session Request, Offboarding, and viewing Access Review data. These forms interact with the conceptual IGA/PAM integration points.

    *   **Logout**:
        -   Click the "Logout" link in the navbar. This will clear the stored access token and redirect you to the login page.

4.  **Important Notes for UI Usage:**
    *   The UI is built with Jinja2 templates and basic client-side JavaScript. It relies on API calls to the FastAPI backend.
    *   Authentication is handled by a JWT stored in `localStorage`. If you clear your browser's storage or the token expires, you'll be redirected to login when trying to access protected pages or make API calls.
    *   The IGA and PAM integrations are still **conceptual** at this stage. The UI forms for these actions will call the backend APIs, which in turn have placeholder client logic. You'll see console logs from the backend indicating these conceptual calls.
    *   Error messages from API interactions should be displayed on the UI pages. Check your browser's developer console for any JavaScript errors or more detailed network request information if things don't work as expected.

This UI provides a way to interact with the core application logic developed through Phase 8.

## Running with Docker (Phase 9)

The application can be containerized using Docker for consistent deployment and local testing.

### Prerequisites for Docker

-   Docker installed and running on your system.

### Building the Docker Image

1.  Navigate to the project root directory (where the `Dockerfile` is located).
2.  Run the Docker build command:
    ```bash
    docker build -t tenant-id-lifecycle-lab-app .
    ```
    This will build an image named `tenant-id-lifecycle-lab-app` using the instructions in the `Dockerfile`.

### Running the Docker Container

1.  **Environment Variables**: The application inside the Docker container needs access to environment variables, especially `DATABASE_URL` and `SECRET_KEY`. You can pass these using a `.env` file and the `--env-file` option, or individually with `-e`.

    Ensure your `.env` file is correctly configured, particularly `DATABASE_URL` to point to an accessible PostgreSQL instance. If you're running Postgres also in Docker (e.g., via Docker Compose, see next section), `DATABASE_URL` might be like `postgresql://app_user:app_user_password@your_postgres_container_name:5432/app_db`. If Postgres is running on your Docker host machine, you might need to use a special hostname like `host.docker.internal` (on Docker Desktop) or your host's IP address.

2.  **Run the container**:
    ```bash
    docker run --name tenant-id-lab-container                -p 8000:8000                --env-file .env                tenant-id-lifecycle-lab-app
    ```
    -   `--name tenant-id-lab-container`: Assigns a name to the running container.
    -   `-p 8000:8000`: Maps port 8000 on your host to port 8000 in the container.
    -   `--env-file .env`: Loads environment variables from your `.env` file into the container.
    -   `tenant-id-lifecycle-lab-app`: The name of the image to run.

3.  **Accessing the Application**:
    Once the container is running (you should see logs from Alembic and Uvicorn), you can access the application and UI in your browser at `http://localhost:8000` (or `http://localhost:8000/ui/`).

4.  **Stopping the Container**:
    ```bash
    docker stop tenant-id-lab-container
    docker rm tenant-id-lab-container # To remove it
    ```
    Or press `Ctrl+C` in the terminal if you didn't run it in detached mode (`-d`).

**Note on Database Migrations**: The `CMD` in the `Dockerfile` attempts to run `alembic upgrade head` before starting Uvicorn. This ensures the database schema is up-to-date when the container starts. Ensure your `DATABASE_URL` is correctly configured and the database server is reachable from within the Docker container.

### Running with Docker Compose (for Local Development)

For a more integrated local development setup, a `docker-compose.dev.yml` file is provided. This can manage the FastAPI application and its PostgreSQL database. It also includes conceptual (commented-out) sections for IGA and PAM backends.

**Prerequisites for Docker Compose:**
- Docker Compose installed.
- A `.env` file configured in the project root (copy from `.env.example`).
  - Ensure `DATABASE_URL` in your `.env` file is set to connect to the `app_db` service defined in `docker-compose.dev.yml`. Typically:
    `DATABASE_URL=postgresql://app_user:app_password@app_db:5432/app_db`
    (Ensure the user, password, service name 'app_db', port, and DB name match what's in `docker-compose.dev.yml` or your `.env` overrides for `POSTGRES_APP_USER`, etc.)
  - Other variables like `SECRET_KEY` are also needed.
- The `wait-for-it.sh` script should be in the project root and executable (`chmod +x wait-for-it.sh`).

**Steps to Run:**

1.  **Build and Start Services:**
    Navigate to the project root and run:
    ```bash
    docker-compose -f docker-compose.dev.yml up --build -d
    ```
    -   `-f docker-compose.dev.yml`: Specifies the compose file.
    -   `--build`: Forces Docker to build the `app` image (e.g., if `Dockerfile` or app code changed).
    -   `-d`: Runs in detached mode. Omit for interactive logs.

2.  **Accessing Services:**
    -   **FastAPI Application UI**: `http://localhost:8000/ui/`
    -   **FastAPI Application API Docs**: `http://localhost:8000/api/v1/docs`
    -   **PostgreSQL Database (app_db)**: Accessible on `localhost:5432` (or as configured by `${POSTGRES_APP_PORT_HOST}` in `.env`).

3.  **Viewing Logs:**
    ```bash
    docker-compose -f docker-compose.dev.yml logs -f app # For the FastAPI app
    docker-compose -f docker-compose.dev.yml logs -f app_db # For the Postgres database
    ```

4.  **Stopping Services:**
    ```bash
    docker-compose -f docker-compose.dev.yml down
    ```
    To remove volumes (and thus delete database data):
    ```bash
    docker-compose -f docker-compose.dev.yml down -v
    ```

**Live Reloading:** The `app` service in `docker-compose.dev.yml` mounts the `./src` directory into the container. Uvicorn is started with `--reload`, so changes to your Python code in `src/` should trigger an automatic reload of the application within the container.

**IGA/PAM Services:** The `docker-compose.dev.yml` includes commented-out sections for midPoint and JumpServer. Fully integrating these would require uncommenting, ensuring correct Docker images and configurations, and significant local system resources. For now, it's recommended to run actual IGA/PAM instances separately if needed for end-to-end testing, and configure the `app` service's environment variables (`IGA_API_URL`, `PAM_API_URL`) to point to them.
