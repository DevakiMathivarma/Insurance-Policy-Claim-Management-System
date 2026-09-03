from decimal import Decimal

from sqlalchemy.orm import Session, joinedload

from app.models.payment import Payment, PaymentStatus
from app.models.policy import Policy
from app.repositories.base_repository import BaseRepository


class PaymentRepository(BaseRepository):

    def __init__(self, db: Session):
        super().__init__(Payment, db)

    def get_by_id_with_details(self, payment_id: int):

        return self.db.query(Payment).options(joinedload(Payment.policy)).filter(Payment.id == payment_id).first()

    def list_for_policy(self, policy_id: int, offset: int, limit: int):

        query = self.db.query(Payment).filter(Payment.policy_id == policy_id).order_by(Payment.payment_date.desc())

        total_records = query.count()

        payments = query.offset(offset).limit(limit).all()

        return payments, total_records

    def list_payments(self, payment_status, payment_method, start_date, end_date, offset, limit):

        query = self.db.query(Payment).options(joinedload(Payment.policy))

        if payment_status:

            query = query.filter(Payment.status == payment_status)

        if payment_method:

            query = query.filter(Payment.payment_method == payment_method)

        if start_date:

            query = query.filter(Payment.payment_date >= start_date)

        if end_date:

            query = query.filter(Payment.payment_date <= end_date)

        query = query.order_by(Payment.payment_date.desc())

        total_records = query.count()

        payments = query.offset(offset).limit(limit).all()

        return payments, total_records

    def get_policies_with_overdue_premium(self):

        from datetime import date
        from app.models.policy import PolicyStatus
        from app.models.customer import Customer

        return (
            self.db.query(Policy)
            .options(joinedload(Policy.customer).joinedload(Customer.user))
            .filter(Policy.policy_status == PolicyStatus.ACTIVE, Policy.next_premium_due_date < date.today())
            .all()
        )

    def get_policies_with_premium_due_within(self, days: int):

        from datetime import date, timedelta
        from app.models.policy import PolicyStatus
        from app.models.customer import Customer

        cutoff = date.today() + timedelta(days=days)

        return (
            self.db.query(Policy)
            .options(joinedload(Policy.customer).joinedload(Customer.user))
            .filter(Policy.policy_status == PolicyStatus.ACTIVE, Policy.next_premium_due_date <= cutoff, Policy.next_premium_due_date >= date.today())
            .all()
        )