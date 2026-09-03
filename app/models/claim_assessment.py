from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ClaimAssessment(Base):
    __tablename__ = "claim_assessments"

    id = Column(Integer, primary_key=True, index=True)

    # one claim, one assessment - uselist=False on the claim side already
    # enforces this at the ORM level, unique=True backs it at the
    # database level too
    claim_id = Column(Integer, ForeignKey("claims.id", ondelete="CASCADE"), unique=True, nullable=False)

    assessor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    eligible_amount = Column(Numeric(12, 2), nullable=False)

    assessment_notes = Column(Text, nullable=True)

    # recommendation isn't given a fixed value list in the task - free
    # text like "Approve", "Reject", "Needs more documents" - a genuine
    # judgment call by the assessor, not a locked status
    recommendation = Column(String(200), nullable=True)

    assessed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # relationships
    claim = relationship("Claim", back_populates="assessment")
    assessor = relationship("User")