from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.schemas.common_schema import AppBaseSchema
from app.schemas.user_schema import UserBasicResponse


class ClaimAssessmentCreate(AppBaseSchema):
    eligible_amount: Decimal = Field(..., gt=0)
    assessment_notes: str | None = Field(None, max_length=2000)
    recommendation: str | None = Field(None, max_length=200)


class ClaimAssessmentResponse(AppBaseSchema):
    id: int
    claim_id: int
    assessor: UserBasicResponse | None
    eligible_amount: Decimal
    assessment_notes: str | None
    recommendation: str | None
    assessed_at: datetime


class ClaimAssessmentMessageResponse(AppBaseSchema):
    message: str
    data: ClaimAssessmentResponse