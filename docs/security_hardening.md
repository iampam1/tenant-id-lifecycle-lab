# Security Hardening & Testing Guide

This document outlines key security hardening practices and testing considerations for the Tenant Identity Lifecycle Lab application. While this project is a lab environment, adhering to security best practices is crucial.

## 1. Secrets & Configuration Management

Proper management of secrets and configuration is fundamental to application security. Secrets include API keys, database credentials, JWT secret keys, etc.

### Guiding Principles:

-   **Never Hardcode Secrets**: Secrets must never be hardcoded directly into the source code, Dockerfiles, or committed to version control (Git).
-   **Environment-Specific Configurations**: Different environments (local development, staging, production) will have different configurations (e.g., database URLs, API keys for external services).
-   **Principle of Least Privilege**: Ensure that credentials used by the application (e.g., database user) have only the minimum necessary permissions.

### Implementation in This Project:

1.  **Local Development (`.env` files)**:
    -   Sensitive configurations for local development (like `DATABASE_URL`, `SECRET_KEY`, dummy IGA/PAM keys) are managed using a `.env` file in the project root.
    -   The `.env` file is created by copying `.env.example` and populating it with actual values.
    -   Crucially, the `.env` file itself is listed in `.gitignore` to prevent it from being committed to the Git repository. This was implemented in Phase 5.

2.  **Production-like Environments (e.g., Fly.io)**:
    -   For deployed environments, secrets are managed using the hosting platform's built-in secret management system.
    -   For Fly.io (as documented in Phase 9 - `docs/deployment_fly_io.md`):
        -   Secrets are set using the `fly secrets set VAR_NAME="value"` command (e.g., `fly secrets set SECRET_KEY="..."`).
        -   The `DATABASE_URL` for the Fly.io PostgreSQL instance is automatically set as a secret when the database is attached to the application (`fly postgres attach ...`).
    -   These secrets are injected as environment variables into the running application container by the platform.

3.  **Configuration Loading (`core/config.py`)**:
    -   The FastAPI application uses Pydantic's `BaseSettings` (in `src/app/core/config.py`) to load all configurations, including secrets, from environment variables.
    -   This approach ensures that the application code itself is decoupled from how secrets are provided in different environments. It simply reads from the environment.

### Best Practices Reminder:

-   **Strong, Unique Secrets**: Ensure that all secrets (especially `SECRET_KEY` for JWTs, database passwords) are strong, unique, and randomly generated where possible.
-   **Rotation**: In a real production system, have a policy for rotating secrets periodically, especially if a compromise is suspected.
-   **Access Control**: Limit access to secret management systems (like Fly.io secrets or GitHub Actions secrets) to authorized personnel only.
-   **Audit Secret Access**: If your platform supports it, audit who accesses or modifies secrets.

## 2. Secure JWT Implementation

JSON Web Tokens (JWTs) are used in this application for authenticating API requests after a user logs in. Ensuring their secure implementation is critical.

### Current Implementation Review:

-   **Strong `SECRET_KEY`**:
    -   The JWT signing key (`SECRET_KEY`) is loaded from environment variables via `settings.SECRET_KEY` in `src/app/core/config.py`.
    -   **Responsibility**: It is crucial that a strong, unique, and randomly generated secret key (e.g., 32 bytes or more, generated with `openssl rand -hex 32`) is used in `.env` for local development and set as a secret in production environments (e.g., via `fly secrets set SECRET_KEY=...`).
    -   This key is used by `jose.jwt.encode()` and `jose.jwt.decode()` in `src/app/core/security.py`.

-   **Appropriate Algorithm**:
    -   The `ALGORITHM` used for signing JWTs is defined as "HS256" (HMAC using SHA-256) in `src/app/core/config.py`.
    -   This algorithm is suitable for symmetric key cryptography, where the same `SECRET_KEY` is used for both signing and verifying tokens. This is appropriate for our current setup where the API itself generates and validates tokens.
    -   If asymmetric keys (public/private key pair, e.g., RS256) were needed (e.g., if an external service issued tokens and our app only verified them), the algorithm and key management would differ.

