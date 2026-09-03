from app.celery_app import celery_app
from app.database import SessionLocal
from app.utils.email import send_email
from app.utils.logger import logger

PREMIUM_DUE_REMINDER_WINDOW_DAYS = 7
POLICY_EXPIRY_REMINDER_WINDOW_DAYS = 30


@celery_app.task(name="app.tasks.send_email_task")
def send_email_task(to_email: str, subject: str, body: str, attachment_paths: list[str] | None = None) -> None:

    try:

        send_email(to_email=to_email, subject=subject, body=body, attachment_paths=attachment_paths)

        logger.info(f"Celery task - email sent to {to_email} : {subject}")

    except Exception as error:

        logger.error(f"Celery task - email failed to {to_email} : {str(error)}")


@celery_app.task(name="app.tasks.send_policy_activation_email")
def send_policy_activation_email(to_email, customer_name, policy_number, policy_document_path=None):

    body = f"Hi {customer_name},\n\nYour policy #{policy_number} has been activated. Your policy document is attached."

    attachments = [policy_document_path] if policy_document_path else []

    send_email_task(to_email, "Policy Activated", body, attachment_paths=attachments)


@celery_app.task(name="app.tasks.send_premium_payment_success_email")
def send_premium_payment_success_email(to_email, customer_name, amount, policy_number):

    body = f"Hi {customer_name},\n\nWe've received your premium payment of {amount} for policy #{policy_number}. Thank you!"

    send_email_task(to_email, "Premium Payment Successful", body)


@celery_app.task(name="app.tasks.send_premium_due_reminder_email")
def send_premium_due_reminder_email(to_email, customer_name, policy_number, amount, due_date):

    body = f"Hi {customer_name},\n\nA premium payment of {amount} is due on {due_date} for your policy #{policy_number}."

    send_email_task(to_email, "Premium Due Reminder", body)


@celery_app.task(name="app.tasks.send_premium_overdue_email")
def send_premium_overdue_email(to_email, customer_name, policy_number, amount):

    body = f"Hi {customer_name},\n\nYour premium payment of {amount} for policy #{policy_number} is now overdue."

    send_email_task(to_email, "Premium Overdue Notice", body)


@celery_app.task(name="app.tasks.send_claim_submission_email")
def send_claim_submission_email(to_email, customer_name, claim_number):

    body = f"Hi {customer_name},\n\nYour claim #{claim_number} has been submitted and is now under review."

    send_email_task(to_email, "Claim Submitted", body)


@celery_app.task(name="app.tasks.send_documents_required_email")
def send_documents_required_email(to_email, customer_name, claim_number):

    body = f"Hi {customer_name},\n\nYour claim #{claim_number} requires additional documents."

    send_email_task(to_email, "Documents Required for Your Claim", body)


@celery_app.task(name="app.tasks.send_claim_decision_email")
def send_claim_decision_email(to_email, customer_name, claim_number, decision):

    body = f"Hi {customer_name},\n\nYour claim #{claim_number} has been {decision}."

    send_email_task(to_email, f"Claim {decision.capitalize()}", body)


@celery_app.task(name="app.tasks.send_claim_settlement_email")
def send_claim_settlement_email(to_email, customer_name, claim_number, approved_amount, settlement_letter_path=None):

    body = f"Hi {customer_name},\n\nYour claim #{claim_number} has been settled for {approved_amount}. Your settlement letter is attached."

    attachments = [settlement_letter_path] if settlement_letter_path else []

    send_email_task(to_email, "Claim Settled", body, attachment_paths=attachments)


@celery_app.task(name="app.tasks.send_policy_expiry_email")
def send_policy_expiry_email(to_email, customer_name, policy_number, end_date):

    body = f"Hi {customer_name},\n\nYour policy #{policy_number} is set to expire on {end_date}."

    send_email_task(to_email, "Policy Expiring Soon", body)


@celery_app.task(name="app.tasks.run_daily_premium_and_policy_checks")
def run_daily_premium_and_policy_checks():

    from app.repositories.policy_repository import PolicyRepository
    from app.repositories.payment_repository import PaymentRepository

    db = SessionLocal()

    try:

        policy_repo = PolicyRepository(db)
        payment_repo = PaymentRepository(db)

        expiring_soon = policy_repo.get_policies_expiring_within(POLICY_EXPIRY_REMINDER_WINDOW_DAYS)

        for policy in expiring_soon:

            customer_user = policy.customer.user

            send_policy_expiry_email.delay(customer_user.email, customer_user.full_name, policy.policy_number, str(policy.end_date))

        expired_policies = policy_repo.get_expired_active_policies()

        for policy in expired_policies:

            from app.models.policy import PolicyStatus
            policy.policy_status = PolicyStatus.EXPIRED

        due_soon_policies = payment_repo.get_policies_with_premium_due_within(PREMIUM_DUE_REMINDER_WINDOW_DAYS)

        for policy in due_soon_policies:

            customer_user = policy.customer.user

            send_premium_due_reminder_email.delay(
                customer_user.email, customer_user.full_name, policy.policy_number, str(policy.premium_amount), str(policy.next_premium_due_date)
            )

        overdue_policies = payment_repo.get_policies_with_overdue_premium()

        for policy in overdue_policies:

            customer_user = policy.customer.user

            send_premium_overdue_email.delay(customer_user.email, customer_user.full_name, policy.policy_number, str(policy.premium_amount))

        db.commit()

        logger.info(
            f"Daily checks complete : {len(expiring_soon)} expiry reminders, {len(expired_policies)} expired, "
            f"{len(due_soon_policies)} due reminders, {len(overdue_policies)} overdue"
        )

    except Exception as error:

        db.rollback()

        logger.error(f"Daily premium/policy check failed : {str(error)}")

    finally:

        db.close()