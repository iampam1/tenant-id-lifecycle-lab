from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer" # Default to bearer, standard for JWT

class TokenData(BaseModel):
    # This will store the 'sub' (subject) claim from the JWT.
    # It could be username, user_id, or email. Let's use username for now.
    username: Optional[str] = None
    # You could add other fields here if you store them in the token, e.g., roles, tenant_id
    # tenant_id: Optional[int] = None
