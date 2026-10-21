from typing import TypeVar

from app.core.response.schemas import BaseResponse

T = TypeVar("T")

# 성공시의 메시지
def success_response(
    code: str = "S",
    message: str = "정상 처리되었습니다.",
    data: T | None = None,
) -> BaseResponse[T]:
    return BaseResponse[T](
        successCode="S",
        resCode=code,
        resMessage=message,
        data=data
    )

# 오류 발생시의 메시지
def failed_response(
    code: str,
    message: str,
    data: T | None = None,
) -> BaseResponse[T]:
    return BaseResponse[T](
        successCode="F",
        resCode=code,
        resMessage=message,
        data=data
    )