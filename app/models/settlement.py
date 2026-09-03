from enum import Enum

from sqlalchemy import CheckConstraint, Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class SettlementStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Settlement(Base):
    __tablename__ = "settlements"

    __table_args__ = (
        CheckConstraint("approved_amount > 0", name="ck_settlement_amount_positive"),
    )

    id = Column(Integer, primary_key=True, index=True)

    # one claim, one settlement - same double-protected pattern as
    # claim_assessment
    claim_id = Column(Integer, ForeignKey("claims.id", ondelete="CASCADE"), unique=True, nullable=False)

    approved_amount = Column(Numeric(12, 2), nullable=False)

    settlement_date = Column(DateTime(timezone=True), nullable=True)

    # a reference number for the actual payout transaction - free text,
    # since the task gives no fixed format
    payment_reference = Column(String(100), nullable=True)

    settlement_status = Column(SQLEnum(SettlementStatus), default=SettlementStatus.PENDING, nullable=False)

    processed_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # relationships
    claim = relationship("Claim", back_populates="settlement")
    processed_by = relationship("User")