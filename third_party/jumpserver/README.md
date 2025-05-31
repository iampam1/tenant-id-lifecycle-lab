# JumpServer PAM - Installation and Setup (Conceptual)

This directory is intended to hold documentation and configuration examples related to setting up JumpServer, a Privileged Access Management (PAM) solution.

## 1. Obtain JumpServer

JumpServer is typically installed by cloning its official repository.

```bash
# Conceptual command:
# git clone https://github.com/jumpserver/jumpserver.git third_party/jumpserver
```
For this project, we will be documenting the setup conceptually. If you were setting it up, you would clone the actual JumpServer code into a directory like this.

## 2. Prerequisites

-   **Docker**: JumpServer heavily relies on Docker for its deployment. Ensure Docker is installed and running on your system.
-   **Docker Compose**: Docker Compose is used to orchestrate the multiple containers required by JumpServer (e.g., JumpServer application, database, cache). Ensure Docker Compose is installed.

## Next Steps

The following aspects will be covered in further documentation:
-   Configuring JumpServer (`config.yml`)
-   Setting up the environment with Docker Compose (`docker-compose.yml`)
-   Accessing the JumpServer UI
-   Basic JumpServer configuration (Assets, Users)

## 3. Configure JumpServer (`config.yml`)

JumpServer's main configuration is typically managed through a `config.yml` file. When you clone the JumpServer repository, you would usually find a sample configuration file (e.g., `config_example.yml`) that you would copy and rename to `config.yml` at the root of the JumpServer directory structure (or as specified by its documentation).

Key settings to define in `config.yml` include:

-   **Database Connection:**
    -   `DB_ENGINE`: Specifies the database engine. JumpServer defaults to `mysql`, but `postgres` can also be used.
        -   Example: `DB_ENGINE: mysql`
    -   `DB_HOST`: The hostname or IP address of the database server. If using Docker Compose as recommended, this will be the service name of the MySQL/PostgreSQL container (e.g., `mysql` or `postgres`).
        -   Example: `DB_HOST: mysql`
    -   `DB_PORT`: The port number for the database server.
        -   Example: `DB_PORT: 3306` (for MySQL)
    -   `DB_USER`: The username for connecting to the database.
        -   Example: `DB_USER: jm`
    -   `DB_PASSWORD`: The password for the database user.
        -   Example: `DB_PASSWORD: jm_pwd`
    -   `DB_NAME`: The name of the database JumpServer will use.
        -   Example: `DB_NAME: jumpserver`

-   **Redis Connection (for caching and task queues):**
    -   `REDIS_HOST`: Hostname of the Redis server (e.g., `redis` if using Docker Compose).
        -   Example: `REDIS_HOST: redis`
    -   `REDIS_PORT`: Port for Redis.
        -   Example: `REDIS_PORT: 6379`
    -   `REDIS_PASSWORD`: Password for Redis (if configured).

-   **Other Important Settings:**
    -   `SECRET_KEY`: A long, random string used for cryptographic signing. **This must be changed to a secure value.**
    -   `LOG_LEVEL`: Logging verbosity (e.g., `INFO`, `DEBUG`).
    -   `SESSION_COOKIE_AGE`, `CSRF_COOKIE_AGE`: Session and CSRF token lifetimes.

**Note:** The exact path for `config.yml` and all available options should be verified against the official JumpServer documentation for the version you are using. For this project, we are creating a conceptual understanding. You would typically create/edit this file in your local JumpServer clone.

## 4. Docker Compose Setup

JumpServer is designed to run as a set of orchestrated Docker containers. The setup typically uses a `docker-compose.yml` file to define and manage these services. An example (`docker-compose.example.yml`) is provided in this directory, based on the project issue description.

### Key Services in `docker-compose.yml`:

-   **`mysql` (or `postgres`):**
    -   The database service for JumpServer.
    -   The example uses `mysql:5.7`.
    -   Environment variables within this service definition set up the initial database (`jumpserver`), user (`jm`), and passwords.
    -   **Important**: For production, passwords should be managed securely (e.g., Docker secrets, environment files not committed to Git).
-   **`redis`:**
    -   A Redis instance used for caching and as a message broker for background tasks.
    -   The example uses `redis:6`.
-   **`jumpserver`:**
    -   The main JumpServer application container.
    -   The `build: .` line suggests that if you have the JumpServer source code, Docker Compose will build the JumpServer image using a `Dockerfile` located in the root of the JumpServer source directory. Alternatively, you might use a pre-built image from Docker Hub (e.g., `jumpserver/jms:latest`).
    -   The `command` specifies how to start the JumpServer application within the container.
    -   Environment variables are passed to the JumpServer container to configure its connection to the database (`DB_HOST: mysql`) and Redis (`REDIS_HOST: redis`), matching the service names defined in the Docker Compose file.
    -   It `depends_on` `mysql` and `redis` to ensure these services start before JumpServer attempts to connect.
    -   Ports are exposed (e.g., `8080:8080`) to make the JumpServer web UI accessible from the host machine.
    -   Volumes can be added for data persistence (e.g., JumpServer data, logs), which is crucial for production-like environments.

