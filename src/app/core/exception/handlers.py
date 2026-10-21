import logging

# FastAPI 오류 응답 처리
from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# Exception 및 오류 응답 Schema
from app.core.exception.exceptions import AppException
from app.core.response.helpers import failed_response

# 로그 호출
logger = logging.getLogger(__name__)

# 공통 오류 응답
def error_json_response (
    code: str,
    message: str,
    status_code: int,
    data=None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    response = failed_response(
        code=code,
        message=message,
        data=data,
    )

    return JSONResponse(
        status_code=status_code,
        content=response.model_dump(
            by_alias=True,
            exclude_none=True,
            mode="json",
        ),
        headers=headers
    )

# 1. 사용자 정의 예외 처리
async def app_exception_handler(
    request: Request,
    exc: AppException,
) -> JSONResponse:
    logger.warning(
        "Application exception [%s]: %s",
        exc.code,
        exc.message
    )

    # 오류 발생 시 JSON 오류
    return error_json_response(
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code
    )

# 2. FastAPI HTTP 예외 처리
async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    logger.warning(
        "HTTP exception [%s] %s %s: %s",
        exc.status_code,
        request.method,
        request.url.path,
        exc.detail
    )

    return error_json_response(
        code=f"HTTP_{exc.status_code}",
        message=(
            exc.detail
            if isinstance(exc.detail, str)
            else "HTTP 요청 처리 중 오류가 발생했습니다."
        ),
        status_code=exc.status_code,
        headers=exc.headers
    )

# 3. 데이터 검증 예외 처리(Validation)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    errors = [
        {
            "field": ".".join(str(part) for part in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]

    logger.warning(
        "Request validation failed [%s %s]: %s",
        request.method,
        request.url.path,
        errors,
    )

    return error_json_response(
        code="VE",
        message="요청 데이터가 올바르지 않습니다.",
        status_code=422,
        data=errors
    )

# 4. 예상하지 못한 서버 오류 처리
async def unhandled_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    logger.error(
        "Unhandled exception [%s %s]",
        request.method,
        request.url.path,
        exc_info=(type(exc), exc, exc.__traceback__),
    )

    return error_json_response(
        code="ISE",
        message="서버 내부 오류가 발생했습니다.",
        status_code=500,
    )