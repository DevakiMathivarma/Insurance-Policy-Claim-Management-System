from sqlalchemy.orm import Session, joinedload

from app.models.claim_assessment import ClaimAssessment
from app.repositories.base_repository import BaseRepository


class ClaimAssessmentRepository(BaseRepository):

    def __init__(self, db: Session):
        super().__init__(ClaimAssessment, db)

    def get_by_claim_id(self, claim_id: int):

        return self.db.query(ClaimAssessment).options(joinedload(ClaimAssessment.assessor)).filter(ClaimAssessment.claim_id == claim_id).first()