### Running JumpServer with Docker Compose:

1.  Navigate to the directory containing the `docker-compose.yml` file (i.e., the root of your JumpServer clone).
2.  Ensure `config.yml` is correctly set up (though many settings can be passed via environment variables in `docker-compose.yml` as shown in the example).
3.  Start the services:

    ```bash
    # If using the example file, you might rename it or specify it:
    # cp docker-compose.example.yml docker-compose.yml
    docker-compose up -d
    ```
    The `-d` flag runs the containers in detached mode (in the background).

4.  To check logs: `docker-compose logs -f jumpserver`
5.  To stop services: `docker-compose down`

## 5. Accessing JumpServer UI and Initial Steps

Once JumpServer is running (e.g., via Docker Compose), you can access its web user interface.

-   **Default URL**:
    Open your web browser and navigate to:
    `http://localhost:8080`
    (This assumes the port mapping `8080:8080` is used in your `docker-compose.yml` for the `jumpserver` service).

-   **Default Admin Credentials**:
    -   Username: `root`
    -   Password: `admin123`

-   **IMPORTANT**:
    -   **Change Default Credentials Immediately**: After your first login, it is crucial to change the default administrator password to a strong, unique password to secure your JumpServer instance.
    -   **Initial Setup Wizard**: JumpServer might guide you through an initial setup wizard on your first login to configure basic settings. Follow the on-screen instructions.

## 6. Basic PAM Configuration (Conceptual)

After setting up JumpServer and logging in as an administrator, you can begin basic PAM configuration.

### a. Create a Test "Asset"

Assets in JumpServer represent the servers, network devices, databases, or applications that users will access through JumpServer.

**Conceptual Steps to Add an Asset (e.g., a Linux Host):**

1.  **Navigate to "Assets"**: In the JumpServer UI, find the section for managing assets (e.g., "Asset Management" > "Assets").
2.  **Add New Asset**: Click the option to create a new asset.
3.  **Asset Details**:
    -   **Name**: A descriptive name for the asset (e.g., `Test_Linux_VM`).
    -   **IP Address/Hostname**: The actual IP address or resolvable hostname of the target machine.
    -   **Platform**: Select the operating system or type (e.g., `Linux`).
    -   **Protocols**: Enable the protocols you want to use for connecting (e.g., `SSH`).
    -   **Port**: Specify the port for the selected protocol (e.g., `22` for SSH).
4.  **Accounts (System Users on the Asset)**:
    -   You need to define how JumpServer will authenticate to the asset itself. This usually involves adding "System Users" (accounts that exist on the target asset).
    -   For example, add a system user like `ssh_user` with its password or SSH key that JumpServer can use to log into the `Test_Linux_VM`.
    -   Alternatively, you can configure JumpServer to prompt the end-user for credentials for the target asset.
5.  **Save the Asset**.

### b. Create a Test "User" (JumpServer User)

These are the users who will log into JumpServer to access the configured assets.

**Conceptual Steps to Add a JumpServer User:**

1.  **Navigate to "Users"**: In the JumpServer UI, find the section for user management (e.g., "User Management" > "Users").
2.  **Add New User**: Click to create a new user.
3.  **User Details**:
    -   **Username**: The username for logging into JumpServer (e.g., `pam_tester`).
    -   **Name**: Full name of the user.
    -   **Email**: User's email address.
    -   **Password**: Set an initial password for the JumpServer user.
    -   **Roles/Groups**: Assign appropriate roles or groups that define what this user can do within JumpServer (e.g., a role that grants access to specific assets).
4.  **Save the User**.

### c. Grant Asset Permissions to User

1.  **Navigate to "Permissions"** (or similar section, e.g., "Asset Permissions", "Authorization Rules").
2.  **Create a New Permission Rule**:
    -   Define which JumpServer user(s) or group(s) (`pam_tester`).
    -   Can access which asset(s) (`Test_Linux_VM`).
    -   Using which system user(s) on the asset (e.g., the `ssh_user` you defined for the asset).
    -   And via which protocols (e.g., `SSH`).
3.  **Save the Permission Rule**.

### d. Verification

-   Log out from JumpServer as admin and log back in as the new JumpServer user (`pam_tester`).
-   The `pam_tester` should now see the `Test_Linux_VM` asset available.
-   Attempt to connect to the asset (e.g., open a browser-based SSH session).
-   JumpServer should proxy the connection to the target asset. If successful, you've verified the basic PAM flow.
