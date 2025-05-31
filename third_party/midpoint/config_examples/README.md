# midPoint Configuration Examples

This directory contains example placeholder files for configuring midPoint.

## `midpoint-example.properties`

This file shows examples of common properties that need to be configured for midPoint, especially the database connection details (`spring.datasource.*`) and potentially the `midpoint.home` directory.

### Important Notes:

1.  **Actual File Name & Location**: The primary configuration file for midPoint might be `midpoint.properties`, `config.xml`, or `ctx-repo.xml` (for repository settings). Its location can vary:
    *   It might be in the main midPoint directory.
    *   It might be expected in a subdirectory like `var/` (which midPoint might create on its first run).
    *   You might need to copy a template file provided by midPoint (e.g., `midpoint.properties.example`) to the correct location and rename it.
2.  **`midpoint.home`**: This property defines the directory where midPoint stores its runtime data, including logs, embedded database (if used), and other operational files. It's crucial to set this correctly. Often, it's set to a `var` directory within or outside the main midPoint installation path.
3.  **Database Connection**: Ensure the `spring.datasource.*` properties (or equivalent XML configuration for `ctx-repo.xml`) correctly point to the PostgreSQL database you set up (`midpoint_db`, user `midadmin`, and your password).
4.  **Official Documentation**: Always refer to the official midPoint documentation for the specific version you are using, as configuration details can change.
