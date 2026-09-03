from datetime import datetime

from pydantic import Field

from app.models.claim_document import DocumentType, VerificationStatus
from app.schemas.common_schema import AppBaseSchema
from app.schemas.user_schema import UserBasicResponse


# used alongside a real file upload (multipart form), not pure JSON -
# same pattern as the property platform's qr verification endpoint
class ClaimDocumentCreate(AppBaseSchema):
    document_type: DocumentType


class ClaimDocumentVerify(AppBaseSchema):
    verification_status: VerificationStatus


class ClaimDocumentResponse(AppBaseSchema):
    id: int
    claim_id: int
    document_type: DocumentType
    file_name: str
    uploaded_at: datetime
    verification_status: VerificationStatus
    verified_by: UserBasicResponse | None


class ClaimDocumentMessageResponse(AppBaseSchema):
    message: str
    data: ClaimDocumentResponse


class ClaimDocumentListResponse(AppBaseSchema):
    message: str
    data: list[ClaimDocumentResponse]