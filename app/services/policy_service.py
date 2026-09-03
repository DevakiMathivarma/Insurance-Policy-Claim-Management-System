import random
import string
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.plan import Plan, PlanStatus
from app.models.policy import Policy, PolicyStatus
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.base_repository import BaseRepository
from app.repositories.policy_repository import PolicyRepository
from app.schemas.policy_schema import PolicyCreate, PolicyUpdate, PolicyResponse
from app.utils.logger import logger
from app.utils.pagination import get_pagination, get_offset
from app.utils.redis_cache import get_cache, set_cache, delete_cache

CACHE_TTL = 600


def _calculate_age(date_of_birth: date) -> int:

    today = date.today()

    return today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))


def _generate_policy_number() -> str:

    year = date.today().year

    random_suffix = "".join(random.choices(string.digits, k=6))

    return f"POL-{year}-{random_suffix}"


def create_policy(data: PolicyCreate, current_user: User, db: Session) -> dict:

    try:

        logger.info(f"Creating policy : customer {data.customer_id}, plan {data.plan_id}")

        customer_repo = BaseRepository(Customer, db)
        plan_repo = BaseRepository(Plan, db)
        policy_repo = PolicyRepository(db)
        audit_repo = AuditLogRepository(db)

        customer = customer_repo.get_by_id(data.customer_id)

        if not customer:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found.")

        plan = plan_repo.get_by_id(data.plan_id)

        if not plan:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found.")

        # inactive plans cannot be purchased - level 2 business rule
        if plan.status != PlanStatus.ACTIVE:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This plan is not currently available for purchase.")

        # only eligible customers can purchase a plan - level 4 business
        # rule, checking age against this specific plan's range
        customer_age = _calculate_age(customer.date_of_birth)

        if not (plan.eligibility_age_min <= customer_age <= plan.eligibility_age_max):

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Customer age {customer_age} does not meet this plan's eligibility range ({plan.eligibility_age_min}-{plan.eligibility_age_max})."
            )

        # generate a unique policy number, retrying on the rare chance of collision
        policy_number = _generate_policy_number()

        while policy_repo.get_by_policy_number(policy_number):

            policy_number = _generate_policy_number()

        policy = Policy(
            policy_number=policy_number,
            customer_id=data.customer_id,
            plan_id=data.plan_id,
            agent_id=current_user.id,
            start_date=data.start_date,
            end_date=data.end_date,
            # locked in from the plan at the moment of purchase, never
            # taken from the request
            coverage_amount=plan.coverage_amount,
            premium_amount=plan.premium_amount,
            policy_status=PolicyStatus.PENDING
        )

        policy_repo.add(policy)

        db.flush()

        audit_repo.log(
            user_id=current_user.id,
            action="CREATE",
            entity_type="Policy",
            entity_id=policy.id,
            description=f"Policy {policy_number} created for customer {data.customer_id}"
        )

        db.commit()

        policy = policy_repo.get_by_id_with_details(policy.id)

        logger.info(f"Policy created successfully : {policy.id}, number {policy_number}")

        return {"message": "Policy created successfully.", "data": policy}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Policy creation failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to create policy.")


# get by id - cached (bonus feature, redis)
def get_policy_by_id(policy_id: int, db: Session) -> dict:

    logger.info(f"Fetching policy by id : {policy_id}")

    cache_key = f"policy:{policy_id}"

    cached_policy = get_cache(cache_key)

    if cached_policy:

        logger.info(f"Policy cache hit : {policy_id}")

        return {"message": "Policy fetched successfully.", "data": cached_policy}

    policy_repo = PolicyRepository(db)

    policy = policy_repo.get_by_id_with_details(policy_id)

    if not policy:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found.")

    set_cache(cache_key, PolicyResponse.model_validate(policy).model_dump(mode="json"), expire=CACHE_TTL)

    return {"message": "Policy fetched successfully.", "data": policy}


