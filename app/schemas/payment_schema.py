from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.models.payment import PaymentMethod, PaymentStatus
from app.schemas.common_schema import AppBaseSchema, PaginationResponse


class PaymentCreate(AppBaseSchema):
    amount: Decimal = Field(..., gt=0)
    payment_method: PaymentMethod
    transaction_id: str = Field(..., min_length=5, max_length=100)


class PaymentResponse(AppBaseSchema):
    id: int
    policy_id: int
    amount: Decimal
    payment_date: datetime
    payment_method: PaymentMethod
    transaction_id: str
    status: PaymentStatus


class PaymentMessageResponse(AppBaseSchema):
    message: str
    data: PaymentResponse


class PaymentPaginationResponse(AppBaseSchema):
    message: str
    pagination: PaginationResponse
    data: list[PaymentResponse]
    