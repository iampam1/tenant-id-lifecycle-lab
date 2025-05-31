# src/app/routers/__init__.py
from . import auth_router
from . import tenant_router
from . import user_router
from . import lifecycle_router

# You could also expose the router objects directly, e.g.:
# from .auth_router import router as auth_api_router
# ...etc.
