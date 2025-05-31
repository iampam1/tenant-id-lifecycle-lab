# IGA API Endpoints & Authentication (Conceptual)

This document outlines key API endpoints and authentication mechanisms for the chosen IGA systems (midPoint as primary, Syncope as alternative) that our FastAPI application will interact with.

## 1. midPoint (Primary IGA Choice)

midPoint provides a comprehensive REST API for managing identities, resources, and configurations.

### Authentication

-   **Method**: Typically HTTP Basic Authentication or a token-based mechanism (e.g., API keys or OAuth2/OIDC if configured).
-   **Default Credentials (for Basic Auth in a default setup)**:
    -   Username: `administrator`
    -   Password: `5ecr3t` (This is the default and **must be changed** in any real instance).
-   **API Key**: For more secure programmatic access, midPoint can be configured to use API tokens/keys. These would be generated within midPoint and provided to client applications.
-   **Headers**:
    -   For Basic Auth: `Authorization: Basic <base64_encoded_username:password>`
    -   For Token: `Authorization: Bearer <token>` or a custom header like `X-API-Key: <key>`.

### Key Conceptual Endpoints (midPoint REST API)

The base URL is typically `http://<midpoint-host>:<port>/midpoint/ws/rest`.

-   **Users**:
    -   `GET /users`: List users (supports querying/filtering).
    -   `POST /users`: Create a new user.
        -   *Request Body*: XML or JSON representation of the user object.
    -   `GET /users/{userOid}`: Get a specific user by OID.
    -   `PUT /users/{userOid}`: Update a user.
    -   `DELETE /users/{userOid}`: Delete a user.
    -   `POST /users/search`: Search for users using a query object.

-   **Organizations (for Multi-Tenancy)**:
    -   If using organizations to represent tenants:
    -   `GET /orgs`: List organizations.
    -   `POST /orgs`: Create a new organization.
        -   *Request Body*: XML or JSON for the organization object.
    -   `GET /orgs/{orgOid}`: Get a specific organization.
    -   `PUT /orgs/{orgOid}`: Update an organization.
    -   `DELETE /orgs/{orgOid}`: Delete an organization.
    -   Users can be created within an organization by referencing the parent org's OID in the user creation payload.

-   **Roles**:
    -   `GET /roles`: List roles.
    -   `POST /roles`: Create a new role.
    -   `GET /roles/{roleOid}`: Get a specific role.
    -   `PUT /roles/{roleOid}`: Update a role.
    -   `DELETE /roles/{roleOid}`: Delete a role.
    -   **Assigning/Revoking Roles**: Typically done by modifying the user object's `assignment` property to include or remove role references.
        -   `PATCH /users/{userOid}` or `PUT /users/{userOid}` with a modified user object.

-   **Resources (Connectors)**:
    -   `GET /resources`: List configured resources.
    -   Endpoints for managing resource configuration, schema, synchronization, etc.

**Note**: The exact structure of request/response bodies (XML or JSON) and specific query parameters should be checked against the official midPoint documentation for the version being used.

## 2. Apache Syncope (Alternative IGA Choice)

Apache Syncope also provides a rich REST API.

### Authentication

-   **Method**: Typically HTTP Basic Authentication for the admin user, or potentially OAuth2/OIDC if configured.
-   **Default Credentials (for Basic Auth)**:
    -   Username: `admin` (or the root user configured during setup)
    -   Password: `password` (This is the default and **must be changed**).
-   **Headers**:
    -   `Authorization: Basic <base64_encoded_username:password>`
    -   `X-Syncope-Domain`: A custom header used to specify the domain (tenant) for the operation. Defaults to the "Master" domain if not provided.

### Key Conceptual Endpoints (Syncope REST API v2)

The base URL is typically `http://<syncope-host>:<port>/syncope/rest`.

-   **Domains (Tenants)**:
    -   `GET /domains`: List all domains.
    -   `POST /domains`: Create a new domain.
        -   *Request Body*: JSON like `{"key": "tenant_a"}`.
    -   `DELETE /domains/{domainKey}`: Delete a domain.

-   **Users (within a Domain)**:
    -   Requires `X-Syncope-Domain: <domainKey>` header for operations within a specific tenant.
    -   `GET /users`: List users in the specified domain.
    -   `POST /users`: Create a new user in the domain.
        -   *Request Body*: JSON user object (username, password, attributes, roles, resources).
    -   `GET /users/{userKey}`: Get a user by their key (UUID or username).
    -   `PUT /users/{userKey}`: Update a user.
    -   `DELETE /users/{userKey}`: Delete a user.

-   **Roles (within a Domain)**:
    -   Requires `X-Syncope-Domain: <domainKey>` header.
    -   `GET /roles`: List roles.
    -   `POST /roles`: Create a role.
    -   `GET /roles/{roleKey}`: Get a role.
    -   `PUT /roles/{roleKey}`: Update a role.
    -   `DELETE /roles/{roleKey}`: Delete a role.
    -   **Assigning/Revoking Roles**: Typically part of the user object's `roles` attribute when creating/updating a user.

-   **Resources (Connectors)**:
    -   `GET /connectors`: List available connector bundles.
    -   `GET /resources`: List configured external resources.

**Note**: Syncope's API is versioned (e.g., v1, v2). The exact endpoints and request/response formats should be verified against the official Apache Syncope documentation for the specific version.

## Environment Variables for Configuration

Our FastAPI application will store the IGA connection details in environment variables, loaded via `core.config.Settings`:
-   `IGA_API_URL`: Base URL of the IGA system's API.
-   `IGA_API_KEY`: Could be a token, or `username:password` for Basic Auth. The `IgaClient` will need to parse this accordingly.
