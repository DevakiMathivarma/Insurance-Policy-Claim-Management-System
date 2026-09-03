from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository):

    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_email(self, email: str):

        return self.db.query(User).filter(User.email == email).first()

    def get_by_email_or_phone(self, email: str, phone: str):

        return self.db.query(User).filter((User.email == email) | (User.phone == phone)).first()