-   **Token Expiration**:
    -   Access tokens have a defined expiration time. This is configured by `ACCESS_TOKEN_EXPIRE_MINUTES` in `src/app/core/config.py` (defaulting to 15 minutes in the example).
    -   The `create_access_token` function in `src/app/core/security.py` correctly sets the `exp` (expiration) claim in the JWT.
    -   The `decode_access_token` function, through `jose.jwt.decode`, automatically validates the `exp` claim and will raise a `JWTError` (e.g., `ExpiredSignatureError`) if the token is expired.
    -   Short-lived access tokens are a good security practice, minimizing the window of opportunity if a token is compromised.

-   **Token Content (`sub` claim)**:
    -   The `create_access_token` function currently uses the user's email as the `sub` (subject) claim of the JWT. This is a common practice.
    -   The `get_current_user` dependency in `src/app/core/dependencies.py` retrieves this `sub` claim to identify and load the user from the database.
    -   **No sensitive information beyond the user identifier (subject) and expiration should be stored directly in the JWT payload unless it's encrypted or the implications are fully understood.** Our current implementation adheres to this by only storing `exp` and `sub`.

-   **Transmission Security (HTTPS)**:
    -   While not part of the JWT itself, tokens must always be transmitted over HTTPS in production to prevent them from being intercepted (Man-in-the-Middle attacks). This is covered in the "HTTPS (TLS) in Production" section. Bearer tokens are sent in the `Authorization` header and are visible if traffic is not encrypted.

### Considerations and Potential Enhancements:

-   **Refresh Tokens**:
    -   Currently, only access tokens are implemented. For scenarios where users need to stay logged in for extended periods without frequently re-entering credentials, a refresh token mechanism is a common pattern.
    -   Refresh tokens are typically longer-lived, stored securely (e.g., HTTPOnly cookie or secure storage), and can be exchanged for new short-lived access tokens.
    -   Implementing refresh tokens would add complexity but improve user experience and can enhance security if done correctly (e.g., refresh token rotation, revocation). This is beyond the scope of the current MVP.

-   **Token Revocation**:
    -   The current JWT implementation does not support immediate server-side revocation of tokens before their expiry (e.g., if a user logs out from all devices or a token is known to be compromised).
    -   True stateless JWTs are difficult to revoke. Solutions involve maintaining a blacklist of revoked tokens (adding state back) or using very short expiry times. This is an advanced feature.

-   **`jti` (JWT ID) Claim**:
    -   Adding a unique identifier (`jti` claim) to each token can help in tracking tokens or implementing some forms of revocation (e.g., if storing `jti`s in a blacklist).

-   **Audience (`aud`) and Issuer (`iss`) Claims**:
    -   For more complex scenarios, especially involving multiple services or token issuers, using `aud` (audience) and `iss` (issuer) claims can provide better token validation and security. These specify who the token is intended for and who issued it.

### Security Best Practices for JWTs:

-   Keep the `SECRET_KEY` confidential and strong.
-   Always use HTTPS.
-   Keep token payloads minimal.
-   Use and validate the `exp` claim.
-   Consider the trade-offs of statelessness vs. the need for features like revocation.

Our current JWT implementation covers the fundamental security aspects for the MVP's requirements.

## 3. Input Validation and Sanitization

Validating and sanitizing all external input is a cornerstone of web application security, crucial for preventing a wide range of vulnerabilities, including injection attacks, data corruption, and denial-of-service.

### Current Implementation & Practices:

1.  **Pydantic for Request Body Validation (FastAPI)**:
    -   Our FastAPI application extensively uses Pydantic models to define the expected schema for request bodies (e.g., `TenantCreate`, `UserCreate`, `UserOnboardRequest`).
    -   When a request comes in, FastAPI automatically validates the incoming JSON payload against the corresponding Pydantic model.
    -   **Benefits**:
        -   **Type Checking**: Ensures that fields are of the correct data type (e.g., `int`, `str`, `bool`, `EmailStr`).
        -   **Constraints**: Pydantic models allow defining constraints like `min_length`, `max_length`, `gt` (greater than), `lt` (less than), regex patterns (via `Field(..., regex="...")`). Examples are used in `tenant_schema.py` and `user_schema.py` (`min_length`, `max_length` for names, `EmailStr` for emails).
        -   **Required Fields**: Automatically checks for the presence of required fields.
        -   **Automatic Error Responses**: If validation fails, FastAPI automatically returns an HTTP 422 "Unprocessable Entity" response detailing the validation errors, preventing invalid data from reaching the application logic.
    -   This significantly reduces the risk of processing malformed or unexpected data and is a primary defense against many injection-style attacks on structured data.

