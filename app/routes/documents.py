from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.auth.current_user import get_current_user
from app.auth.permissions import require_admin_or_claims_officer, require_any_role
from app.database import get_db
from app.models.claim_document import DocumentType, VerificationStatus
from app.models.user import User
from app.schemas.claim_document_schema import ClaimDocumentMessageResponse, ClaimDocumentListResponse
from app.services.claim_document_service import upload_claim_document, get_documents_for_claim, verify_claim_document

router = APIRouter(prefix="/api/v1", tags=["Claim Document Management"])


@router.post("/claims/{claim_id}/documents", response_model=ClaimDocumentMessageResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    claim_id: int,
    document_type: DocumentType = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return await upload_claim_document(claim_id, document_type, file, current_user, db)


@router.get("/claims/{claim_id}/documents", response_model=ClaimDocumentListResponse, dependencies=[Depends(require_any_role)])
def list_documents(claim_id: int, db: Session = Depends(get_db)):

    return get_documents_for_claim(claim_id, db)


@router.put("/documents/{document_id}/verify", response_model=ClaimDocumentMessageResponse, dependencies=[Depends(require_admin_or_claims_officer)])
def verify_document(document_id: int, verification_status: VerificationStatus, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_claims_officer)):

    return verify_claim_document(document_id, verification_status, current_user, db)