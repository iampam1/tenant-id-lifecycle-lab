-- Placeholder for initial database schema.
-- This file is for reference; Alembic will be the source of truth for schema management.

-- Tenants Table: Stores information about each tenant.
CREATE TABLE tenants (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    config_json JSONB NULLABLE
);

-- Users Table: Stores application users.
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    username VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL, -- Initially, let's make email globally unique
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    UNIQUE (tenant_id, username),
    UNIQUE (tenant_id, email) -- Email unique per tenant
);
-- Reconsidering email uniqueness: The spec says UNIQUE (tenant_id, email).
-- So, removing global UNIQUE constraint for email and keeping tenant-specific one.
-- The UNIQUE (tenant_id, email) above handles this.

-- Roles Table: Defines roles within the application.
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NULLABLE,
    role_name VARCHAR(100) NOT NULL,
    permissions_json JSONB NULLABLE,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    UNIQUE (tenant_id, role_name)
);

-- User_Roles Table (Join Table): Links users to their roles.
CREATE TABLE user_roles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    UNIQUE (user_id, role_id)
);

-- Audit_Logs Table
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    tenant_id INTEGER NULLABLE,
    user_id INTEGER NULLABLE,
    action_type VARCHAR(100) NOT NULL,
    details JSONB NULLABLE,
    "timestamp" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- Quoted "timestamp" to avoid conflict with keyword
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Note: Specific choices like SERIAL vs UUID for IDs, exact VARCHAR lengths,
-- and nullability will be finalized in Alembic migration scripts.
-- JSONB is used for flexibility with config_json and permissions_json.
