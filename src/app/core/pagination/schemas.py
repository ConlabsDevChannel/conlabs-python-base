from typing import Generic, TypeVar

from pydantic import BaseModel, Field, computed_field # computed_field는 Pydantic이 계산된 필드를 포함시킴

T = TypeVar("T")

class PageRequest(BaseModel):
    page: int = Field(default=1, ge=1) # 기본 페이지 1, 최소 1
    size: int = Field(default=20, ge=1, le=100) # 기본 20, 최소 1, 최대 100

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size

class PageResponse(BaseModel, Generic[T]):
    items: list[T]
    page: int
    size: int
    total_elements: int = Field(ge=0)

    @computed_field
    @property
    def total_pages(self) -> int:
        return (
            (self.total_elements + self.size - 1) // self.size
            if self.total_elements > 0
            else 0
        )

    @computed_field
    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages

    @computed_field
    @property
    def has_previous(self) -> bool:
        return self.page > 1