from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.app.core.config import settings
# Import routers
from src.app.routers import tenant_router, user_router, auth_router, lifecycle_router # Adjusted order for consistency

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json" # Example: /api/v1/openapi.json
)

# Set all CORS enabled origins
# This is a permissive configuration for development.
# For production, you should restrict origins more carefully.
# Example: if settings.BACKEND_CORS_ORIGINS:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Or use settings.BACKEND_CORS_ORIGINS if defined and populated
    allow_credentials=True,
    allow_methods=["*"], # Allows all standard methods
    allow_headers=["*"], # Allows all headers
)

# Root endpoint
@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}

# Include routers
app.include_router(auth_router.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Auth"])
app.include_router(tenant_router.router, prefix=f"{settings.API_V1_STR}/tenants", tags=["Tenants"])
app.include_router(user_router.router, prefix=f"{settings.API_V1_STR}/users", tags=["Users"])
app.include_router(lifecycle_router.router, prefix=f"{settings.API_V1_STR}/lifecycle", tags=["Identity Lifecycle"])


# To run this application (from the root of the repository, ensure .env file is present):
# uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
