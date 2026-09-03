from datetime import date, datetime
from decimal import Decimal

from pydantic import Field

from app.models.claim import ClaimStatus
from app.schemas.common_schema import AppBaseSchema, PaginationResponse
from app.schemas.customer_schema import CustomerBasicResponse
from app.schemas.policy_schema import PolicyBasicResponse


class ClaimCreate(AppBaseSchema):
    policy_id: int
    claim_type: str = Field(..., min_length=2, max_length=100)
    incident_date: date
    claim_amount: Decimal = Field(..., gt=0)
    description: str | None = Field(None, max_length=2000)


class ClaimUpdate(AppBaseSchema):
    description: str | None = Field(None, max_length=2000)


class ClaimBasicResponse(AppBaseSchema):
    id: int
    claim_number: str
    status: ClaimStatus


class ClaimResponse(ClaimBasicResponse):
    policy: PolicyBasicResponse
    customer: CustomerBasicResponse
    claim_type: str
    incident_date: date
    claim_amount: Decimal
    description: str | None
    created_at: datetime
    updated_at: datetime


class ClaimMessageResponse(AppBaseSchema):
    message: str
    data: ClaimResponse


class ClaimPaginationResponse(AppBaseSchema):
    message: str
    data: list[ClaimResponse]
    pagination: PaginationResponse