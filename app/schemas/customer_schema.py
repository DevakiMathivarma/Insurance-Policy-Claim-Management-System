from datetime import date, datetime

from pydantic import EmailStr, Field, model_validator

from app.schemas.common_schema import AppBaseSchema, PaginationResponse
from app.schemas.user_schema import UserBasicResponse

MINIMUM_CUSTOMER_AGE = 18


# creates both the login account and the customer profile together, in one call 
class CustomerCreate(AppBaseSchema):
    full_name: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=15)
    password: str = Field(..., min_length=8, max_length=100)
    date_of_birth: date
    address: str | None = Field(None, max_length=300)
    identification_number: str = Field(..., min_length=3, max_length=50)
    occupation: str | None = Field(None, max_length=150)

    # validate customer age since it only needs this one field
    @model_validator(mode="after")
    def check_minimum_age(self):
        today = date.today()
        age = today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        if age < MINIMUM_CUSTOMER_AGE:
            raise ValueError(f"Customer must be at least {MINIMUM_CUSTOMER_AGE} years old.")
        return self


class CustomerUpdate(AppBaseSchema):
    full_name: str | None = Field(None, min_length=3, max_length=100)
    phone: str | None = Field(None, min_length=10, max_length=15)
    address: str | None = Field(None, max_length=300)
    occupation: str | None = Field(None, max_length=150)


class CustomerBasicResponse(AppBaseSchema):
    id: int
    user: UserBasicResponse


class CustomerResponse(CustomerBasicResponse):
    date_of_birth: date
    address: str | None
    identification_number: str
    occupation: str | None
    created_by: UserBasicResponse | None
    created_at: datetime
    updated_at: datetime


class CustomerMessageResponse(AppBaseSchema):
    message: str
    data: CustomerResponse


class CustomerPaginationResponse(AppBaseSchema):
    message: str
    pagination: PaginationResponse
    data: list[CustomerResponse]
    