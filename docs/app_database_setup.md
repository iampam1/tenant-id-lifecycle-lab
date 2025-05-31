# Application Database Setup (PostgreSQL)

Our custom Python (FastAPI) application requires its own PostgreSQL database to store application-specific data, such as tenant information, application users, roles, audit logs, etc. This document outlines the conceptual setup.

## 1. Provision a PostgreSQL Instance

You'll need a running PostgreSQL server. For development and MVP deployment, several cloud providers offer free tiers that are suitable:

-   **Fly.io**: Offers a free "starter" tier for PostgreSQL.
-   **Render.com**: Provides a free PostgreSQL add-on.
-   **Railway.app**: Offers a free PostgreSQL service as part of its trial/hobby tier.
-   **Local Instance**: For local development, you can install PostgreSQL directly on your machine or run it via Docker.

The choice of hosting for the database will depend on where the main application is deployed.

## 2. Create the Application Database and User

Regardless of where PostgreSQL is hosted, you'll need to create:
1.  A dedicated database for the application (e.g., `app_db`).
2.  A dedicated user with privileges to access this database.

### Conceptual SQL Commands:

Connect to your PostgreSQL server as a superuser (or a user with database creation privileges).

```sql
-- 1. Create the database for the application
CREATE DATABASE app_db;

-- 2. Create a dedicated user for the application
-- Replace 'app_user_password' with a strong, unique password.
CREATE USER app_user WITH PASSWORD 'app_user_password';

-- 3. Grant all privileges on the app_db to the app_user
-- For enhanced security in production, you might grant more restrictive privileges
-- after the initial schema setup by Alembic.
GRANT ALL PRIVILEGES ON DATABASE app_db TO app_user;

-- 4. (Optional but good practice) Set the default schema for the user in this database
-- This helps if you are not using the public schema or want to ensure the user
-- operates within a specific schema by default.
-- ALTER USER app_user SET search_path TO public; -- Or your app's schema if different
```

### Verification (Conceptual):

You should be able to connect to the newly created database using the new user's credentials:

```bash
# psql -U app_user -d app_db -h your_postgres_host
```
You'll be prompted for `app_user_password`.

## Next Steps

-   The connection string for this database (e.g., `postgresql://app_user:app_user_password@your_postgres_host:5432/app_db`) will be needed for:
    -   The Python application's configuration (e.g., in a `.env` file for FastAPI settings).
    -   Alembic configuration (`alembic.ini`) to manage database migrations.

## 3. Initial Application Database Schema

The following tables are planned for the initial version of the application, based on Phase 4, Step 2 and Step 4 of the project issue. Alembic will be used to manage the creation and evolution of this schema.

-   **`tenants` Table:** Stores information about each tenant.
    -   `id`: SERIAL PRIMARY KEY (or UUID)
    -   `name`: VARCHAR(255) UNIQUE NOT NULL
    -   `created_at`: TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    -   `config_json`: JSONB NULLABLE (for tenant-specific configurations, IGA/PAM connection details, etc.)

-   **`users` Table:** Stores application users (these are users of our web app, e.g., tenant admins, not necessarily end-users managed by IGA).
    -   `id`: SERIAL PRIMARY KEY (or UUID)
    -   `tenant_id`: INTEGER NOT NULL (FOREIGN KEY REFERENCES `tenants(id)` ON DELETE CASCADE)
    -   `username`: VARCHAR(255) NOT NULL
    -   `email`: VARCHAR(255) UNIQUE NOT NULL
    -   `hashed_password`: VARCHAR(255) NOT NULL
    -   `created_at`: TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    -   `is_active`: BOOLEAN DEFAULT TRUE
    -   UNIQUE (`tenant_id`, `username`)
    -   UNIQUE (`tenant_id`, `email`)

-   **`roles` Table:** Defines roles within the application for authorization (e.g., tenant admin, app admin).
    -   `id`: SERIAL PRIMARY KEY (or UUID)
    -   `tenant_id`: INTEGER NULLABLE (FOREIGN KEY REFERENCES `tenants(id)` ON DELETE CASCADE) - Nullable if some roles are global (Super Admin).
    -   `role_name`: VARCHAR(100) NOT NULL
    -   `permissions_json`: JSONB NULLABLE (for storing specific permissions associated with the role)
    -   UNIQUE (`tenant_id`, `role_name`) - A role name should be unique within a tenant or globally if tenant_id is NULL.

-   **`user_roles` Table (Join Table):** Links users to their roles.
    -   `id`: SERIAL PRIMARY KEY
    -   `user_id`: INTEGER NOT NULL (FOREIGN KEY REFERENCES `users(id)` ON DELETE CASCADE)
    -   `role_id`: INTEGER NOT NULL (FOREIGN KEY REFERENCES `roles(id)` ON DELETE CASCADE)
    -   UNIQUE (`user_id`, `role_id`)

-   **`audit_logs` Table (Mentioned in Phase 11, good to plan for):**
    -   `id`: BIGSERIAL PRIMARY KEY
    -   `tenant_id`: INTEGER NULLABLE (FOREIGN KEY REFERENCES `tenants(id)` ON DELETE SET NULL)
    -   `user_id`: INTEGER NULLABLE (FOREIGN KEY REFERENCES `users(id)` ON DELETE SET NULL) (User performing the action)
    -   `action_type`: VARCHAR(100) NOT NULL (e.g., "user_onboard", "privilege_request", "tenant_created")
    -   `details`: JSONB NULLABLE (for storing event-specific data)
    -   `timestamp`: TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP

This schema will be implemented and version-controlled using Alembic migrations.

## 4. Multi-Tenancy Strategy for the Python Application

