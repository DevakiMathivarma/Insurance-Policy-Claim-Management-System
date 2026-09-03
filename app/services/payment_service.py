from datetime import date
from dateutil.relativedelta import relativedelta

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.models.policy import Policy, PolicyStatus
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.base_repository import BaseRepository
from app.repositories.payment_repository import PaymentRepository
from app.schemas.payment_schema import PaymentCreate
from app.utils.logger import logger
from app.utils.pagination import get_pagination, get_offset


def create_payment(policy_id: int, data: PaymentCreate, current_user: User, db: Session) -> dict:

    try:

        logger.info(f"Recording premium payment : policy {policy_id}, transaction {data.transaction_id}")

        policy_repo = BaseRepository(Policy, db)
        payment_repo = PaymentRepository(db)
        audit_repo = AuditLogRepository(db)

        policy = policy_repo.get_by_id(policy_id)

        if not policy:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found.")

        # prevent duplicate transactions - friendly pre-check, backed by
        # the database's own unique constraint
        existing_payment = db.query(Payment).filter(Payment.transaction_id == data.transaction_id).first()

        if existing_payment:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This transaction ID has already been used.")

        # payment amount must match the expected premium - level 6
        # business rule
        if data.amount != policy.premium_amount:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment amount must exactly match the policy's premium amount of {policy.premium_amount}."
            )

        payment = Payment(
            policy_id=policy_id,
            amount=data.amount,
            payment_method=data.payment_method,
            transaction_id=data.transaction_id,
            status=PaymentStatus.SUCCESS,
            created_by_user_id=current_user.id
        )

        payment_repo.add(payment)

        db.flush()

        # failed payments should not activate a policy - since this
        # payment was just validated as successful, activate the policy
        # if it's still pending
        was_first_activation = False

        if policy.policy_status == PolicyStatus.PENDING:

            policy.policy_status = PolicyStatus.ACTIVE

            was_first_activation = True

        # advance the next premium due date by 1 year from today,
        # regardless of whether this was the first payment or a renewal
        policy.next_premium_due_date = date.today() + relativedelta(years=1)

        audit_repo.log(
            user_id=current_user.id,
            action="CREATE",
            entity_type="Payment",
            entity_id=payment.id,
            description=f"Premium payment of {data.amount} recorded for policy {policy_id}"
        )

        db.commit()

        db.refresh(payment)

        # level 14 - premium payment success email, always sent
        from app.tasks import send_premium_payment_success_email

        customer_user = policy.customer.user

        send_premium_payment_success_email.delay(customer_user.email, customer_user.full_name, str(data.amount), policy.policy_number)

        # level 14 - policy activation email + pdf policy document,
        # only sent the first time a policy activates
        if was_first_activation:

            from app.utils.pdf import generate_policy_document_pdf
            from app.tasks import send_policy_activation_email

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

        logger.info(f"Premium payment recorded successfully : {payment.id}, policy activated={was_first_activation}")

        return {"message": "Premium payment recorded successfully.", "data": payment}

    except HTTPException:

        raise

    except IntegrityError:

        db.rollback()

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This transaction ID has already been used.")

    except Exception as error:

        db.rollback()

        logger.error(f"Premium payment recording failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to record premium payment.")


def get_payment_by_id(payment_id: int, db: Session) -> dict:

    logger.info(f"Fetching payment by id : {payment_id}")

    payment_repo = PaymentRepository(db)

    payment = payment_repo.get_by_id_with_details(payment_id)

    if not payment:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found.")

    return {"message": "Payment fetched successfully.", "data": payment}


# level 12 - filter by payment status, method, date range
def get_all_payments(
    db: Session,
    page: int = 1,
    limit: int = 10,
    payment_status=None,
    payment_method=None,
    start_date=None,
    end_date=None
) -> dict:

    logger.info("Fetching payments list.")

    payment_repo = PaymentRepository(db)

    payments, total_records = payment_repo.list_payments(payment_status, payment_method, start_date, end_date, get_offset(page, limit), limit)

    return {"message": "Payments fetched successfully.", "data": payments, "pagination": get_pagination(total_records, page, limit)}


def get_payments_for_policy(policy_id: int, db: Session, page: int = 1, limit: int = 10) -> dict:

    logger.info(f"Fetching payments for policy : {policy_id}")

    payment_repo = PaymentRepository(db)

    payments, total_records = payment_repo.list_for_policy(policy_id, get_offset(page, limit), limit)

    return {"message": "Payments fetched successfully.", "data": payments, "pagination": get_pagination(total_records, page, limit)}