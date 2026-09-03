from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.plan import Plan, PlanStatus
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.plan_repository import PlanRepository
from app.schemas.plan_schema import PlanCreate, PlanUpdate, PlanResponse
from app.utils.logger import logger
from app.utils.pagination import get_pagination, get_offset
from app.utils.redis_cache import get_cache, set_cache, delete_cache

CACHE_TTL = 600


def create_plan(data: PlanCreate, current_user: User, db: Session) -> dict:

    try:

        logger.info(f"Creating plan : {data.plan_name}")

        plan_repo = PlanRepository(db)
        audit_repo = AuditLogRepository(db)

        plan = Plan(**data.model_dump())

        plan_repo.add(plan)

        db.flush()

        audit_repo.log(
            user_id=current_user.id,
            action="CREATE",
            entity_type="Plan",
            entity_id=plan.id,
            description=f"Plan '{data.plan_name}' created"
        )

        db.commit()

        db.refresh(plan)

        logger.info(f"Plan created successfully : {plan.id}")

        return {"message": "Plan created successfully.", "data": plan}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Plan creation failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to create plan.")


# get by id - cached (bonus feature, redis)
def get_plan_by_id(plan_id: int, db: Session) -> dict:

    logger.info(f"Fetching plan by id : {plan_id}")

    cache_key = f"plan:{plan_id}"

    cached_plan = get_cache(cache_key)

    if cached_plan:

        logger.info(f"Plan cache hit : {plan_id}")

        return {"message": "Plan fetched successfully.", "data": cached_plan}

    plan_repo = PlanRepository(db)

    plan = plan_repo.get_by_id(plan_id)

    if not plan:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found.")

    set_cache(cache_key, PlanResponse.model_validate(plan).model_dump(mode="json"), expire=CACHE_TTL)

    return {"message": "Plan fetched successfully.", "data": plan}


# level 12 - filter by plan type, status
def get_all_plans(
    db: Session,
    page: int = 1,
    limit: int = 10,
    plan_type=None,
    status_filter=None,
    search: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> dict:

    logger.info("Fetching plans list.")

    plan_repo = PlanRepository(db)

    sortable_columns = {"created_at": Plan.created_at, "premium_amount": Plan.premium_amount}

    sort_column = sortable_columns.get(sort_by, Plan.created_at)

    plans, total_records = plan_repo.list_plans(plan_type, status_filter, search, sort_column, sort_order, get_offset(page, limit), limit)

    return {"message": "Plans fetched successfully.", "data": plans, "pagination": get_pagination(total_records, page, limit)}


def update_plan(plan_id: int, data: PlanUpdate, current_user: User, db: Session) -> dict:

    try:

        logger.info(f"Updating plan : {plan_id}")

        plan_repo = PlanRepository(db)
        audit_repo = AuditLogRepository(db)

        plan = plan_repo.get_by_id(plan_id)

        if not plan:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found.")

        update_data = data.model_dump(exclude_unset=True)

        for key, value in update_data.items():

            setattr(plan, key, value)

        audit_repo.log(
            user_id=current_user.id,
            action="UPDATE",
            entity_type="Plan",
            entity_id=plan.id,
            description="Plan updated"
        )

        db.commit()

        db.refresh(plan)

        delete_cache(f"plan:{plan_id}")

        logger.info(f"Plan updated successfully : {plan_id}")

        return {"message": "Plan updated successfully.", "data": plan}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Plan update failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to update plan.")


# soft delete - status flips to inactive, which also naturally satisfies
# "inactive plans cannot be purchased" once policy_service checks this field
def delete_plan(plan_id: int, current_user: User, db: Session) -> dict:

    try:

        logger.info(f"Deleting plan : {plan_id}")

        plan_repo = PlanRepository(db)
        audit_repo = AuditLogRepository(db)

        plan = plan_repo.get_by_id(plan_id)

        if not plan:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found.")

        plan.status = PlanStatus.INACTIVE

        audit_repo.log(
            user_id=current_user.id,
            action="DELETE",
            entity_type="Plan",
            entity_id=plan.id,
            description="Plan soft-deleted"
        )

        db.commit()

        delete_cache(f"plan:{plan_id}")

        logger.info(f"Plan deleted successfully : {plan_id}")

        return {"message": "Plan deleted successfully."}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Plan deletion failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to delete plan.")