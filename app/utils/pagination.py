from math import ceil

from app.schemas.common_schema import PaginationResponse


def get_pagination(total_records: int, page: int, page_size: int) -> PaginationResponse:

    total_pages = ceil(total_records / page_size) if total_records else 1

    return PaginationResponse(
        total_records=total_records,
        current_page=page,
        limit=page_size,
        total_pages=total_pages
    )


def get_offset(page: int, page_size: int) -> int:

    return (page - 1) * page_size