from datetime import datetime
from decimal import Decimal

from pydantic import Field, model_validator

from app.models.plan import PlanStatus, PlanType
from app.schemas.common_schema import AppBaseSchema, PaginationResponse


class PlanCreate(AppBaseSchema):
    plan_name: str = Field(..., min_length=3, max_length=200)
    plan_type: PlanType
    description: str | None = Field(None, max_length=2000)
    coverage_amount: Decimal = Field(..., gt=0)
    premium_amount: Decimal = Field(..., gt=0)
    duration_years: int = Field(..., gt=0)
    eligibility_age_min: int = Field(..., ge=0, le=120)
    eligibility_age_max: int = Field(..., ge=0, le=120)

    # coverage amount must be greater than premium - level 2's own
    # business rule, matching the database's check constraint. also
    # validates the age range makes sense, same reasoning as the model's
    # own check constraint
    @model_validator(mode="after")
    def check_coverage_and_age_range(self):
        if self.coverage_amount <= self.premium_amount:
            raise ValueError("coverage_amount must be greater than premium_amount.")
        if self.eligibility_age_min >= self.eligibility_age_max:
            raise ValueError("eligibility_age_min must be less than eligibility_age_max.")
        return self


class PlanUpdate(AppBaseSchema):
    plan_name: str | None = Field(None, min_length=3, max_length=200)
    description: str | None = Field(None, max_length=2000)
    status: PlanStatus | None = None


class PlanBasicResponse(AppBaseSchema):
    id: int
    plan_name: str
    plan_type: PlanType
    status: PlanStatus


class PlanResponse(PlanBasicResponse):
    description: str | None
    coverage_amount: Decimal
    premium_amount: Decimal
    duration_years: int
    eligibility_age_min: int
    eligibility_age_max: int
    created_at: datetime
    updated_at: datetime


class PlanMessageResponse(AppBaseSchema):
    message: str
    data: PlanResponse


class PlanPaginationResponse(AppBaseSchema):
    message: str
    pagination: PaginationResponse
    data: list[PlanResponse]
    