from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    # who performed the action
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # what kind of action happened - free text like "CREATE", "UPDATE",
    # "APPROVE", "SETTLE" - not an enum, since actions vary widely
    action = Column(String(50), nullable=False)

    # which table/resource was affected - free text like "Policy",
    # "Claim", "Settlement"
    entity_type = Column(String(50), nullable=False)

    # the id of the specific row affected - deliberately a plain number,
    # not a real ForeignKey, since it needs to point at a different table
    # depending on entity_type
    entity_id = Column(Integer, nullable=False)

    description = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # relationships
    user = relationship("User")