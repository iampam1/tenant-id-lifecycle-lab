from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    username = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True) # Uniqueness per tenant handled by UniqueConstraint
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    user_roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")

    # Add UniqueConstraint for (tenant_id, username) and (tenant_id, email)
    # These are typically defined in the Alembic migration or can be added here too.
    # For now, focusing on basic column structure. Alembic will handle constraints based on schema.

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', tenant_id={self.tenant_id})>"
