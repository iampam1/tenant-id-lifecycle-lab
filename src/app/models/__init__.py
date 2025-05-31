# src/app/models/__init__.py
from .base import Base
from .tenant import Tenant
from .user import User
from .role import Role
from .user_role import UserRole
from .audit_log import AuditLog

# This makes it easier to import models, e.g.:
# from src.app.models import Tenant, User
# Also helps Alembic discover models if __init__.py is processed,
# though direct imports in env.py are more explicit for Alembic.
