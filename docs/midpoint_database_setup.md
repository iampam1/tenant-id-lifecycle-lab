# midPoint Database Setup (PostgreSQL)

midPoint requires a PostgreSQL database for its operations. Below are the conceptual steps and example SQL commands to set up the database.

## Prerequisites

- PostgreSQL server installed and running.
- Access to a PostgreSQL client (e.g., `psql`) or a GUI tool (e.g., pgAdmin).

## Steps

1.  **Connect to PostgreSQL**:
    Connect to your PostgreSQL server as a superuser (or a user with database creation privileges).

    ```bash
    psql -U postgres
    ```

2.  **Create the Database**:
    Create a new database for midPoint. The issue suggests `midpoint_db`.

    ```sql
    CREATE DATABASE midpoint_db;
    ```

3.  **Create a Database User**:
    Create a dedicated user for midPoint to access this database. The issue suggests `midadmin`. **Remember to use a strong, unique password in a real environment.**

    ```sql
    CREATE USER midadmin WITH PASSWORD 'your_strong_password_here';
    ```

4.  **Grant Privileges**:
    Grant the newly created user all necessary privileges on the `midpoint_db` database.

    ```sql
    GRANT ALL PRIVILEGES ON DATABASE midpoint_db TO midadmin;
    ```

    *Note: For enhanced security in a production environment, you might grant more restrictive privileges once midPoint has created its schema, but `ALL PRIVILEGES` is common for initial setup.*

5.  **Verify Connection (Optional but Recommended)**:
    You can test if the new user can connect to the database:

    ```bash
    psql -U midadmin -d midpoint_db -h localhost
    ```
    You should be prompted for the password and then successfully connect.

## Next Steps

- Once the database and user are created, you will need to configure midPoint's properties file (e.g., `midpoint.properties` or `ctx-repo.xml`) to use these connection details (hostname, port, database name, username, and password).
