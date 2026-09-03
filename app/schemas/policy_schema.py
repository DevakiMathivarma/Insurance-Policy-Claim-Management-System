from datetime import date, datetime
from decimal import Decimal

from pydantic import Field, model_validator

from app.models.policy import PolicyStatus
from app.schemas.common_schema import AppBaseSchema, PaginationResponse
from app.schemas.customer_schema import CustomerBasicResponse
from app.schemas.plan_schema import PlanBasicResponse
from app.schemas.user_schema import UserBasicResponse


class PolicyCreate(AppBaseSchema):
    customer_id: int
    plan_id: int
    start_date: date
    end_date: date

    # end date must be after start date - level 4's own business rule,
    # needs both fields at once, so it belongs here
    @model_validator(mode="after")
    def check_dates(self):
        if self.start_date >= self.end_date:
            raise ValueError("start_date must be before end_date.")
        return self


class PolicyUpdate(AppBaseSchema):
    end_date: date | None = None


class PolicyBasicResponse(AppBaseSchema):
    id: int
    policy_number: str
    policy_status: PolicyStatus


class PolicyResponse(PolicyBasicResponse):
    customer: CustomerBasicResponse
    plan: PlanBasicResponse
    agent: UserBasicResponse | None
    start_date: date
    end_date: date
    coverage_amount: Decimal
    premium_amount: Decimal
    created_at: datetime
    updated_at: datetime


class PolicyMessageResponse(AppBaseSchema):
    message: str
    data: PolicyResponse


class PolicyPaginationResponse(AppBaseSchema):
    message: str
    pagination: PaginationResponse
    data: list[PolicyResponse]

class PolicyListResponse(AppBaseSchema):
    message: str
    data: list[PolicyResponse]