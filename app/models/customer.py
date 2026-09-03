from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)

    # one login account, one customer profile
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    # full_name, email, phone already live on User, not repeated here
    date_of_birth = Column(Date, nullable=False)
    address = Column(String(300), nullable=True)

    # identification_number must be unique  enforced at the database level so it can never be silently violated
    identification_number = Column(String(50), unique=True, nullable=False)

    occupation = Column(String(150), nullable=True)

    # who created this profile - the customer themselves (self-registered),
    # or an insurance agent creating it on their behalf
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # relationships
    user = relationship("User", back_populates="customer", foreign_keys=[user_id])
    created_by = relationship("User", foreign_keys=[created_by_user_id])

    policies = relationship("Policy", back_populates="customer", cascade="all, delete-orphan")
    claims = relationship("Claim", back_populates="customer", cascade="all, delete-orphan")