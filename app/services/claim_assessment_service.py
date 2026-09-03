from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.claim import Claim, ClaimStatus
from app.models.claim_assessment import ClaimAssessment
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.base_repository import BaseRepository
from app.repositories.claim_assessment_repository import ClaimAssessmentRepository
from app.schemas.claim_assessment_schema import ClaimAssessmentCreate
from app.utils.logger import logger


def create_assessment(claim_id: int, data: ClaimAssessmentCreate, current_user: User, db: Session) -> dict:

    try:

        logger.info(f"Creating assessment for claim : {claim_id}")

        claim_repo = BaseRepository(Claim, db)
        assessment_repo = ClaimAssessmentRepository(db)
        audit_repo = AuditLogRepository(db)

        claim = claim_repo.get_by_id(claim_id)

        if not claim:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found.")

        # one assessment per claim - friendly pre-check, backed by the
        # database's own unique constraint on claim_id
        existing_assessment = assessment_repo.get_by_claim_id(claim_id)

        if existing_assessment:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This claim has already been assessed.")

        # calculate the eligible settlement amount based on policy
        # coverage and assessment - level 9's own business logic. the
        # task gives no formula, so this is the claims officer's own
        # professional judgment; the one real, checkable ceiling is that
        # it cannot exceed the policy's actual coverage
        if data.eligible_amount > claim.policy.coverage_amount:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Eligible amount cannot exceed the policy's coverage amount of {claim.policy.coverage_amount}."
            )

        assessment = ClaimAssessment(
            claim_id=claim_id,
            assessor_id=current_user.id,
            eligible_amount=data.eligible_amount,
            assessment_notes=data.assessment_notes,
            recommendation=data.recommendation
        )

        assessment_repo.add(assessment)

        db.flush()

        # an assessed claim moves to under review, ready for a final
        # approve/reject decision - a reasonable status transition since
        # the task doesn't explicitly state one
        if claim.status == ClaimStatus.SUBMITTED:

            claim.status = ClaimStatus.UNDER_REVIEW

        audit_repo.log(
            user_id=current_user.id,
            action="CREATE",
            entity_type="ClaimAssessment",
            entity_id=assessment.id,
            description=f"Assessment created for claim {claim_id}, eligible amount {data.eligible_amount}"
        )

        db.commit()

        assessment = assessment_repo.get_by_claim_id(claim_id)

        logger.info(f"Assessment created successfully : {assessment.id}")

        return {"message": "Assessment created successfully.", "data": assessment}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Assessment creation failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to create assessment.")


def get_assessment_for_claim(claim_id: int, db: Session) -> dict:

    logger.info(f"Fetching assessment for claim : {claim_id}")

    assessment_repo = ClaimAssessmentRepository(db)

    assessment = assessment_repo.get_by_claim_id(claim_id)

    if not assessment:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No assessment found for this claim.")

    return {"message": "Assessment fetched successfully.", "data": assessment}