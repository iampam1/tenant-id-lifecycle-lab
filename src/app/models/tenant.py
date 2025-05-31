from sqlalchemy import Column, Integer, String, DateTime, JSON as SA_JSON # Renamed to avoid conflict if JSON is used elsewhere
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base # Assuming Base is defined in models/base.py

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    config_json = Column(SA_JSON, nullable=True) # For tenant-specific IGA/PAM configs etc.

    # Relationships
    # Ensure User and Role are imported if type hinting is used stringified, or define them before Tenant if not.
    # For simplicity with circular dependencies, stringified names are often used.
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    # roles = relationship("Role", back_populates="tenant", cascade="all, delete-orphan") # Role model not fully defined yet with back_populates for tenant

    def __repr__(self):
        return f"<Tenant(id={self.id}, name='{self.name}')>"
