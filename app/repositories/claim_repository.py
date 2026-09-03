from sqlalchemy.orm import Session, joinedload

from app.models.claim import Claim
from app.models.customer import Customer
from app.repositories.base_repository import BaseRepository


class ClaimRepository(BaseRepository):

    def __init__(self, db: Session):
        super().__init__(Claim, db)

    def get_by_id_with_details(self, claim_id: int):

        return (
            self.db.query(Claim)
            .options(joinedload(Claim.policy), joinedload(Claim.customer).joinedload(Customer.user))
            .filter(Claim.id == claim_id)
            .first()
        )

    def get_by_claim_number(self, claim_number: str):

        return self.db.query(Claim).filter(Claim.claim_number == claim_number).first()

    def get_duplicate_for_incident(self, policy_id: int, incident_date, claim_type, exclude_claim_id: int | None = None):

        query = self.db.query(Claim).filter(
            Claim.policy_id == policy_id,
            Claim.incident_date == incident_date,
            Claim.claim_type == claim_type
        )

        if exclude_claim_id:

            query = query.filter(Claim.id != exclude_claim_id)

        return query.first()

    def list_claims(self, claim_status, claim_type, start_date, end_date, min_amount, max_amount, sort_column, sort_order, offset, limit):

        query = self.db.query(Claim).options(joinedload(Claim.policy), joinedload(Claim.customer).joinedload(Customer.user))

        if claim_status:

            query = query.filter(Claim.status == claim_status)

        if claim_type:

            query = query.filter(Claim.claim_type == claim_type)

        if start_date:

            query = query.filter(Claim.incident_date >= start_date)

        if end_date:

            query = query.filter(Claim.incident_date <= end_date)

        if min_amount is not None:

            query = query.filter(Claim.claim_amount >= min_amount)

        if max_amount is not None:

            query = query.filter(Claim.claim_amount <= max_amount)

        query = query.order_by(sort_column.asc() if sort_order == "asc" else sort_column.desc())

        total_records = query.count()

        claims = query.offset(offset).limit(limit).all()

        return claims, total_records