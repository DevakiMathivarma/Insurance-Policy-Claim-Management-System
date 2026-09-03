from enum import Enum

from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class DocumentType(str, Enum):
    ID_PROOF = "ID_PROOF"
    INVOICE = "INVOICE"
    MEDICAL_REPORT = "MEDICAL_REPORT"
    FIR = "FIR"
    REPAIR_ESTIMATE = "REPAIR_ESTIMATE"
    OTHER = "OTHER"


class VerificationStatus(str, Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class ClaimDocument(Base):
    __tablename__ = "claim_documents"

    id = Column(Integer, primary_key=True, index=True)

    claim_id = Column(Integer, ForeignKey("claims.id", ondelete="CASCADE"), nullable=False)

    document_type = Column(SQLEnum(DocumentType), nullable=False)

    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)

    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    verification_status = Column(SQLEnum(VerificationStatus), default=VerificationStatus.PENDING, nullable=False)

    verified_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # relationships
    claim = relationship("Claim", back_populates="documents")
    verified_by = relationship("User")