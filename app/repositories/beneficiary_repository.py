from sqlalchemy.orm import Session

from app.models.beneficiary import Beneficiary
from app.repositories.base_repository import BaseRepository


class BeneficiaryRepository(BaseRepository):

    def __init__(self, db: Session):
        super().__init__(Beneficiary, db)

    def list_for_policy(self, policy_id: int):

        return self.db.query(Beneficiary).filter(Beneficiary.policy_id == policy_id).all()

    def get_total_percentage_for_policy(self, policy_id: int, exclude_beneficiary_id: int | None = None) -> float:

        query = self.db.query(Beneficiary).filter(Beneficiary.policy_id == policy_id)

        if exclude_beneficiary_id:

            query = query.filter(Beneficiary.id != exclude_beneficiary_id)

        beneficiaries = query.all()

        return sum(b.percentage for b in beneficiaries)

    def get_duplicate(self, policy_id: int, name: str, identification_number: str | None, exclude_beneficiary_id: int | None = None):

        query = self.db.query(Beneficiary).filter(
            Beneficiary.policy_id == policy_id,
            Beneficiary.name == name,
            Beneficiary.identification_number == identification_number
        )

        if exclude_beneficiary_id:

            query = query.filter(Beneficiary.id != exclude_beneficiary_id)

        return query.first()