from datetime import datetime, timedelta
from typing import Optional, Any, Union

from jose import JWTError, jwt
from passlib.context import CryptContext

from src.app.core.config import settings

# Password Hashing
# Using passlib with bcrypt for password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against its hashed version."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a plain password."""
    return pwd_context.hash(password)


# JWT Token Handling
def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Creates a new JWT access token.
    :param subject: The subject of the token (e.g., username or user ID).
    :param expires_delta: Optional timedelta for token expiration. If None, uses default from settings.
    :return: The encoded JWT token as a string.
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """
    Decodes a JWT access token.
    :param token: The encoded JWT token string.
    :return: The decoded token payload as a dictionary, or None if decoding fails or token is invalid.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        # Optionally, you could check for 'exp' (expiration) here again,
        # though jwt.decode should handle it if the token is expired.
        # You might also want to validate other claims if present.
        return payload
    except JWTError: # Catches various errors like expired token, invalid signature, etc.
        return None

# Example Usage (can be removed or kept for testing):
# if __name__ == "__main__":
#     # Password Hashing Example
#     plain_pw = "password123"
#     hashed_pw = get_password_hash(plain_pw)
#     print(f"Plain: {plain_pw}")
#     print(f"Hashed: {hashed_pw}")
#     print(f"Verification (correct): {verify_password(plain_pw, hashed_pw)}")
#     print(f"Verification (incorrect): {verify_password('wrongpassword', hashed_pw)}")

#     # JWT Example
#     user_identifier = "testuser@example.com"
#     access_token = create_access_token(subject=user_identifier)
#     print(f"
Access Token for '{user_identifier}': {access_token}")

#     decoded_payload = decode_access_token(access_token)
#     if decoded_payload:
#         print(f"Decoded Payload: {decoded_payload}")
#         print(f"Subject from token: {decoded_payload.get('sub')}")
#     else:
#         print("Token could not be decoded or is invalid.")

#     # Example of an expired token
#     expired_token = create_access_token(subject="expired_user", expires_delta=timedelta(seconds=-10))
#     print(f"
Expired Token: {expired_token}")
#     decoded_expired_payload = decode_access_token(expired_token)
#     if decoded_expired_payload:
#         print(f"Decoded Expired Payload: {decoded_expired_payload}") # Should not print this
#     else:
#         print("Expired token correctly identified as invalid.")
