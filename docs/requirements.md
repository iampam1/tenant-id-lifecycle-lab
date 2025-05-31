# Requirements & Architecture (Draft)

## Target Functionalities

- User Onboarding
- Access Request & Approval
- Privilege Elevation & Management
- User Offboarding
- Tenant Isolation

## Chosen Technologies (Initial Thoughts - Subject to Change)

- **IGA Engine:** TBD (midPoint or Apache Syncope) - *Rationale: Exploring options based on ease of setup, community support, and feature set for multi-tenancy.*
- **PAM Engine:** TBD (JumpServer or Teleport) - *Rationale: Evaluating based on ease of integration, open-source availability, and core PAM features.*
- **Database:** PostgreSQL - *Rationale: Robust, open-source, and well-supported by Python tools and free hosting tiers.*
- **Web Framework:** FastAPI - *Rationale: Modern, high-performance Python framework with automatic data validation and API documentation.*
- **Hosting Platforms:** Exploring Fly.io, Render.com, Railway.app - *Rationale: Free tiers available for PostgreSQL and Python web applications.*
- **AI Agent Usage:** GitHub Copilot (if available), ChatGPT (Free/Plus), potentially open-source LLMs for specific tasks like code generation and documentation.

## Architecture Sketch Placeholder

(A basic block diagram will be added here: `docs/architecture.png`)
