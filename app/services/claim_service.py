import random
import string
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.claim import Claim, ClaimStatus
from app.models.claim_document import VerificationStatus
from app.models.policy import Policy, PolicyStatus
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.base_repository import BaseRepository
from app.repositories.claim_repository import ClaimRepository
from app.schemas.claim_schema import ClaimCreate, ClaimUpdate
from app.utils.logger import logger
from app.utils.pagination import get_pagination, get_offset


def _generate_claim_number() -> str:
    year = date.today().year
    random_suffix = "".join(random.choices(string.digits, k=6))
    return f"CLM-{year}-{random_suffix}"


def create_claim(data: ClaimCreate, current_user, db: Session) -> dict:
    try:
        policy_repo = BaseRepository(Policy, db)
        claim_repo = ClaimRepository(db)
        audit_repo = AuditLogRepository(db)

        policy = policy_repo.get_by_id(data.policy_id)
        if not policy:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found.")

        if policy.policy_status != PolicyStatus.ACTIVE:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Claims can only be created for active policies.")

        if not (policy.start_date <= data.incident_date <= policy.end_date):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Incident date must fall between the policy's coverage period ({policy.start_date} to {policy.end_date}).")

        if data.claim_amount > policy.coverage_amount:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Claim amount cannot exceed the policy's coverage amount of {policy.coverage_amount}.")

        duplicate = claim_repo.get_duplicate_for_incident(data.policy_id, data.incident_date, data.claim_type)
        if duplicate:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A claim for this incident has already been filed on this policy.")

        claim_number = _generate_claim_number()
        while claim_repo.get_by_claim_number(claim_number):
            claim_number = _generate_claim_number()

        claim = Claim(claim_number=claim_number, policy_id=data.policy_id, customer_id=policy.customer_id,
            claim_type=data.claim_type, incident_date=data.incident_date, claim_amount=data.claim_amount,
            description=data.description, status=ClaimStatus.DRAFT)
        claim_repo.add(claim)
        db.flush()

        audit_repo.log(user_id=current_user.id, action="CREATE", entity_type="Claim", entity_id=claim.id, description=f"Claim {claim_number} created")
        db.commit()
        claim = claim_repo.get_by_id_with_details(claim.id)
        return {"message": "Claim created successfully.", "data": claim}
    except HTTPException:
        raise
    except Exception as error:
        db.rollback()
        logger.error(f"Claim creation failed : {str(error)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to create claim.")


def get_claim_by_id(claim_id: int, db: Session) -> dict:
    claim_repo = ClaimRepository(db)
    claim = claim_repo.get_by_id_with_details(claim_id)
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found.")
    return {"message": "Claim fetched successfully.", "data": claim}


def get_all_claims(db: Session, page=1, limit=10, claim_status=None, claim_type=None, start_date=None, end_date=None, min_amount=None, max_amount=None, sort_by="created_at", sort_order="desc") -> dict:
    claim_repo = ClaimRepository(db)
    sortable_columns = {"created_at": Claim.created_at, "claim_amount": Claim.claim_amount, "incident_date": Claim.incident_date}
    sort_column = sortable_columns.get(sort_by, Claim.created_at)
    claims, total_records = claim_repo.list_claims(claim_status, claim_type, start_date, end_date, min_amount, max_amount, sort_column, sort_order, get_offset(page, limit), limit)
    return {"message": "Claims fetched successfully.", "data": claims, "pagination": get_pagination(total_records, page, limit)}


def update_claim(claim_id: int, data: ClaimUpdate, current_user, db: Session) -> dict:
    try:
        claim_repo = ClaimRepository(db)
        audit_repo = AuditLogRepository(db)
        claim = claim_repo.get_by_id_with_details(claim_id)
        if not claim:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found.")
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(claim, key, value)
        audit_repo.log(user_id=current_user.id, action="UPDATE", entity_type="Claim", entity_id=claim.id, description="Claim updated")
        db.commit()
        db.refresh(claim)
        return {"message": "Claim updated successfully.", "data": claim}
    except HTTPException:
        raise
    except Exception as error:
        db.rollback()
        logger.error(f"Claim update failed : {str(error)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to update claim.")