2.  **Path and Query Parameter Validation (FastAPI)**:
    -   FastAPI also performs type validation for path parameters and query parameters based on their Python type hints in the endpoint function signatures.
    -   Additional validation (like `Query(..., min_length=3)`, `Path(...)`) can be added using FastAPI's `Query` and `Path` utility functions if more specific constraints are needed for these parameters. Currently, our application primarily uses path parameters for IDs (which are type-hinted as `int`) and basic query parameters for pagination (`skip`, `limit` as `int`).

3.  **SQLAlchemy ORM for SQL Injection Prevention**:
    -   The application uses SQLAlchemy Object-Relational Mapper (ORM) for all database interactions (e.g., in `tenant_service.py`, `auth_service.py`).
    -   **Benefit**: SQLAlchemy ORM, when used correctly, automatically parameterizes queries. This means user-supplied input is treated as data, not as executable SQL code, effectively preventing SQL injection vulnerabilities.
    -   **Crucial Point**: Avoid constructing raw SQL queries with string formatting or concatenation using user input. Always use the ORM's methods for querying, filtering, and creating/updating records. Our current implementation adheres to this by using methods like `db.query()`, `filter()`, `add()`, `commit()`.

4.  **Output Encoding (Implicit via FastAPI/Jinja2)**:
    -   FastAPI automatically handles JSON serialization for API responses, which correctly encodes data, preventing most JSON-related injection or XSS issues if the frontend interprets the JSON strictly as data.
    -   For HTML templating (Jinja2, as used for the UI in Phase 8), Jinja2 by default performs auto-escaping of variables rendered in templates. This is a critical defense against Cross-Site Scripting (XSS) if user-supplied data is displayed on web pages.
        -   Example: If `{{ user_input }}` is used in a Jinja2 template, special characters like `<`, `>`, `&` will be escaped to `&lt;`, `&gt;`, `&amp;`, respectively.
        -   **Caution**: Developers must be careful not to disable auto-escaping inadvertently (e.g., by using the `|safe` filter in Jinja2 with untrusted data).

### Areas for Vigilance & Future Consideration:

-   **Complex Validation Logic**: For validation rules that go beyond what Pydantic can declaratively define (e.g., inter-field dependencies not easily expressed, complex business rules), custom validation functions (`@validator` in Pydantic) or checks within the service layer are necessary.
-   **File Uploads (Not in current scope)**: If file uploads were to be implemented, they would require careful validation of file types, sizes, and content, as well as secure storage practices.
-   **Rate Limiting**: While not strictly input validation, rate limiting on API endpoints (especially authentication and resource-intensive ones) is crucial to protect against brute-force attacks and denial-of-service. This is typically implemented with middleware (e.g., `slowapi`).
-   **Header Validation**: Depending on the application, validating HTTP headers (e.g., `Content-Type`, custom headers) might be necessary. FastAPI provides ways to define and extract headers.
-   **Regular Expression Denial of Service (ReDoS)**: If using complex regular expressions (e.g., in Pydantic field validation or elsewhere), be mindful of ReDoS vulnerabilities where poorly crafted regexes can lead to excessive CPU usage with certain inputs.

By leveraging FastAPI's Pydantic integration for request validation and SQLAlchemy ORM for database interaction, the application has a strong foundation for input validation and SQLi prevention. Jinja2's auto-escaping helps protect the UI part. Continuous vigilance is needed if new input vectors or data processing methods are introduced.

## 4. HTTPS (TLS) in Production

Encrypting data in transit using HTTPS (HTTP Secure, which relies on TLS - Transport Layer Security) is non-negotiable for any web application that handles sensitive data, including login credentials, session tokens (like JWTs), and personal information.

### Importance of HTTPS:

