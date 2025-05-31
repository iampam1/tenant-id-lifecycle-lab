# midPoint Basic IGA Configuration (Conceptual)

This document outlines the conceptual steps for basic IGA configurations within midPoint, as relevant to the Tenant Identity Lifecycle Lab project.

## 1. Tenant / Domain Handling in midPoint

midPoint is inherently designed with multi-tenancy capabilities, often implemented through **Organizations** or **Organizational Units (OUs)**.

-   **Organizations as Tenants**: You can represent each tenant in your lab as a top-level Organization within midPoint.
    -   Users, roles, resources, and policies can then be scoped to these specific organizations.
    -   This provides strong isolation between tenants.

-   **Attributes for Tenant Partitioning (Simpler MVP Approach)**:
    -   For a simpler Minimum Viable Product (MVP) where full organizational separation might be complex to manage initially, a single midPoint instance could be used.
    -   Tenants could be distinguished by a custom **attribute** on user objects (e.g., `tenant_id` or `tenant_name`).
    -   Policies and views would then need to be carefully crafted to filter and apply based on this tenant attribute.
    -   The project issue suggests: "For MVP, you might run one midPoint instance and partition each tenant by an attribute."

-   **Separate midPoint Instances (Maximum Isolation)**:
    -   Another approach, offering the highest isolation, is to run a completely separate midPoint instance for each tenant.
    -   This increases infrastructure overhead (each instance needs its own database, configuration, etc.) but provides clear boundaries.
    -   The project issue mentions: "If using midPoint, decide to either: Host multiple midPoint instances (one per tenant)... or Use a single midPoint instance with a custom “tenant” attribute field. For MVP, separate instances are easier [to conceptualize for IGA data separation, though perhaps not for initial app dev]."

**For this lab's initial Python web application development (Phase 5+), we will likely assume a single midPoint instance where tenant identification might be via API interaction context or attributes, deferring full organizational setup in midPoint itself unless specifically dived into.** The Python app will manage tenant records in its own database.

### Steps (Conceptual for using Organizations):

1.  **Log in to midPoint UI** as `administrator`.
2.  Navigate to the **Organizations** section.
3.  Create a new top-level organization for each tenant (e.g., `Tenant_A`, `Tenant_B`).
    -   Define basic properties for each organization.
4.  When creating users or other resources, assign them to the appropriate tenant organization.


## 2. Create a Sample Connector (Conceptual)

A core function of an IGA system is to connect to various target systems (applications, databases) to manage identities within them. For this lab, we'll conceptualize connecting to a test PostgreSQL database.

### Target System Example: `target_app_db`

-   Assume you have another PostgreSQL database named `target_app_db`.
-   This database contains a table, for example, `users_table` with columns like `id`, `username`, `email`, `status`.

### Steps to Configure a JDBC Connector (Conceptual):

1.  **Log in to midPoint UI** as `administrator`.
2.  Navigate to **Resources** and choose to create a new resource.
3.  **Select Connector Type**:
    -   midPoint offers various connectors. For a SQL database, you would typically use a **JDBC Connector** (e.g., `ConnId org.identityconnectors.databasetable.DatabaseTableConnector`).
4.  **Configure Connector Parameters**:
    -   **Connection Details**:
        -   JDBC URL: `jdbc:postgresql://hostname:port/target_app_db`
        -   Username: A user with R/W access to `target_app_db` (e.g., `target_db_user`)
        -   Password: Password for `target_db_user`
        -   Database Table: `users_table` (the table to provision to)
        -   Primary Key: `id` (or the name of the primary key column in `users_table`)
    -   **Synchronization Settings**: Define how often midPoint should check for changes (e.g., reconciliation, live sync).
    -   **Schema Handling**:
        -   Trigger midPoint to discover the schema of `users_table`.
        -   Define which attributes from midPoint (e.g., `name`, `givenName`, `familyName`, `emailAddress`) map to which columns in `users_table` (e.g., `username`, `email`).
        -   Specify how to handle unique identifiers and passwords (e.g., password hashing or direct mapping if the target system handles it).
5.  **Define Resource Object Type**:
    -   Map a midPoint "User" object (or a specific persona/archetype) to the `users_table`.
    -   Define attribute mappings:
        -   `midPointUser.name` → `users_table.username`
        -   `midPointUser.emailAddress` → `users_table.email`
        -   `midPointUser.activation.administrativeStatus` → `users_table.status` (e.g., 'enabled' maps to 'active')
6.  **Test the Connector**:
    -   midPoint usually provides a "Test Connection" feature.
    -   Attempt to fetch a few accounts from `target_app_db` if any exist.
7.  **Enable the Resource**:
    -   Once configured and tested, enable the resource for provisioning and reconciliation.

### Validation:

-   After setting up the connector and mappings, creating a new user in midPoint (and assigning them to be provisioned to this resource) should result in a corresponding new row appearing in the `users_table` within `target_app_db`.
-   Updating a user in midPoint should update the corresponding row.
-   Deleting or disabling a user in midPoint should delete or disable the row (based on configuration).


