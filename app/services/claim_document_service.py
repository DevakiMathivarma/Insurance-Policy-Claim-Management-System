from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.models.claim import Claim
from app.models.claim_document import ClaimDocument, DocumentType, VerificationStatus
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.base_repository import BaseRepository
from app.repositories.claim_document_repository import ClaimDocumentRepository
from app.utils.file_upload import save_claim_document
from app.utils.logger import logger


async def upload_claim_document(claim_id: int, document_type: DocumentType, file: UploadFile, current_user: User, db: Session) -> dict:

    try:

        logger.info(f"Uploading document for claim : {claim_id}, type {document_type.value}")

        claim_repo = BaseRepository(Claim, db)
        document_repo = ClaimDocumentRepository(db)
        audit_repo = AuditLogRepository(db)

        claim = claim_repo.get_by_id(claim_id)

        if not claim:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found.")

        # only allowed file types should be accepted - level 8 business
        # rule, the real check happens inside save_claim_document itself
        original_filename, file_path = await save_claim_document(file, claim_id)

        document = ClaimDocument(
            claim_id=claim_id,
            document_type=document_type,
            file_name=original_filename,
            file_path=file_path,
            verification_status=VerificationStatus.PENDING
        )

        document_repo.add(document)

        db.flush()

        audit_repo.log(
            user_id=current_user.id,
            action="CREATE",
            entity_type="ClaimDocument",
            entity_id=document.id,
            description=f"Document '{original_filename}' uploaded for claim {claim_id}"
        )

        db.commit()

        document = document_repo.get_by_id_with_details(document.id)

        logger.info(f"Claim document uploaded successfully : {document.id}")

        return {"message": "Document uploaded successfully.", "data": document}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Claim document upload failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to upload document.")


def get_documents_for_claim(claim_id: int, db: Session) -> dict:

    logger.info(f"Fetching documents for claim : {claim_id}")

    document_repo = ClaimDocumentRepository(db)

    documents = document_repo.list_for_claim(claim_id)

    return {"message": "Documents fetched successfully.", "data": documents}


def verify_claim_document(document_id: int, verification_status: VerificationStatus, current_user: User, db: Session) -> dict:

    try:

        logger.info(f"Verifying claim document : {document_id}, status {verification_status.value}")

        document_repo = ClaimDocumentRepository(db)
        claim_repo = BaseRepository(Claim, db)
        audit_repo = AuditLogRepository(db)

        document = document_repo.get_by_id_with_details(document_id)

        if not document:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

        document.verification_status = verification_status
        document.verified_by_user_id = current_user.id

        audit_repo.log(
            user_id=current_user.id,
            action="VERIFY",
            entity_type="ClaimDocument",
            entity_id=document.id,
            description=f"Document verification set to {verification_status.value}"
        )

        db.commit()

        document = document_repo.get_by_id_with_details(document_id)

        # level 14 - "documents required" notification. worth being
        # precise about when this actually fires: if a document is
        # rejected, the claim genuinely needs a replacement, so notify
        # the customer right at this moment, not just when staff
        # separately flip the claim's own status
        if verification_status == VerificationStatus.REJECTED:

            from app.tasks import send_documents_required_email
            

            claim = claim_repo.get_by_id(document.claim_id)

            if claim:

                customer_user = claim.customer.user

                send_documents_required_email.delay(customer_user.email, customer_user.full_name, claim.claim_number)

        logger.info(f"Claim document verified successfully : {document_id}")

        return {"message": "Document verification updated successfully.", "data": document}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Claim document verification failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to verify document.")