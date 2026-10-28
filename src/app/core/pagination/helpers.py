from typing import TypeVar

from app.core.pagination.schemas import PageRequest, PageResponse

T = TypeVar("T")

def create_page(
    items: list[T],
    total_elements: int,
    request: PageRequest,
) -> PageResponse[T]:
    return PageResponse[T](
        items=items,
        page=request.page,
        size=request.size,
        total_elements=total_elements,
    )