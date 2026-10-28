from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.pagination.schemas import PageRequest


class TodoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)


class TodoUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    completed: bool | None = None

    @model_validator(mode="after")
    def validate_patch(self) -> "TodoUpdate":
        if not self.model_fields_set:
            raise ValueError("수정할 필드를 하나 이상 지정하세요.")
        for field in ("title", "completed"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field}에는 null을 지정할 수 없습니다.")
        return self


class TodoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    completed: bool
    created_at: datetime
    updated_at: datetime


class TodoListQuery(PageRequest):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    q: str | None = Field(default=None, min_length=1, max_length=200)
    completed: bool | None = None
    sort: Literal["id", "title", "created_at", "updated_at"] = "created_at"
    direction: Literal["asc", "desc"] = "desc"
