from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditLogRepository:

    def __init__(self, db: Session):
        self.db = db

    def log(self, user_id: int | None, action: str, entity_type: str, entity_id: int, description: str | None = None) -> AuditLog:

        entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description
        )

        self.db.add(entry)

        return entry