def submit_claim(claim_id: int, current_user, db: Session) -> dict:
    try:
        claim_repo = ClaimRepository(db)
        audit_repo = AuditLogRepository(db)
        claim = claim_repo.get_by_id_with_details(claim_id)
        if not claim:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found.")
        if claim.status != ClaimStatus.DRAFT:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only draft claims can be submitted.")
        claim.status = ClaimStatus.SUBMITTED
        audit_repo.log(user_id=current_user.id, action="SUBMIT", entity_type="Claim", entity_id=claim.id, description="Claim submitted")
        db.commit()
        claim = claim_repo.get_by_id_with_details(claim_id)

        from app.tasks import send_claim_submission_email
        customer_user = claim.customer.user
        send_claim_submission_email.delay(customer_user.email, customer_user.full_name, claim.claim_number)

        from app.routes.websocket import broadcast_claim_status_sync
        broadcast_claim_status_sync(claim.id, ClaimStatus.SUBMITTED.value)

        return {"message": "Claim submitted successfully.", "data": claim}
    except HTTPException:
        raise
    except Exception as error:
        db.rollback()
        logger.error(f"Claim submission failed : {str(error)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to submit claim.")


def approve_claim(claim_id: int, current_user, db: Session) -> dict:
    try:
        claim_repo = ClaimRepository(db)
        audit_repo = AuditLogRepository(db)
        claim = claim_repo.get_by_id_with_details(claim_id)
        if not claim:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found.")
        if claim.status not in (ClaimStatus.SUBMITTED, ClaimStatus.UNDER_REVIEW):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only submitted or under-review claims can be approved.")
        # unverified claims cannot proceed to final approval - level 8
        # business rule. a claim with zero documents must also be
        # blocked, not just one with unverified documents - an empty
        # claim.documents list would otherwise make the check below
        # trivially pass, which defeats the whole point of the rule
        if not claim.documents:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one verified document is required before this claim can be approved.")

        unverified_documents = [doc for doc in claim.documents if doc.verification_status != VerificationStatus.VERIFIED]
        if unverified_documents:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="All documents must be verified before this claim can be approved.")
        claim.status = ClaimStatus.APPROVED
        audit_repo.log(user_id=current_user.id, action="APPROVE", entity_type="Claim", entity_id=claim.id, description="Claim approved")
        db.commit()
        claim = claim_repo.get_by_id_with_details(claim_id)

        from app.tasks import send_claim_decision_email
        customer_user = claim.customer.user
        send_claim_decision_email.delay(customer_user.email, customer_user.full_name, claim.claim_number, "approved")

        from app.routes.websocket import broadcast_claim_status_sync
        broadcast_claim_status_sync(claim.id, ClaimStatus.APPROVED.value)

        return {"message": "Claim approved successfully.", "data": claim}
    except HTTPException:
        raise
    except Exception as error:
        db.rollback()
        logger.error(f"Claim approval failed : {str(error)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to approve claim.")


def reject_claim(claim_id: int, current_user, db: Session) -> dict:
    try:
        claim_repo = ClaimRepository(db)
        audit_repo = AuditLogRepository(db)
        claim = claim_repo.get_by_id_with_details(claim_id)
        if not claim:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found.")
        if claim.status not in (ClaimStatus.SUBMITTED, ClaimStatus.UNDER_REVIEW):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only submitted or under-review claims can be rejected.")
        claim.status = ClaimStatus.REJECTED
        audit_repo.log(user_id=current_user.id, action="REJECT", entity_type="Claim", entity_id=claim.id, description="Claim rejected")
        db.commit()
        claim = claim_repo.get_by_id_with_details(claim_id)

        from app.tasks import send_claim_decision_email
        customer_user = claim.customer.user
        send_claim_decision_email.delay(customer_user.email, customer_user.full_name, claim.claim_number, "rejected")

        from app.routes.websocket import broadcast_claim_status_sync
        broadcast_claim_status_sync(claim.id, ClaimStatus.REJECTED.value)

        return {"message": "Claim rejected successfully.", "data": claim}
    except HTTPException:
        raise
    except Exception as error:
        db.rollback()
        logger.error(f"Claim rejection failed : {str(error)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to reject claim.")