# level 12 - filter by policy status, plan type, customer, expiry date
def get_all_policies(
    db: Session,
    page: int = 1,
    limit: int = 10,
    policy_status=None,
    plan_type=None,
    customer_id: int | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> dict:

    logger.info("Fetching policies list.")

    policy_repo = PolicyRepository(db)

    sortable_columns = {"created_at": Policy.created_at, "end_date": Policy.end_date}

    sort_column = sortable_columns.get(sort_by, Policy.created_at)

    policies, total_records = policy_repo.list_policies(policy_status, plan_type, customer_id, sort_column, sort_order, get_offset(page, limit), limit)

    return {"message": "Policies fetched successfully.", "data": policies, "pagination": get_pagination(total_records, page, limit)}


def update_policy(policy_id: int, data: PolicyUpdate, current_user: User, db: Session) -> dict:

    try:

        logger.info(f"Updating policy : {policy_id}")

        policy_repo = PolicyRepository(db)
        audit_repo = AuditLogRepository(db)

        policy = policy_repo.get_by_id_with_details(policy_id)

        if not policy:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found.")

        update_data = data.model_dump(exclude_unset=True)

        for key, value in update_data.items():

            setattr(policy, key, value)

        audit_repo.log(
            user_id=current_user.id,
            action="UPDATE",
            entity_type="Policy",
            entity_id=policy.id,
            description="Policy updated"
        )

        db.commit()

        db.refresh(policy)

        delete_cache(f"policy:{policy_id}")

        logger.info(f"Policy updated successfully : {policy_id}")

        return {"message": "Policy updated successfully.", "data": policy}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Policy update failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to update policy.")

def activate_policy(policy_id: int, current_user: User, db: Session) -> dict:

    try:

        logger.info(f"Activating policy : {policy_id}")

        policy_repo = PolicyRepository(db)
        audit_repo = AuditLogRepository(db)

        policy = policy_repo.get_by_id_with_details(policy_id)

        if not policy:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found.")

        if policy.policy_status != PolicyStatus.PENDING:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending policies can be activated.")

        policy.policy_status = PolicyStatus.ACTIVE

        audit_repo.log(
            user_id=current_user.id,
            action="ACTIVATE",
            entity_type="Policy",
            entity_id=policy.id,
            description="Policy activated"
        )

        db.commit()

        delete_cache(f"policy:{policy_id}")

        policy = policy_repo.get_by_id_with_details(policy_id)

        # level 14 - policy activation email + pdf policy document, same
        # wiring as the payment-triggered activation path, now genuinely
        # consistent between both activation routes
        from app.utils.pdf import generate_policy_document_pdf
        from app.tasks import send_policy_activation_email

        customer_user = policy.customer.user

        document_path = generate_policy_document_pdf(
            policy_id=policy.id,
            policy_number=policy.policy_number,
            customer_name=customer_user.full_name,
            plan_name=policy.plan.plan_name,
            coverage_amount=str(policy.coverage_amount),
            premium_amount=str(policy.premium_amount),
            start_date=str(policy.start_date),
            end_date=str(policy.end_date)
        )

        send_policy_activation_email.delay(customer_user.email, customer_user.full_name, policy.policy_number, document_path)

        logger.info(f"Policy activated successfully : {policy_id}")

        return {"message": "Policy activated successfully.", "data": policy}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Policy activation failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to activate policy.")


def cancel_policy(policy_id: int, current_user: User, db: Session) -> dict:

    try:

        logger.info(f"Cancelling policy : {policy_id}")

        policy_repo = PolicyRepository(db)
        audit_repo = AuditLogRepository(db)

        policy = policy_repo.get_by_id_with_details(policy_id)

        if not policy:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found.")

        if policy.policy_status in (PolicyStatus.CANCELLED, PolicyStatus.EXPIRED):

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This policy is already cancelled or expired.")

        policy.policy_status = PolicyStatus.CANCELLED

        audit_repo.log(
            user_id=current_user.id,
            action="CANCEL",
            entity_type="Policy",
            entity_id=policy.id,
            description="Policy cancelled"
        )

        db.commit()

        delete_cache(f"policy:{policy_id}")

        policy = policy_repo.get_by_id_with_details(policy_id)

        logger.info(f"Policy cancelled successfully : {policy_id}")

        return {"message": "Policy cancelled successfully.", "data": policy}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Policy cancellation failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to cancel policy.")


def renew_policy(policy_id: int, current_user: User, db: Session) -> dict:

    try:

        logger.info(f"Renewing policy : {policy_id}")

        policy_repo = PolicyRepository(db)
        audit_repo = AuditLogRepository(db)

        old_policy = policy_repo.get_by_id_with_details(policy_id)

        if not old_policy:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found.")

        # only eligible policies can be renewed - level 11 business
        # rule. a policy genuinely due for renewal must be active or
        # already expired, not cancelled/suspended/still pending
        if old_policy.policy_status not in (PolicyStatus.ACTIVE, PolicyStatus.EXPIRED):

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only active or expired policies can be renewed.")

        # prevent duplicate renewal - level 11 business rule
        existing_renewal = policy_repo.get_renewal_for_policy(policy_id)

        if existing_renewal:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This policy has already been renewed.")

        # generate a new policy period - level 11's own requirement,
        # picking up exactly where the old one left off
        new_start_date = old_policy.end_date
        new_end_date = date(new_start_date.year + old_policy.plan.duration_years, new_start_date.month, new_start_date.day)

        new_policy_number = _generate_policy_number()

        while policy_repo.get_by_policy_number(new_policy_number):

            new_policy_number = _generate_policy_number()

            new_policy = Policy(
            policy_number=new_policy_number,
            customer_id=old_policy.customer_id,
            plan_id=old_policy.plan_id,
            agent_id=current_user.id,
            start_date=new_start_date,
            end_date=new_end_date,
            coverage_amount=old_policy.coverage_amount,
            premium_amount=old_policy.premium_amount,
            policy_status=PolicyStatus.PENDING,
            renewed_from_policy_id=old_policy.id,
            # the first premium on a renewed policy is due right away,
            # at the new period's own start - same reasoning as a fresh
            # policy needing its first payment before activation
            next_premium_due_date=new_start_date)
        

        policy_repo.add(new_policy)

        db.flush()

        audit_repo.log(
            user_id=current_user.id,
            action="RENEW",
            entity_type="Policy",
            entity_id=new_policy.id,
            description=f"Policy {new_policy_number} renewed from {old_policy.policy_number}"
        )

        db.commit()

        new_policy = policy_repo.get_by_id_with_details(new_policy.id)

        logger.info(f"Policy renewed successfully : old {policy_id}, new {new_policy.id}")

        return {"message": "Policy renewed successfully.", "data": new_policy}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Policy renewal failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to renew policy.")



def get_expiring_policies(db: Session, days: int = 30) -> dict:

    logger.info(f"Fetching policies expiring within {days} days.")

    policy_repo = PolicyRepository(db)

    policies = policy_repo.get_policies_expiring_within(days)

    return {"message": "Expiring policies fetched successfully.", "data": policies}