-   **Confidentiality**: Encrypts the data exchanged between the client (user's browser, API consumer) and the server, preventing eavesdroppers (e.g., on public Wi-Fi) from reading it. This protects sensitive information like passwords, API keys, and personal data.
-   **Integrity**: Ensures that the data has not been tampered with during transit. TLS provides mechanisms to detect any modification of data.
-   **Authentication (Server-side)**: Allows clients to verify the authenticity of the server they are connecting to, by checking its TLS certificate. This helps prevent Man-in-the-Middle (MitM) attacks where an attacker impersonates the server.
-   **Trust and Professionalism**: Browsers visibly mark sites not using HTTPS as "Not Secure," which erodes user trust. HTTPS is a standard expectation.
-   **Compliance**: Many data protection regulations (e.g., GDPR, HIPAA) require or strongly imply the use of encryption for data in transit.

### Implementation in This Project (Production Context):

-   **Local Development**:
    -   Typically, local development (e.g., `uvicorn src.app.main:app --reload`) runs over HTTP (`http://localhost:8000`). This is generally acceptable for local-only development where traffic does not leave the machine.
    -   For more rigorous local testing of HTTPS-related features (like Secure cookies, if used), developers can set up local HTTPS using tools like `mkcert` to generate self-signed certificates.

-   **Production Deployment (e.g., Fly.io)**:
    -   Modern Platform-as-a-Service (PaaS) providers like **Fly.io automatically handle TLS termination** for applications.
    -   When you deploy an application to Fly.io and it's exposed via their routing mesh:
        -   Fly.io provisions and manages TLS certificates (typically from Let's Encrypt) for your application's default hostname (e.g., `your-app-name.fly.dev`).
        -   The `fly.toml` configuration, as set up in our example (`fly.toml.example`), includes:
            ```toml
            [[services.ports]]
              port = 80
              handlers = ["http"]
              force_https = true # Automatically redirects HTTP to HTTPS

            [[services.ports]]
              port = 443
              handlers = ["tls", "http"]
            ```
            This configuration ensures that Fly.io's edge proxies handle incoming port 80 (HTTP) and 443 (HTTPS) traffic, terminate TLS for HTTPS traffic, and then forward the decrypted HTTP traffic to your application running on its internal port (e.g., 8000). The `force_https = true` directive automatically redirects users from HTTP to HTTPS.
    -   **No Application Code Changes Needed for TLS Termination**: Your FastAPI application code continues to run as an HTTP server internally (e.g., Uvicorn listening on port 8000). The TLS handling is done by the platform's infrastructure before traffic reaches your app.

-   **Custom Domains**:
    -   If you configure a custom domain for your Fly.io application (e.g., `lab.yourdomain.com`), Fly.io will also manage TLS certificate issuance and renewal for that custom domain.

-   **External IGA/PAM Services**:
    -   If the IGA or PAM systems that this application integrates with are hosted externally (i.e., not within the same private network or on the same platform), it is **critical** that communications between this application and those external services also occur over HTTPS.
    -   This means the `IGA_API_URL` and `PAM_API_URL` configured for the application must use `https://...` and point to services with valid TLS certificates. The `IgaClient` and `PamClient` (using the `requests` library) will then automatically use TLS for these connections.

### Best Practices:

-   **Always Use HTTPS in Production**: No exceptions for web applications handling any user data or authentication.
-   **Keep TLS Configurations Up-to-Date**: Rely on hosting platforms like Fly.io to manage this, or if managing your own servers, keep your TLS libraries and ciphersuites current.
-   **HSTS (HTTP Strict Transport Security)**: For added security, consider implementing HSTS headers (can often be configured at the edge/CDN level or via middleware). HSTS tells browsers to only communicate with your site over HTTPS, even if a user types `http://`.

By deploying on a platform like Fly.io that handles TLS termination by default, this project adheres to the critical requirement of using HTTPS in production.

## 5. Audit Logging

Comprehensive audit logging is essential for security monitoring, incident investigation, and compliance. Audit logs provide a chronological record of events and actions within the application.

### Current Audit Logging Implementation:

-   **`AuditLog` Model and Table**:
    -   An `AuditLog` SQLAlchemy model (`src/app/models/audit_log.py`) and corresponding `audit_logs` database table were defined in Phase 4 (schema) and Phase 5 (model).
    -   The schema includes:
        -   `id` (PK)
        -   `tenant_id` (FK, nullable)
        -   `user_id` (FK, nullable - user performing the action)
        -   `action_type` (String - e.g., "privilege_session_request_success")
        -   `details` (JSONB - for event-specific data)
        -   `timestamp` (Timestamp with time zone, defaults to current time)

-   **Existing Audit Log Entries**:
    -   **Privilege Session Requests (Phase 7)**: The `POST /lifecycle/privilege` endpoint in `routers/lifecycle_router.py` creates audit log entries for:
        -   Successful requests (`action_type="privilege_session_request_success"`), logging PAM username, target asset, and indication that a URL was provided.
        -   Failed requests where PAM didn't return a URL (`action_type="privilege_session_request_failed"`).
        -   Errors during the request process (`action_type="privilege_session_request_error"`), logging the error message.
    -   **User Offboarding (Phase 7)**: The `POST /lifecycle/offboard` endpoint in `routers/lifecycle_router.py` creates an audit log entry (`action_type="user_offboard_attempt"`) detailing the outcomes of de-provisioning from IGA, PAM, and local app deactivation.

### What Makes a Good Audit Log Entry?

Effective audit logs should capture sufficient detail to reconstruct events and understand actions. Key elements include:

-   **Timestamp**: When the event occurred (accurate, with timezone). (Implemented)
-   **Who**: The actor performing the action. This is typically the authenticated `user_id` and their `tenant_id`. For unauthenticated actions (if any, e.g., failed login attempts before user is known) or system actions, this might be different (e.g., source IP, system principal). (Implemented for authenticated actions)
-   **What**: The type of event or action that occurred (`action_type`). This should be a clear, consistent, and predefined string. (Implemented)
-   **Where**: The component or resource affected (e.g., which tenant's data, which user account was modified). Often part of `details` or derivable from `tenant_id` / `user_id`.
-   **Outcome**: Whether the action was successful or failed. (Implicit in `action_type` like `_success` or `_failed`, or could be a separate `status` field).
-   **Relevant Details (`details` JSONB field)**: Any additional context-specific information that is useful for understanding the event. Examples:
    -   For a failed login: attempted username, source IP.
    -   For a resource modification: fields changed, old/new values (if not too verbose or sensitive).
    -   For an API call to an external system: target system, success/failure of that call. (Partially implemented)

### Areas for Review and Potential Enhancement (Conceptual):

-   **Critical Actions to Audit**: Review all critical API endpoints and business logic flows to ensure they are adequately audited. Consider:
    -   **Authentication Events**:
        -   Successful logins (`POST /auth/login`).
        -   Failed login attempts (could include source IP, attempted username - be mindful of PII).
        -   User registration (`POST /auth/register`).
        -   Logout (if an explicit logout endpoint is implemented).
    -   **Tenant Management**:
        -   Tenant creation (`POST /tenants/`).
        -   Tenant updates (`PUT /tenants/{tenant_id}`).
        -   Tenant deletion (`DELETE /tenants/{tenant_id}`).
    -   **User Management (Application Users)**:
        -   User creation (`POST /users/`).
        -   User updates (e.g., password changes, status changes - if implemented).
        -   User deletion (if implemented).
    -   **Administrative Actions**: Any actions performed by a super-admin that affect system configuration or other tenants.
    -   **Security Events**: Changes to permissions, roles, or security settings.

-   **Consistency**: Ensure `action_type` strings are consistent and well-defined.
-   **Detail Level**: Ensure the `details` field captures enough information without being overly verbose or logging overly sensitive data (e.g., raw passwords should never be logged).
-   **Log Integrity and Security**:
    -   In a production system, consider how audit logs are protected from tampering or unauthorized access. This might involve shipping logs to a separate, secure log management system (e.g., ELK stack, Splunk).
    -   Database-level permissions for the `audit_logs` table should be restrictive for the application user (e.g., only INSERT allowed, no UPDATE/DELETE).
-   **Log Review and Alerting**: Audit logs are most useful if they are regularly reviewed and if alerts are set up for suspicious or critical events. This is typically handled by external monitoring and SIEM (Security Information and Event Management) systems.

The current audit logging provides a good start for key lifecycle events. Expanding it to cover other sensitive operations as listed above would further enhance the application's security posture and traceability.

## 6. PAM Session Cleanup (Conceptual Best Practices)

While our application requests privileged sessions via a Privileged Access Management (PAM) system, the actual lifecycle management of these sessions (e.g., timeouts, termination, recording) is primarily a responsibility of the PAM tool itself (JumpServer, Teleport, etc.). Our application's role is generally to initiate the request.

### Key Concepts for PAM Session Security:

-   **Session Timeouts**:
    -   PAM systems should be configured with session timeout policies. This includes:
        -   **Idle Timeouts**: Automatically terminate a session if there's no activity for a specified period (e.g., 15-30 minutes). This prevents sessions from being left open indefinitely on unattended workstations.
        -   **Maximum Session Duration**: Enforce a maximum total duration for any privileged session (e.g., 8 hours), after which the user must re-authenticate or re-request access.
    -   **Configuration Location**: These settings are configured directly within the PAM system's administration interface or configuration files (e.g., in JumpServer's settings, or Teleport's role definitions/session controls).

-   **Short-Lived Credentials/Certificates (Especially Teleport)**:
    -   PAM systems like Teleport operate on the principle of short-lived certificates for access. When a user starts a session, Teleport issues a certificate with a limited Time-To-Live (TTL), e.g., a few minutes to a few hours.
    -   Once the certificate expires, the session automatically terminates, and the user must re-authenticate with Teleport to get a new certificate. This significantly reduces the risk associated with compromised session credentials.

-   **Session Recording and Monitoring**:
    -   Most enterprise-grade PAM solutions offer session recording (video and/or command logs). This is crucial for:
        -   **Auditing**: Reviewing actions performed during privileged sessions.
        -   **Forensics**: Investigating security incidents.
        -   **Compliance**: Meeting regulatory requirements.
    -   Configuration for session recording, storage, and retention is managed within the PAM tool.

-   **Manual Session Termination**:
    -   PAM administrators should have the ability to manually view active sessions and terminate any suspicious or no-longer-needed sessions directly from the PAM console.

-   **Concurrent Session Control**:
    -   Some PAM systems allow policies to limit the number of concurrent privileged sessions a user can have.

### Application's Role:

-   **Initiation**: Our FastAPI application, via the `PamClient` and the `/lifecycle/privilege` endpoint, initiates the request for a session. It receives a session URL or ticket.
-   **No Direct Session Management**: Our application typically does **not** directly manage the active session's lifecycle (keep-alives, termination signals) within the PAM system once the session is established via the provided URL. The user interacts directly with the PAM's web terminal or gateway.
-   **Secure Handling of Session URL/Ticket**: If a session URL or ticket is returned to our application and then to the user, it should be treated as sensitive, temporary information.

### Recommendations for This Project (Conceptual):

-   **Documentation**: When setting up the chosen PAM tool (JumpServer or Teleport) for the lab environment (even conceptually), document where and how to configure:
    -   Idle session timeouts.
    -   Maximum session durations (if applicable).
    -   Certificate TTLs (for Teleport).
-   **User Guidance**: If providing a UI, remind users to explicitly log out of privileged sessions when finished, even if timeouts are in place.

By relying on the robust session management capabilities built into dedicated PAM tools, we avoid having to implement complex session control logic within our application and leverage security features designed for privileged access.

## 7. Periodic Access Reviews (Manual Process for MVP)

Periodic access reviews are a critical governance process to ensure that users only have the permissions they currently need (principle of least privilege) and that access for former employees or users who have changed roles is revoked in a timely manner.

### Current Implementation (MVP - Manual Review Support):

-   **API Endpoint for Data Retrieval**:
    -   The `GET /api/v1/lifecycle/review` endpoint (implemented in Phase 7) provides data for manual access reviews.
    -   When called by an authenticated tenant administrator, this endpoint (conceptually) queries the integrated IGA system (via `IgaClient.get_users_and_roles_for_tenant()`) for users within that administrator's tenant and their assigned roles/entitlements in the IGA system.
    -   The response includes a list of users and their roles, along with a timestamp.

-   **User Interface for Display**:
    -   The `GET /ui/lifecycle/review` page (implemented in Phase 8) calls the backend API endpoint and displays this information in a table format.
    -   This UI allows a tenant administrator to view the current state of user access (as reported by the IGA system) for their tenant.

-   **Manual Review Process**:
    -   The current MVP supports a **manual review process**:
        1.  A tenant administrator navigates to the "Access Review Data" page in the UI.
        2.  They review the list of users and their assigned roles/entitlements.
        3.  If any access is deemed inappropriate or no longer necessary, the administrator must **manually take action** to revoke that access.
            -   This might involve using the IGA system's own administration console directly.
            -   Or, if our application were to be extended, it could include API endpoints that call `IgaClient.revoke_role_from_user()` or similar functions to programmatically request changes in the IGA system based on the review. (This extension is not part of the current MVP's direct functionality from the review page itself).

### Importance and Goals of Access Reviews:

-   **Adherence to Least Privilege**: Regularly verify that users do not have excessive permissions beyond what their current job role requires.
-   **Identify Orphaned Accounts**: Detect accounts for users who have left the organization or changed roles and no longer need access.
-   **Detect Privilege Creep**: Notice if users have accumulated unnecessary permissions over time.
-   **Compliance**: Many regulatory frameworks (e.g., SOX, HIPAA, PCI DSS) require periodic access reviews.
-   **Security Posture**: Reducing unnecessary access minimizes the potential attack surface and the impact of a compromised account.

### Future Considerations for Automation (Beyond MVP):

-   **Automated Certification Campaigns**: Full-featured IGA systems (like midPoint or Syncope) often have built-in capabilities for running automated access certification campaigns. These campaigns can:
    -   Automatically assign review tasks to managers or application owners.
    -   Track review progress and decisions (approve, revoke, delegate).
    -   Generate reports for auditors.
    -   Potentially trigger automated de-provisioning actions based on review outcomes.
-   **Integration with IGA Campaigns**: Our application could, in the future, integrate with such IGA campaign features, perhaps by initiating campaigns or pulling review task statuses.

For the MVP, providing the data for a manual review is a valuable first step in enabling better access governance. Tenant administrators are advised (e.g., in documentation or training) to perform these reviews regularly.

## 8. Basic Penetration Testing Concepts (MVP)

While a comprehensive penetration test by security professionals is beyond the scope of this lab project's MVP, developers (and informed testers/interviewers) can perform some basic conceptual checks to probe for common vulnerabilities. This is about fostering a security-aware mindset.

**Disclaimer**: These are not exhaustive tests and do not guarantee security. They are simple checks based on common issues.

### a. Authorization Bypass / Multi-Tenancy Checks

-   **Concept**: Verify that users cannot access or modify data belonging to other tenants, or perform actions they are not authorized for.
-   **Test Ideas**:
    1.  **Tenant Data Isolation**:
        -   Log in as an administrator for `TenantA`. Note the `tenant_id` for `TenantA`.
        -   Attempt to use API endpoints to access resources that should be specific to `TenantB` by guessing or obtaining `TenantB`'s `tenant_id` or specific resource IDs from `TenantB`.
            -   Example: Call `GET /api/v1/tenants/{tenantB_id}` or `GET /api/v1/users/` (if this endpoint were to list users for a *specified* tenant_id in query params, which it currently doesn't; our `GET /users/` lists for current user's tenant).
            -   More relevant: If an endpoint like `GET /api/v1/users/{user_id_from_tenantB}` existed, try to access it.
        -   **Expected Outcome**: The API should return HTTP 403 (Forbidden) or HTTP 404 (Not Found, to avoid information disclosure about resource existence). Our current basic check in `user_router.py` for `POST /users/` (creating user in another tenant) and commented-out examples in `tenant_router.py` aim for this.
    2.  **Privilege Escalation**:
        -   Are there different user roles (e.g., tenant admin vs. regular user within a tenant, though not fully implemented yet)?
        -   Log in as a lower-privileged user. Attempt to access API endpoints or perform actions that should be restricted to higher-privileged users (e.g., a regular user trying to call `POST /api/v1/users/` to create another user).
        -   **Expected Outcome**: HTTP 403 (Forbidden). (Requires role-based access control (RBAC) to be more fully implemented).

### b. JWT Token Manipulation

-   **Concept**: Test how the application handles invalid, expired, or tampered JWTs.
-   **Test Ideas**:
    1.  **Access without Token**: Attempt to call a protected API endpoint (e.g., `GET /api/v1/tenants/`) without an `Authorization` header.
        -   **Expected Outcome**: HTTP 401 (Unauthorized) or 403 (Forbidden), as per FastAPI's `OAuth2PasswordBearer` default behavior.
    2.  **Invalid Token**: Send a malformed JWT or a JWT signed with a different secret key.
        -   **Expected Outcome**: HTTP 401 (Unauthorized). The `decode_access_token` function should catch `JWTError`.
    3.  **Expired Token**:
        -   Obtain a valid token. Wait for it to expire (based on `ACCESS_TOKEN_EXPIRE_MINUTES`).
        -   Attempt to use the expired token to access a protected endpoint.
        -   **Expected Outcome**: HTTP 401 (Unauthorized).
    4.  **Token Payload Tampering (Conceptual)**: If the token were to contain role information directly in its payload (which ours currently does not for roles, only 'sub'), an attacker might try to modify the payload to escalate privileges.
        -   **Defense**: JWT signature validation (already in place via `jose.jwt.decode`) prevents this, as any payload modification invalidates the signature if the attacker doesn't know the `SECRET_KEY`.

### c. Input Validation & Basic Injection Checks (Conceptual)

-   **Concept**: Test how the application handles unexpected or malicious input, particularly for query parameters or path parameters if they are used in sensitive ways.
-   **Test Ideas**:
    1.  **Path/Query Parameter Type Coercion**:
        -   If an endpoint expects an integer ID in the path (e.g., `/tenants/{tenant_id}`), try sending non-integer values (e.g., `/tenants/abc`, `/tenants/1;DROP TABLE users`).
        -   **Expected Outcome**: FastAPI's automatic validation based on type hints should return HTTP 422 (Unprocessable Entity) for type mismatches. SQLAlchemy ORM prevents SQLi from such path parameters if they were somehow passed to DB layer improperly.
    2.  **Testing `details` JSON fields**:
        -   For endpoints that accept JSON in the `details` field of an audit log or `config_json` for tenants, try sending malformed JSON or excessively large JSON payloads.
        -   **Expected Outcome**: Pydantic/FastAPI should handle malformed JSON (HTTP 422). For large payloads, server-level protections (e.g., request size limits in a reverse proxy like Nginx/Traefik, or in Uvicorn/Hypercorn if configured) would be the primary defense against DoS.
    3.  **SQL Injection (via ORM)**:
        -   As noted in "Input Validation and Sanitization," the use of SQLAlchemy ORM is the primary defense against SQL injection. Direct testing for SQLi against ORM-based operations is usually about verifying that no raw SQL is constructed with user input.
        -   One could try typical SQLi payloads in Pydantic schema string fields, but Pydantic validation and the ORM should prevent these from reaching the database as executable SQL. The values would be treated as literal strings.

### d. Checking Security Headers (Conceptual)

-   **Concept**: Inspect HTTP response headers for common security headers.
-   **Test Ideas**:
    -   Use browser developer tools or `curl -I` to check responses from the application.
    -   Look for headers like:
        -   `Strict-Transport-Security` (HSTS): Enforces HTTPS. (Usually set at edge/proxy).
        -   `X-Content-Type-Options: nosniff`: Prevents MIME-type sniffing.
        -   `X-Frame-Options: DENY` or `SAMEORIGIN`: Protects against clickjacking.
        -   `Content-Security-Policy` (CSP): Helps prevent XSS and other code injection attacks.
    -   **Note**: Many of these are best set by a reverse proxy (Nginx, Traefik) or at the edge CDN, or via ASGI middleware in FastAPI for headers like `X-Content-Type-Options`. Fly.io's `force_https = true` helps with HSTS-like behavior.

These basic checks can help build confidence but are not a substitute for a formal security testing process for a production application.
