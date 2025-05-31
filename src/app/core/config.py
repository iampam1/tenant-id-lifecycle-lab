from pydantic import BaseSettings, Field
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Tenant Identity Lifecycle Lab"
    API_V1_STR: str = "/api/v1" # Example API prefix

    # Database Configuration
    DATABASE_URL: str = Field(..., env="DATABASE_URL") # Example: "postgresql://user:pass@host:port/db_name"

    # IGA Engine Configuration (midPoint or Syncope)
    IGA_API_URL: Optional[str] = Field(None, env="IGA_API_URL") # Example: "http://localhost:8080/midpoint" or "http://localhost:9080/syncope"
    IGA_API_KEY: Optional[str] = Field(None, env="IGA_API_KEY") # Or username:password for basic auth

    # PAM Engine Configuration (JumpServer or Teleport)
    PAM_API_URL: Optional[str] = Field(None, env="PAM_API_URL") # Example: "http://localhost:8080" (JumpServer)
    PAM_API_TOKEN: Optional[str] = Field(None, env="PAM_API_TOKEN") # Or other auth mechanism

    # JWT Secret Key for FastAPI application's own authentication
    # Generate a strong key, e.g., using: openssl rand -hex 32
    SECRET_KEY: str = Field(..., env="SECRET_KEY")

    # Access Token lifetime (example: 15 minutes)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15

    # ALGORITHM for JWT
    ALGORITHM: str = "HS256"

    # CORS Origins (example, adjust as needed for frontend)
    # BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]


    class Config:
        # When using .env file, make sure python-dotenv is installed
        # pip install python-dotenv
        # Alembic might also need it if it uses this Settings class
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
