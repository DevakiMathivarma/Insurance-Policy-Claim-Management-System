from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.claim import Claim, ClaimStatus
from app.models.settlement import Settlement, SettlementStatus
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.base_repository import BaseRepository
from app.repositories.claim_assessment_repository import ClaimAssessmentRepository
from app.repositories.settlement_repository import SettlementRepository
from app.schemas.settlement_schema import SettlementCreate
from app.utils.logger import logger
from app.utils.pagination import get_pagination, get_offset


def create_settlement(claim_id: int, data: SettlementCreate, current_user: User, db: Session) -> dict:

    try:

        logger.info(f"Creating settlement for claim : {claim_id}")

        claim_repo = BaseRepository(Claim, db)
        assessment_repo = ClaimAssessmentRepository(db)
        settlement_repo = SettlementRepository(db)
        audit_repo = AuditLogRepository(db)

        claim = claim_repo.get_by_id(claim_id)

        if not claim:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found.")

        if claim.status != ClaimStatus.APPROVED:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only approved claims can be settled.")

        existing_settlement = settlement_repo.get_by_claim_id(claim_id)

        if existing_settlement:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This claim has already been settled.")

        assessment = assessment_repo.get_by_claim_id(claim_id)

        if not assessment:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This claim has no assessment on record and cannot be settled yet.")

        if data.approved_amount > assessment.eligible_amount:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Settlement amount cannot exceed the assessed eligible amount of {assessment.eligible_amount}."
            )

        settlement = Settlement(
            claim_id=claim_id,
            approved_amount=data.approved_amount,
            payment_reference=data.payment_reference,
            settlement_status=SettlementStatus.COMPLETED,
            settlement_date=datetime.now(timezone.utc),
            processed_by_user_id=current_user.id
        )

        settlement_repo.add(settlement)

        db.flush()

        claim.status = ClaimStatus.SETTLED

        audit_repo.log(
            user_id=current_user.id,
            action="CREATE",
            entity_type="Settlement",
            entity_id=settlement.id,
            description=f"Settlement of {data.approved_amount} processed for claim {claim_id}"
        )

        db.commit()

        db.refresh(settlement)

        settlement = settlement_repo.get_by_id_with_details(settlement.id)

        from app.utils.pdf import generate_settlement_letter_pdf
        from app.tasks import send_claim_settlement_email

        customer_user = claim.customer.user

        letter_path = generate_settlement_letter_pdf(
            settlement_id=settlement.id,
            claim_number=claim.claim_number,
            customer_name=customer_user.full_name,
            approved_amount=str(data.approved_amount),
            settlement_date=str(settlement.settlement_date),
            payment_reference=data.payment_reference or "N/A"
        )

        send_claim_settlement_email.delay(customer_user.email, customer_user.full_name, claim.claim_number, str(data.approved_amount), letter_path)

        from app.routes.websocket import broadcast_claim_status_sync

        broadcast_claim_status_sync(claim.id, ClaimStatus.SETTLED.value)

        logger.info(f"Settlement created successfully : {settlement.id}")

        return {"message": "Settlement processed successfully.", "data": settlement}

    except HTTPException:

        raise

    except IntegrityError:

        db.rollback()

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This claim has already been settled.")

    except Exception as error:

        db.rollback()

        logger.error(f"Settlement creation failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to process settlement.")


def get_settlement_by_id(settlement_id: int, db: Session) -> dict:

    logger.info(f"Fetching settlement by id : {settlement_id}")

    settlement_repo = SettlementRepository(db)

    settlement = settlement_repo.get_by_id_with_details(settlement_id)

    if not settlement:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Settlement not found.")

    return {"message": "Settlement fetched successfully.", "data": settlement}


def get_all_settlements(db: Session, page: int = 1, limit: int = 10, settlement_status=None) -> dict:

    logger.info("Fetching settlements list.")

    settlement_repo = SettlementRepository(db)

    settlements, total_records = settlement_repo.list_settlements(settlement_status, get_offset(page, limit), limit)

    return {"message": "Settlements fetched successfully.", "data": settlements, "pagination": get_pagination(total_records, page, limit)}