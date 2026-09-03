from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.customer import Customer
from app.models.user import User
from app.repositories.base_repository import BaseRepository


class CustomerRepository(BaseRepository):

    def __init__(self, db: Session):
        super().__init__(Customer, db)

    def get_by_id_with_details(self, customer_id: int):

        return (
            self.db.query(Customer)
            .options(joinedload(Customer.user), joinedload(Customer.created_by))
            .filter(Customer.id == customer_id)
            .first()
        )

    def get_by_identification_number(self, identification_number: str):

        return self.db.query(Customer).filter(Customer.identification_number == identification_number).first()

    def list_customers(self, search, sort_column, sort_order, offset, limit):

        query = (
            self.db.query(Customer)
            .options(joinedload(Customer.user), joinedload(Customer.created_by))
            .join(User, Customer.user_id == User.id)
        )

        if search:

            search_term = f"%{search}%"

            query = query.filter(or_(User.full_name.ilike(search_term), User.email.ilike(search_term)))

        query = query.order_by(sort_column.asc() if sort_order == "asc" else sort_column.desc())

        total_records = query.count()

        customers = query.offset(offset).limit(limit).all()

        return customers, total_records