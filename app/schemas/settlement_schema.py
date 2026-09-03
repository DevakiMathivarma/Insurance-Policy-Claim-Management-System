from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.models.settlement import SettlementStatus
from app.schemas.common_schema import AppBaseSchema, PaginationResponse
from app.schemas.user_schema import UserBasicResponse


class SettlementCreate(AppBaseSchema):
    approved_amount: Decimal = Field(..., gt=0)
    payment_reference: str | None = Field(None, max_length=100)


class SettlementResponse(AppBaseSchema):
    id: int
    claim_id: int
    approved_amount: Decimal
    settlement_date: datetime | None
    payment_reference: str | None
    settlement_status: SettlementStatus
    processed_by: UserBasicResponse | None
    created_at: datetime


class SettlementMessageResponse(AppBaseSchema):
    message: str
    data: SettlementResponse


class SettlementPaginationResponse(AppBaseSchema):
    message: str
    data: list[SettlementResponse]
    pagination: PaginationResponse