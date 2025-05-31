# PAM API Endpoints & Authentication (Conceptual)

This document outlines key API endpoints and authentication mechanisms for the chosen Privileged Access Management (PAM) systems (JumpServer as primary, Teleport as alternative) that our FastAPI application might interact with.

## 1. JumpServer (Primary PAM Choice)

JumpServer provides a REST API for programmatic management and interaction.

### Authentication

-   **Method**: Typically Token-based authentication.
    -   An API token is generated for a user (often an admin or service account) within the JumpServer UI.
-   **Headers**:
    -   `Authorization: Token <your_jumpserver_api_token>`
    -   `Content-Type: application/json`
    -   `Accept: application/json`

### Key Conceptual Endpoints (JumpServer REST API)

The base URL is typically `http://<jumpserver-host>:<port>/api/v1` (or `/api/v2` etc., depending on version).

-   **Users (JumpServer Users)**:
    -   `GET /users/users/`: List JumpServer users.
    -   `POST /users/users/`: Create a JumpServer user.
        -   *Request Body*: JSON with user details (username, name, email, password, roles, etc.).
    -   `GET /users/users/{id}/`: Get a specific JumpServer user.
    -   `PUT /users/users/{id}/`: Update a JumpServer user.
    -   `DELETE /users/users/{id}/`: Delete a JumpServer user.

-   **Assets (Managed Systems)**:
    -   `GET /assets/assets/`: List assets.
    -   `POST /assets/assets/`: Create an asset.
    -   `GET /assets/assets/{id}/`: Get a specific asset.
    -   (Endpoints for managing system users on assets, asset permissions, etc.)

-   **Session Management / Access Requests**:
    -   JumpServer's API for directly requesting a session URL for a user to a specific asset might vary or might be part of a broader "perms" (permissions) module.
    -   The issue description (Phase 7.1, Step 6 - JumpServerClient) suggests an endpoint like `/api/access-requests/` or similar for initiating a session and getting a URL. This needs to be verified with JumpServer's specific API documentation.
    -   `POST /perms/asset-permissions/connect/`: This is another potential endpoint pattern seen in some JumpServer discussions for initiating connections, but requires verification. It might return connection details or a token for a websocket connection.
    -   The goal is to find an endpoint that, given a JumpServer username and an asset identifier, can return a web-accessible URL to launch a session (e.g., SSH, RDP via web terminal).

-   **Audit**:
    -   `GET /audits/login-logs/`: Access login logs.
    -   `GET /audits/command-logs/`: Access command execution logs from sessions.

**Note**: The exact API paths and request/response structures should be confirmed from the official JumpServer documentation for the specific version being used.

## 2. Teleport (Alternative PAM Choice)

Teleport's primary interaction for users is often via its CLI (`tsh`) or Web UI, which handle certificate-based authentication. For programmatic API interaction, Teleport offers a gRPC API and an HTTP API that often mirrors gRPC services.

### Authentication

-   **Method**: Typically involves mutual TLS (mTLS) with client certificates for backend services, or specific tokens for certain API operations.
    -   Generating short-lived user certificates via `tctl auth sign` or an identity provider flow.
    -   Using provisioned tokens for nodes or bots.
-   For a simple client interacting with the Teleport Proxy/Auth service's HTTP endpoints, it might involve a pre-shared token or specific user credentials if an API endpoint supports it. The issue description's example `TeleportClient` (Phase 7.1, Step 6) suggests a simple URL construction for SSH, implying UI redirection rather than a direct API session URL retrieval for a third-party app.

### Key Conceptual Endpoints/Interactions

-   **User Management**:
    -   Primarily via `tctl users add/rm` on the auth server.
    -   APIs exist for managing users, roles, and connectors (e.g., GitHub SSO).
    -   `GET /api/users`, `POST /api/users` (requires appropriate auth).

-   **Session Initiation**:
    -   Teleport's strength is its certificate-based access. A third-party app (like ours) wanting to initiate a session for a user would typically:
        1.  Ensure the user exists in Teleport and has appropriate roles.
        2.  **Redirect to Teleport Web UI**: Construct a URL that takes the user to the Teleport Web UI to select an asset and start a session. The example from the issue was:
            `https://{proxy_addr}/web/ssh/host/{host}?username={user}&t={self.token}` (where `t` might be a specific type of temporary token or parameter).
        3.  **Programmatic Session Start (Advanced)**: Might involve using `tsh` commands server-side if the app server has `tsh` configured with an identity, or interacting with Teleport's gRPC API to stream session data (more complex).

-   **Listing Nodes/Assets**:
    -   `GET /api/nodes` (via Teleport Proxy, requires auth).

**Note**: Teleport's API for third-party integration for session launching is less about getting a simple "session URL" and more about either redirecting the user to the Teleport environment or using its client tools/SDKs.

## Environment Variables for Configuration

Our FastAPI application will store PAM connection details in environment variables, loaded via `core.config.Settings`:
-   `PAM_API_URL`: Base URL of the PAM system's API (e.g., JumpServer API URL, Teleport Proxy URL).
-   `PAM_API_TOKEN`: API token for JumpServer, or other relevant auth credentials/tokens for Teleport if applicable for the chosen integration method.
