from sqlalchemy import Column, Integer, String, JSON as SA_JSON, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    # tenant_id is nullable if some roles are global (e.g., super_admin)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    role_name = Column(String(100), nullable=False, index=True) # e.g., "tenant_admin", "application_user"
    permissions_json = Column(SA_JSON, nullable=True) # For storing specific permissions

    # Relationships
    # tenant = relationship("Tenant", back_populates="roles") # If a tenant can have multiple roles directly
    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")

    # UniqueConstraint for (tenant_id, role_name) will be handled by Alembic based on schema.

    def __repr__(self):
        return f"<Role(id={self.id}, role_name='{self.role_name}', tenant_id={self.tenant_id})>"
