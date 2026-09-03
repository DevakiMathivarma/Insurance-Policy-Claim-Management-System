from enum import Enum

from sqlalchemy import CheckConstraint, Column, Date, DateTime, Enum as SQLEnum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ClaimStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    DOCUMENTS_REQUIRED = "DOCUMENTS_REQUIRED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SETTLED = "SETTLED"


class Claim(Base):
    __tablename__ = "claims"

    __table_args__ = (
        CheckConstraint("claim_amount > 0", name="ck_claim_amount_positive"),
    )

    id = Column(Integer, primary_key=True, index=True)

    # unique, human-readable reference - same pattern as policy_number
    claim_number = Column(String(50), unique=True, nullable=False, index=True)

    policy_id = Column(Integer, ForeignKey("policies.id", ondelete="RESTRICT"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False)

    # claim_type isn't given a fixed value list in the task - free text
    # like "Accident", "Theft", "Hospitalization"
    claim_type = Column(String(100), nullable=False)

    incident_date = Column(Date, nullable=False)
    claim_amount = Column(Numeric(12, 2), nullable=False)
    description = Column(Text, nullable=True)

    status = Column(SQLEnum(ClaimStatus), default=ClaimStatus.DRAFT, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # relationships
    policy = relationship("Policy", back_populates="claims")
    customer = relationship("Customer", back_populates="claims")

    documents = relationship("ClaimDocument", back_populates="claim", cascade="all, delete-orphan")
    assessment = relationship("ClaimAssessment", back_populates="claim", uselist=False, cascade="all, delete-orphan")
    settlement = relationship("Settlement", back_populates="claim", uselist=False, cascade="all, delete-orphan")