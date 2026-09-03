from sqlalchemy.orm import Session


class BaseRepository:
    """Generic CRUD - each specific repository inherits this and only adds
    queries unique to its own table. Deliberately does NOT commit - the
    calling service still controls the transaction boundary."""

    def __init__(self, model, db: Session):
        self.model = model
        self.db = db

    def get_by_id(self, id: int):
        return self.db.query(self.model).filter(self.model.id == id).first()

    def add(self, obj):
        self.db.add(obj)
        return obj

    def delete(self, obj):
        self.db.delete(obj)