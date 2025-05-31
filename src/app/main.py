from fastapi import FastAPI, status # Add status
from fastapi.staticfiles import StaticFiles # Import StaticFiles
from fastapi.templating import Jinja2Templates # Import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware

from src.app.core.config import settings
from src.app.routers import tenant_router, user_router, auth_router, lifecycle_router, ui_router # Add ui_router

# Initialize Jinja2Templates
# The directory "src/app/templates" should exist or be created.
templates = Jinja2Templates(directory="src/app/templates")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Mount static files directory
# The directory "src/app/static" should exist or be created.
app.mount("/static", StaticFiles(directory="src/app/static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/") # Keep existing root endpoint or modify as preferred
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}

@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
async def health_check():
    """
    Simple health check endpoint.
    Returns 200 OK if the application is running.
    Can be expanded to check database connectivity or other dependencies.
    """
    return {"status": "ok"}

# Include API routers
app.include_router(auth_router.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Auth"])
app.include_router(tenant_router.router, prefix=f"{settings.API_V1_STR}/tenants", tags=["Tenants"])
app.include_router(user_router.router, prefix=f"{settings.API_V1_STR}/users", tags=["Users"])
app.include_router(lifecycle_router.router, prefix=f"{settings.API_V1_STR}/lifecycle", tags=["Identity Lifecycle"])

# Include UI router - should be last or have a general prefix
app.include_router(ui_router.router, prefix="/ui", tags=["UI (Pages)"])


# To run this application (from the root of the repository, ensure .env file is present):
# uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
