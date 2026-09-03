from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Beneficiary(Base):
    __tablename__ = "beneficiaries"

    __table_args__ = (
        CheckConstraint("percentage > 0 AND percentage <= 100", name="ck_beneficiary_percentage_range"),
    )

    id = Column(Integer, primary_key=True, index=True)

    policy_id = Column(Integer, ForeignKey("policies.id", ondelete="CASCADE"), nullable=False)

    name = Column(String(150), nullable=False)

    # relationship isn't given a fixed value list in the task - free text
    # like "Spouse", "Son", "Daughter", same reasoning as maintenance
    # request's category field in the property platform
    relationship_type = Column(String(50), nullable=False)

    percentage = Column(Numeric(5, 2), nullable=False)

    phone = Column(String(15), nullable=True)
    identification_number = Column(String(50), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # relationships
    policy = relationship("Policy", back_populates="beneficiaries")