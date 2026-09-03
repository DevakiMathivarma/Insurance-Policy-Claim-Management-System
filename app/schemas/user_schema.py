# app/schemas/user_schema.py

from datetime import datetime

from pydantic import EmailStr, Field

from app.models.user import UserRole
from app.schemas.common_schema import AppBaseSchema, PaginationResponse


class UserBasicResponse(AppBaseSchema):
    id: int
    full_name: str
    email: EmailStr
    phone: str
    role: UserRole


class UserResponse(UserBasicResponse):
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserActivationRequest(AppBaseSchema):
    is_active: bool


class UserMessageResponse(AppBaseSchema):
    message: str
    data: UserResponse


class UserPaginationResponse(AppBaseSchema):
    message: str
    pagination: PaginationResponse
    data: list[UserResponse]
    