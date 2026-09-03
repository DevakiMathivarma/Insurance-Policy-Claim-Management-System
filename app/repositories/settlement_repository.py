from sqlalchemy.orm import Session, joinedload

from app.models.settlement import Settlement
from app.repositories.base_repository import BaseRepository


class SettlementRepository(BaseRepository):

    def __init__(self, db: Session):
        super().__init__(Settlement, db)

    def get_by_id_with_details(self, settlement_id: int):

        return self.db.query(Settlement).options(joinedload(Settlement.claim), joinedload(Settlement.processed_by)).filter(Settlement.id == settlement_id).first()

    def get_by_claim_id(self, claim_id: int):

        return self.db.query(Settlement).filter(Settlement.claim_id == claim_id).first()

    def list_settlements(self, settlement_status, offset, limit):

        query = self.db.query(Settlement).options(joinedload(Settlement.claim), joinedload(Settlement.processed_by))

        if settlement_status:

            query = query.filter(Settlement.settlement_status == settlement_status)

        query = query.order_by(Settlement.created_at.desc())

        total_records = query.count()

        settlements = query.offset(offset).limit(limit).all()

        return settlements, total_records