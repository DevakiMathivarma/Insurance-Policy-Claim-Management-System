from sqlalchemy.orm import Session, joinedload

from app.models.claim_document import ClaimDocument
from app.repositories.base_repository import BaseRepository


class ClaimDocumentRepository(BaseRepository):

    def __init__(self, db: Session):
        super().__init__(ClaimDocument, db)

    def get_by_id_with_details(self, document_id: int):

        return self.db.query(ClaimDocument).options(joinedload(ClaimDocument.verified_by)).filter(ClaimDocument.id == document_id).first()

    def list_for_claim(self, claim_id: int):

        return (
            self.db.query(ClaimDocument)
            .options(joinedload(ClaimDocument.verified_by))
            .filter(ClaimDocument.claim_id == claim_id)
            .order_by(ClaimDocument.uploaded_at.desc())
            .all()
        )