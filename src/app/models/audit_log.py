from sqlalchemy import Column, Integer, String, DateTime, JSON as SA_JSON, ForeignKey, BigInteger
from sqlalchemy.sql import func
from .base import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(BigInteger, primary_key=True, index=True) # Using BigInteger as per schema
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True) # User performing action
    action_type = Column(String(100), nullable=False, index=True)
    details = Column(SA_JSON, nullable=True) # Event-specific data
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships (optional, could be useful for querying)
    # tenant = relationship("Tenant")
    # user = relationship("User")

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action_type='{self.action_type}', user_id={self.user_id}, tenant_id={self.tenant_id})>"
