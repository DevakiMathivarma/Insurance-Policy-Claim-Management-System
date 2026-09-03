from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.policy import Policy
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.base_repository import BaseRepository
from app.repositories.beneficiary_repository import BeneficiaryRepository
from app.models.beneficiary import Beneficiary
from app.schemas.beneficiary_schema import BeneficiaryCreate, BeneficiaryUpdate
from app.utils.logger import logger


def create_beneficiary(policy_id: int, data: BeneficiaryCreate, current_user: User, db: Session) -> dict:

    try:

        logger.info(f"Adding beneficiary to policy : {policy_id}")

        policy_repo = BaseRepository(Policy, db)
        beneficiary_repo = BeneficiaryRepository(db)
        audit_repo = AuditLogRepository(db)

        policy = policy_repo.get_by_id(policy_id)

        if not policy:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found.")

        # duplicate beneficiaries should be prevented - level 5 business
        # rule, matching on name + identification number together
        duplicate = beneficiary_repo.get_duplicate(policy_id, data.name, data.identification_number)

        if duplicate:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This beneficiary is already listed on this policy.")

        # beneficiary percentages must total exactly 100% - level 5
        # business rule. reject immediately if this addition would push
        # the running total past 100%, same real-world "one complete
        # form" reasoning we agreed on
        current_total = beneficiary_repo.get_total_percentage_for_policy(policy_id)

        new_total = current_total + data.percentage

        if new_total > 100:

            remaining = Decimal("100") - current_total

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"This would bring the total to {new_total}%. Only {remaining}% remains available."
            )

        beneficiary = Beneficiary(policy_id=policy_id, **data.model_dump())

        beneficiary_repo.add(beneficiary)

        db.flush()

        audit_repo.log(
            user_id=current_user.id,
            action="CREATE",
            entity_type="Beneficiary",
            entity_id=beneficiary.id,
            description=f"Beneficiary '{data.name}' added to policy {policy_id}, {data.percentage}%"
        )

        db.commit()

        db.refresh(beneficiary)

        logger.info(f"Beneficiary added successfully : {beneficiary.id}")

        return {"message": "Beneficiary added successfully.", "data": beneficiary}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Beneficiary creation failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to add beneficiary.")


def get_beneficiaries_for_policy(policy_id: int, db: Session) -> dict:

    logger.info(f"Fetching beneficiaries for policy : {policy_id}")

    beneficiary_repo = BeneficiaryRepository(db)

    beneficiaries = beneficiary_repo.list_for_policy(policy_id)

    return {"message": "Beneficiaries fetched successfully.", "data": beneficiaries}


def update_beneficiary(beneficiary_id: int, data: BeneficiaryUpdate, current_user: User, db: Session) -> dict:

    try:

        logger.info(f"Updating beneficiary : {beneficiary_id}")

        beneficiary_repo = BeneficiaryRepository(db)
        audit_repo = AuditLogRepository(db)

        beneficiary = beneficiary_repo.get_by_id(beneficiary_id)

        if not beneficiary:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Beneficiary not found.")

        update_data = data.model_dump(exclude_unset=True)

        # if percentage is being changed, re-run the running-total check,
        # excluding this beneficiary's own current share from the total
        # first, then adding back their new proposed percentage
        if "percentage" in update_data:

            current_total_excluding_self = beneficiary_repo.get_total_percentage_for_policy(beneficiary.policy_id, exclude_beneficiary_id=beneficiary_id)

            new_total = current_total_excluding_self + update_data["percentage"]

            if new_total > 100:

                remaining = Decimal("100") - current_total_excluding_self

                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"This would bring the total to {new_total}%. Only {remaining}% remains available."
                )

        # duplicate check also needs to run again if name/id is being
        # changed, excluding this beneficiary's own row
        check_name = update_data.get("name", beneficiary.name)
        check_id = update_data.get("identification_number", beneficiary.identification_number)

        duplicate = beneficiary_repo.get_duplicate(beneficiary.policy_id, check_name, check_id, exclude_beneficiary_id=beneficiary_id)

        if duplicate:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This beneficiary is already listed on this policy.")

        for key, value in update_data.items():

            setattr(beneficiary, key, value)

        audit_repo.log(
            user_id=current_user.id,
            action="UPDATE",
            entity_type="Beneficiary",
            entity_id=beneficiary.id,
            description="Beneficiary updated"
        )

        db.commit()

        db.refresh(beneficiary)

        logger.info(f"Beneficiary updated successfully : {beneficiary_id}")

        return {"message": "Beneficiary updated successfully.", "data": beneficiary}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Beneficiary update failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to update beneficiary.")


def delete_beneficiary(beneficiary_id: int, current_user: User, db: Session) -> dict:

    try:

        logger.info(f"Deleting beneficiary : {beneficiary_id}")

        beneficiary_repo = BeneficiaryRepository(db)
        audit_repo = AuditLogRepository(db)

        beneficiary = beneficiary_repo.get_by_id(beneficiary_id)

        if not beneficiary:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Beneficiary not found.")

        beneficiary_repo.delete(beneficiary)

        audit_repo.log(
            user_id=current_user.id,
            action="DELETE",
            entity_type="Beneficiary",
            entity_id=beneficiary_id,
            description="Beneficiary removed"
        )

        db.commit()

        logger.info(f"Beneficiary deleted successfully : {beneficiary_id}")

        return {"message": "Beneficiary deleted successfully."}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Beneficiary deletion failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to delete beneficiary.")