from enum import Enum

from sqlalchemy import CheckConstraint, Column, Date, DateTime, Enum as SQLEnum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class PolicyStatus(str, Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    SUSPENDED = "SUSPENDED"


class Policy(Base):
    __tablename__ = "policies"

    __table_args__ = (
        CheckConstraint("coverage_amount > 0", name="ck_policy_coverage_positive"),
        CheckConstraint("premium_amount > 0", name="ck_policy_premium_positive"),
    )

    id = Column(Integer, primary_key=True, index=True)

    # unique, human-readable reference - level 4's own business rule,
    # enforced at the database level
    policy_number = Column(String(50), unique=True, nullable=False, index=True)

    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id", ondelete="RESTRICT"), nullable=False)
    agent_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    # locked in from the plan at the moment of purchase, not looked up
    # live - same "lock in what was agreed" principle as lease's
    # monthly_rent in the property platform
    coverage_amount = Column(Numeric(12, 2), nullable=False)
    premium_amount = Column(Numeric(10, 2), nullable=False)

    policy_status = Column(SQLEnum(PolicyStatus), default=PolicyStatus.PENDING, nullable=False)
    next_premium_due_date = Column(Date, nullable=True)
    renewed_from_policy_id = Column(Integer, ForeignKey("policies.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # relationships
    customer = relationship("Customer", back_populates="policies")
    plan = relationship("Plan", back_populates="policies")
    agent = relationship("User")

    beneficiaries = relationship("Beneficiary", back_populates="policy", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="policy", cascade="all, delete-orphan")
    claims = relationship("Claim", back_populates="policy")