The project issue (Phase 4, Step 3) specifies the multi-tenancy strategy for the custom Python web application:

-   **Chosen Strategy: Option B - Row-Level Isolation.**
    -   This means most tables in the `app_db` that contain tenant-specific data will have a `tenant_id` column.
    -   This `tenant_id` will be a foreign key referencing the `tenants.id` column.

### Rationale for MVP:

-   **Simplicity of Management**: Compared to schema-per-tenant or database-per-tenant, row-level isolation is generally simpler to manage from an infrastructure and application logic perspective for an MVP.
-   **Querying**: All application queries that access tenant-specific data *must* include a filter based on the `tenant_id` (e.g., `WHERE tenant_id = current_tenant_id`). This ensures data segregation.
-   **Shared Schema**: All tenants share the same database schema, simplifying schema migrations (Alembic will manage one set of schema changes).

### Implementation Notes:

-   The `users`, `roles`, and potentially `audit_logs` tables already include a `tenant_id` column in the defined schema.
-   Application logic (e.g., in FastAPI service layers or routers) will be responsible for:
    -   Identifying the current tenant context (likely from the authenticated user's session or token).
    -   Ensuring that all database queries are correctly scoped to that `tenant_id`.
-   Global data (e.g., super-admin users or system-wide roles, if any) might have a `NULL` `tenant_id` or be managed in separate tables not subject to this specific row-level isolation. The `roles` table schema allows for `tenant_id` to be `NULL` to accommodate this possibility.

This strategy aligns with the IGA approach where Syncope uses native "domains" or midPoint might use separate instances or an organization attribute, keeping the IGA's multi-tenancy distinct from the app's internal multi-tenancy for its own data.

## 5. Setting Up Alembic for Database Migrations

Alembic is a database migration tool for SQLAlchemy. It allows you to manage and version your database schema changes over time.

### Initialization (Conceptual)

Typically, you would initialize Alembic in your project by running:

```bash
# alembic init src/db/migrations
```
This command creates:
- An `alembic.ini` file in your project root.
- A `src/db/migrations` directory containing:
    - `env.py`: The runtime configuration script for Alembic.
    - `script.py.mako`: A template for new migration scripts.
    - `versions/`: A directory to store individual migration script files.

For this project, these files and directories have been created manually with placeholder content.

### Configuration

1.  **`alembic.ini`**:
    -   This file is the main configuration file for Alembic.
    -   The most important setting is `sqlalchemy.url`, which must be updated to point to your application database (`app_db`).
        Example: `sqlalchemy.url = postgresql://app_user:app_user_password@localhost:5432/app_db`
    -   `script_location` is set to `src/db/migrations`.

2.  **`src/db/migrations/env.py`**:
    -   This script is run when you execute Alembic commands.
    -   Crucially, it needs to be configured to find your SQLAlchemy models' metadata. This is done by setting `target_metadata`.
    -   You will need to import `Base` (the declarative base class for your SQLAlchemy models, likely to be defined in `src/app/models/base.py` later) and set `target_metadata = Base.metadata`. This allows Alembic's autogenerate feature to detect changes to your models and create migration scripts.
       ```python
       # Example placeholder in env.py:
       # from src.app.models.base import Base # Adjust import path
       # target_metadata = Base.metadata
       target_metadata = None # Must be updated
       ```

With these configurations in place, Alembic can connect to your database and manage schema migrations.

## 6. Creating the Initial Alembic Migration

Once Alembic is configured and your SQLAlchemy models (defining tables like `tenants`, `users`, `roles`, etc.) are created (covered in Phase 5), you would create your first migration script.

### Generating a Migration Script (Conceptual - after models exist)

If your models are defined and `env.py` correctly points to their `Base.metadata`, you could use Alembic's autogenerate feature:

```bash
# alembic revision -m "create_base_tables" --autogenerate
```
This command compares the current database schema (if any) with the schema defined by your models and generates a new migration script in `src/db/migrations/versions/` with the necessary `op.create_table()` calls.

Alternatively, you can create an empty migration script and fill it in manually:
```bash
# alembic revision -m "create_base_tables"
```

### Example Content of the First Migration Script

The first migration script (e.g., `src/db/migrations/versions/xxxxxxxxxxxx_create_base_tables.py`) would use Alembic's `op` functions to create the tables defined in your initial schema.

**Conceptual Structure (`xxxxxxxxxxxx_create_base_tables.py`):**

```python
"""create_base_tables

Revision ID: xxxxxxxxxxxx
Revises:
Create Date: YYYY-MM-DD HH:MM:SS.ffffff

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'xxxxxxxxxxxx' # Actual revision ID will be generated
down_revision: Union[str, None] = None # This is the first migration
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('tenants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('config_json', sa.JSON(), nullable=True), # Changed from JSONB for broader SQLAlchemy compatibility w/o dialect specifics
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_table('roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=True),
        sa.Column('role_name', sa.String(length=100), nullable=False),
        sa.Column('permissions_json', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'role_name', name='uq_tenant_role_name')
    )
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.true(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'email', name='uq_tenant_email'),
        sa.UniqueConstraint('tenant_id', 'username', name='uq_tenant_username')
    )
    op.create_table('audit_logs',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action_type', sa.String(length=100), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('timestamp', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user_roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'role_id', name='uq_user_role')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user_roles')
    op.drop_table('audit_logs')
    op.drop_table('users')
    op.drop_table('roles')
    op.drop_table('tenants')
    # ### end Alembic commands ###
```

### Applying the Migration

Once the migration script is created and reviewed, you apply it to the database using:

```bash
# alembic upgrade head
```
This command runs all pending migration scripts, bringing the database schema to the latest version.
