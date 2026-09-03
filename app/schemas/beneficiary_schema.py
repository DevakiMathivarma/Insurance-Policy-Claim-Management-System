from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.schemas.common_schema import AppBaseSchema


class BeneficiaryCreate(AppBaseSchema):
    name: str = Field(..., min_length=2, max_length=150)
    relationship_type: str = Field(..., min_length=2, max_length=50)
    percentage: Decimal = Field(..., gt=0, le=100)
    phone: str | None = Field(None, max_length=15)
    identification_number: str | None = Field(None, max_length=50)


class BeneficiaryUpdate(AppBaseSchema):
    name: str | None = Field(None, min_length=2, max_length=150)
    relationship_type: str | None = Field(None, min_length=2, max_length=50)
    percentage: Decimal | None = Field(None, gt=0, le=100)
    phone: str | None = Field(None, max_length=15)
    identification_number: str | None = Field(None, max_length=50)


class BeneficiaryResponse(AppBaseSchema):
    id: int
    policy_id: int
    name: str
    relationship_type: str
    percentage: Decimal
    phone: str | None
    identification_number: str | None
    created_at: datetime
    updated_at: datetime


class BeneficiaryMessageResponse(AppBaseSchema):
    message: str
    data: BeneficiaryResponse


class BeneficiaryListResponse(AppBaseSchema):
    message: str
    data: list[BeneficiaryResponse]