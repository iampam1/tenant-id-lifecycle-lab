from typing import Generator, Any, Optional
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from src.app.db.session import SessionLocal
from src.app.core.config import settings
from src.app.core import security # For decode_access_token
from src.app.services import auth_service # For get_user_by_username/email
from src.app.models import user as user_model # For type hinting return value
from src.app.schemas import token_schema # For TokenData

# Define the OAuth2 scheme.
# tokenUrl should point to the login endpoint.
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

def get_db() -> Generator[Any, Any, Any]:
    """
    Dependency to get a database session.
    Ensures the database session is always closed after the request.
    """
    db = None
    try:
        db = SessionLocal()
        yield db
    finally:
        if db:
            db.close()

async def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> user_model.User:
    """
    Dependency to get the current authenticated user.
    Decodes JWT token, validates it, and fetches the user from the database.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = security.decode_access_token(token)
    if payload is None: # Token is invalid (e.g. expired, malformed)
        raise credentials_exception

    # Assuming the 'sub' of the token is the user's email, as set in auth_router.login_for_access_token
    # This could also be user_id or username depending on how create_access_token is used.
    subject_email: Optional[str] = payload.get("sub")
    if subject_email is None:
        raise credentials_exception # 'sub' claim missing

    # Fetch the user from the database using the subject (email) from the token.
    # Since email is used as subject, and assumed globally unique for login:
    user = auth_service.get_user_by_email(db, email=subject_email)

    if user is None:
        raise credentials_exception # User not found for the given subject

    if not user.is_active:
        # Optionally, you might allow inactive users but restrict their actions.
        # For now, treat inactive as unauthorized for general API access.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, # Or 403 Forbidden
            detail="Inactive user"
        )

    return user

async def get_current_active_user( # Example of a more specific dependency
    current_user: user_model.User = Depends(get_current_user)
) -> user_model.User:
    """
    Same as get_current_user, but explicitly checks for active status.
    This is somewhat redundant if get_current_user already checks for is_active,
    but can be used to make intent clearer or if get_current_user might change.
    """
    if not current_user.is_active: # This check is already in get_current_user
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user
