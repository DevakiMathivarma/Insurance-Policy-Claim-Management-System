from sqlalchemy.orm import Session, joinedload

from app.models.policy import Policy
from app.repositories.base_repository import BaseRepository


class PolicyRepository(BaseRepository):

    def __init__(self, db: Session):
        super().__init__(Policy, db)

    def get_by_id_with_details(self, policy_id: int):

        return (
            self.db.query(Policy)
            .options(joinedload(Policy.customer), joinedload(Policy.plan), joinedload(Policy.agent))
            .filter(Policy.id == policy_id)
            .first()
        )

    def get_by_policy_number(self, policy_number: str):

        return self.db.query(Policy).filter(Policy.policy_number == policy_number).first()

    def list_policies(self, policy_status, plan_type, customer_id, sort_column, sort_order, offset, limit):

        from app.models.plan import Plan

        query = self.db.query(Policy).options(joinedload(Policy.customer), joinedload(Policy.plan), joinedload(Policy.agent))

        if policy_status:

            query = query.filter(Policy.policy_status == policy_status)

        if plan_type:

            query = query.join(Plan, Policy.plan_id == Plan.id).filter(Plan.plan_type == plan_type)

        if customer_id:

            query = query.filter(Policy.customer_id == customer_id)

        query = query.order_by(sort_column.asc() if sort_order == "asc" else sort_column.desc())

        total_records = query.count()

        policies = query.offset(offset).limit(limit).all()

        return policies, total_records

    def get_policies_expiring_within(self, days: int):

        from datetime import date, timedelta
        from app.models.policy import PolicyStatus
        from app.models.customer import Customer

        cutoff = date.today() + timedelta(days=days)

        return (
            self.db.query(Policy)
            .options(joinedload(Policy.customer).joinedload(Customer.user))
            .filter(Policy.policy_status == PolicyStatus.ACTIVE, Policy.end_date <= cutoff, Policy.end_date >= date.today())
            .all()
        )

    def get_expired_active_policies(self):

        from datetime import date
        from app.models.policy import PolicyStatus

        return self.db.query(Policy).filter(Policy.policy_status == PolicyStatus.ACTIVE, Policy.end_date < date.today()).all()
    
    def get_renewal_for_policy(self, policy_id: int):

        return self.db.query(Policy).filter(Policy.renewed_from_policy_id == policy_id).first()