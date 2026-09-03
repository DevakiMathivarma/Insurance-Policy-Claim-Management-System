from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.plan import Plan
from app.repositories.base_repository import BaseRepository


class PlanRepository(BaseRepository):

    def __init__(self, db: Session):
        super().__init__(Plan, db)

    def list_plans(self, plan_type, status, search, sort_column, sort_order, offset, limit):

        query = self.db.query(Plan)

        if plan_type:

            query = query.filter(Plan.plan_type == plan_type)

        if status:

            query = query.filter(Plan.status == status)

        if search:

            search_term = f"%{search}%"

            query = query.filter(or_(Plan.plan_name.ilike(search_term), Plan.description.ilike(search_term)))

        query = query.order_by(sort_column.asc() if sort_order == "asc" else sort_column.desc())

        total_records = query.count()

        plans = query.offset(offset).limit(limit).all()

        return plans, total_records