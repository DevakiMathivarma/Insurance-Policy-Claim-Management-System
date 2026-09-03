from enum import Enum

from sqlalchemy import CheckConstraint, Column, DateTime, Enum as SQLEnum, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class PlanType(str, Enum):
    LIFE = "LIFE"
    HEALTH = "HEALTH"
    VEHICLE = "VEHICLE"
    PROPERTY = "PROPERTY"
    TRAVEL = "TRAVEL"



# status 
class PlanStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class Plan(Base):
    __tablename__ = "plans"

    __table_args__ = (
        CheckConstraint("premium_amount > 0", name="ck_plan_premium_positive"),
        CheckConstraint("coverage_amount > premium_amount", name="ck_plan_coverage_exceeds_premium"),
        CheckConstraint("duration_years > 0", name="ck_plan_duration_positive"),
        CheckConstraint("eligibility_age_min < eligibility_age_max", name="ck_plan_age_range_valid"),
    )

    id = Column(Integer, primary_key=True, index=True)

    plan_name = Column(String(200), nullable=False)
    plan_type = Column(SQLEnum(PlanType), nullable=False)
    description = Column(Text, nullable=True)

    coverage_amount = Column(Numeric(12, 2), nullable=False)
    premium_amount = Column(Numeric(10, 2), nullable=False)
    duration_years = Column(Integer, nullable=False)

    eligibility_age_min = Column(Integer, nullable=False)
    eligibility_age_max = Column(Integer, nullable=False)

    status = Column(SQLEnum(PlanStatus), default=PlanStatus.ACTIVE, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # relationships
    policies = relationship("Policy", back_populates="plan")