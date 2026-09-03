from pydantic import BaseModel, ConfigDict


class AppBaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    message: str


class PaginationResponse(AppBaseSchema):
    total_records: int
    current_page: int
    limit: int
    total_pages: int