## 3. Define a Test Role / Policy (Conceptual)

Roles in midPoint are fundamental for governing access. They group entitlements and can be assigned to users, often triggering provisioning actions to target systems.

### Objective:

-   Create a basic role (e.g., `standard_user`).
-   This role, when assigned to a user, should ensure the user is provisioned to the `target_app_db` (configured via the sample JDBC connector).

### Steps to Create and Assign a Role (Conceptual):

1.  **Log in to midPoint UI** as `administrator`.
2.  Navigate to **Roles**.
3.  **Create a New Role**:
    -   Name: `standard_user`
    -   Description: "Standard user role with basic access to target_app_db."
    -   Type: Typically an "Application Role" or a generic role.
4.  **Configure Role Entitlements/Constructions**:
    -   This is where you link the role to the provisioning resource.
    -   Add a **Construction** (or sometimes called an "Inducement" or "Policy Rule" depending on midPoint version/terminology) to the role.
    -   In this construction:
        -   Specify the **Resource**: Select the JDBC connector resource created for `target_app_db`.
        -   Define the **Object Type**: `Account` (or the name you gave the mapped object type for `users_table`).
        -   **Intent**: Define the intended state or attributes for users who get this role on this resource. For simple provisioning, this might just be "active" or ensure the account exists.
        -   Optionally, assign specific attributes or default values that should be set on the target system account when this role is assigned (e.g., a default group membership within the target application if the connector supports it).
5.  **Assign the Role to a Test User**:
    -   Create a new test user in midPoint (e.g., `test_standard_user`).
    -   Assign the `standard_user` role to this user.
    -   If you are using Organizations for multi-tenancy, ensure the user and the role assignment are within the correct tenant context if applicable.
6.  **Verify Provisioning**:
    -   After assigning the role, check the `users_table` in `target_app_db`.
    -   The `test_standard_user` should now be provisioned to this table as a result of the role assignment and the connector configuration.
    -   Check midPoint logs for any errors or confirmation of the provisioning event.
    -   Revoking the role should de-provision or disable the account in `target_app_db` (based on policy).

### Policy Considerations:

-   midPoint's policy engine is powerful. You can define:
    -   **Assignment Policies**: Control who can be assigned which roles (e.g., users in Tenant_A can only be assigned Tenant_A_roles).
    -   **Synchronization Policies**: How changes from the target system are reconciled back into midPoint.
    -   **Lifecycle Policies**: Define what happens at different stages of a user's lifecycle (e.g., pre-provisioning, de-provisioning).


## 4. Set Up Self-Service Registration (Conceptual - Optional MVP)

Allowing end-users to request accounts through a self-service portal can streamline onboarding. midPoint can support this, typically involving forms and approval workflows.

### Objective:

-   Create a simple mechanism for users to request an account.
-   Implement a basic approval workflow (manual approval by an administrator for MVP).

### Conceptual Steps:

1.  **Identify or Create a User "Persona" for Registration**:
    -   Often, self-service registration creates users of a specific type or with a default set of initial roles (e.g., "unverified_user" or "guest_access_requestor").
2.  **Design a Registration Form**:
    -   midPoint's UI customization capabilities (or integration with external form builders) would be used.
    -   The form should collect necessary information (e.g., First Name, Last Name, Email, desired Username, justification).
3.  **Configure a "Registration" Object or Task in midPoint**:
    -   This might involve creating a specific object type in midPoint to represent a registration request or using a generic task/workflow feature.
4.  **Implement an Approval Workflow**:
    -   For an MVP, this could be a very simple workflow:
        -   User submits the registration form.
        -   A task is created in midPoint and assigned to an administrator (e.g., member of an "Account Approvers" role).
        -   The administrator reviews the request in the midPoint UI.
        -   The administrator can approve or reject the request.
    -   midPoint has a powerful workflow engine (often based on Activiti or similar BPMN engines) that can be used for more complex multi-step approvals, notifications, etc.
5.  **Post-Approval Actions**:
    -   If **approved**:
        -   A new user account is created in midPoint with the details from the form.
        -   Initial roles (e.g., `standard_user`, or a more limited "pending_verification" role) are assigned.
        -   Provisioning to target systems (like `target_app_db`) occurs based on these roles.
        -   The user might receive an email notification.
    -   If **rejected**:
        -   The request is closed.
        -   Optionally, the requestor receives a notification.
6.  **Expose the Registration Form**:
    -   Make the registration form accessible, potentially through a link on the midPoint login page or a dedicated portal page.

### Considerations for MVP:

-   **Manual Approval**: Relying on an administrator to manually approve requests via the midPoint task list is sufficient for an MVP.
-   **Basic Form**: A simple form collecting essential user attributes.
-   **Limited Roles**: Assign only very basic roles upon approval.

This functionality, while powerful, adds complexity. For the initial phases of the Tenant Identity Lifecycle Lab focused on the Python web app interacting with established IGA users, full self-service registration via midPoint might be deferred. However, understanding this capability is important for a complete IGA picture.
