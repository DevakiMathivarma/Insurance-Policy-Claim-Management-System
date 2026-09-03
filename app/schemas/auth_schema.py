from pydantic import EmailStr, Field

from app.models.user import UserRole
from app.schemas.common_schema import AppBaseSchema


# used for insurance agent, claims officer, and finance officer - the 3
# staff roles with no extra fields beyond the base login account.
# customer has its own dedicated create schema instead, same reasoning
# as tenant in the property platform
class RegisterRequest(AppBaseSchema):
    full_name: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=15)
    password: str = Field(..., min_length=8, max_length=100)
    role: UserRole


class LoginResponse(AppBaseSchema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(AppBaseSchema):
    refresh_token: str


class AccessTokenResponse(AppBaseSchema):
    access_token: str
    token_type: str = "bearer"


class ChangePasswordRequest(AppBaseSchema):
    current_password: str = Field(..., min_length=8, max_length=100)
    new_password: str = Field(..., min_length=8, max_length=100)