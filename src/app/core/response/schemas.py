# 기본 스키마 구현
from typing import Generic, TypeVar
from pydantic import BaseModel, Field

# 이 구조는 과거에 만들어두었던 Java의 BaseResponse<T>의 구현
# T의 경우 Schema의 Key를 가진 class
T = TypeVar("T")

class BaseResponse(BaseModel, Generic[T]):
    success_code: str = Field(alias="successCode")
    res_code: str = Field(alias="resCode")
    res_message: str = Field(alias="resMessage")
    data: T | None = None