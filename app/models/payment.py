from enum import Enum

from sqlalchemy import CheckConstraint, Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


# task gives an explicit fixed list here
# free-text payment_method
class PaymentMethod(str, Enum):
    UPI = "UPI"
    CARD = "CARD"
    NET_BANKING = "NET_BANKING"
    AUTO_DEBIT = "AUTO_DEBIT"


class PaymentStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PENDING = "PENDING"


class Payment(Base):
    __tablename__ = "payments"

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_payment_amount_positive"),
    )

    id = Column(Integer, primary_key=True, index=True)

    policy_id = Column(Integer, ForeignKey("policies.id", ondelete="RESTRICT"), nullable=False)

    amount = Column(Numeric(10, 2), nullable=False)

    payment_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    payment_method = Column(SQLEnum(PaymentMethod), nullable=False)

    # unique transaction reference - the real mechanism behind "prevent
    # duplicate transactions"
    transaction_id = Column(String(100), unique=True, nullable=False, index=True)

    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)

    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # relationships
    policy = relationship("Policy", back_populates="payments")
    created_by = relationship("User")