# midPoint Installation

This directory is intended to hold the midPoint IGA platform.

## Download

- Download the latest midPoint distribution (Community Edition) from [https://evolveum.com/downloads/midpoint/](https://evolveum.com/downloads/midpoint/).
- Unzip the distribution into this directory (`third_party/midpoint`).

## Prerequisites

- Java 11+ must be installed and available in your system's PATH.

## Next Steps

1.  Configure a PostgreSQL database for midPoint.
2.  Update midPoint configuration files (`midpoint.properties` or `ctx-repo.xml` found typically in `var/` after first run, or to be created from template) to point to the database.
3.  Adjust `midpoint.home` if necessary (usually points to the `var` directory within the midPoint installation).
4.  Start midPoint using the scripts provided in its `bin` directory (e.g., `./midpoint.sh start`).

## Starting and Accessing midPoint

### Starting midPoint

1.  Navigate to the root directory of your midPoint installation (e.g., `cd third_party/midpoint/midpoint-x.y.z`).
2.  Ensure your configuration (database connection, `midpoint.home`) is correctly set up.
3.  Use the provided shell script to start midPoint. This script is usually located in a `bin` directory within the midPoint distribution.

    ```bash
    # Example command, actual path might vary
    ./bin/midpoint.sh start
    # or on Windows:
    # .in\midpoint.bat start
    ```

4.  **Monitor Logs**: Check the midPoint logs (usually in `midpoint.home/var/log/midpoint.log` or console output) for startup messages. Look for messages indicating that midPoint has started successfully (e.g., "MidPoint started").

### Accessing the midPoint Web UI

-   Once midPoint has started, you can typically access its web administration interface at:
    **`http://localhost:8080/midpoint`**

-   **Default Credentials**:
    -   Username: `administrator`
    -   Password: `5ecr3t`

-   **IMPORTANT**: Change the default administrator password immediately after your first login for security reasons!
