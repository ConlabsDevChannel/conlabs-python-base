from typing import Annotated

from fastapi import Depends, Request

from app.core.auth.schemas import Principal
from app.core.auth.service import SessionService
from app.core.auth.store import SessionStoreError
from app.core.exception.exceptions import AppException

SESSION_COOKIE_NAME = "auth_session"

# 시작 시 등록한 세션 서비스 가져옴
def get_session_service(request: Request) -> SessionService:
    service = getattr(
        request.app.state,
        "auth_session_service",
        None,
    )

    if service is None:
        raise AppException(
            code="AUTH_UNAVAILABLE",
            message="인증 서비스를 사용할 수 없습니다.",
            status_code=503,
        )

    return service

# 쿠키가 없으면 None, 유효하면 인증 주체 반환
async def get_optional_principal(
    request: Request,
    service: Annotated[SessionService, Depends(get_session_service)],
) -> Principal | None:
    # 토큰을 쿠키에서 가져옴
    token = request.cookies.get(SESSION_COOKIE_NAME)

    # 쿠키 자체가 없는 경우만 익명 요청으로 처리
    if token is None:
        return None

    try:
        principal = await service.resolve(token)
    except SessionStoreError as exc:
        raise AppException(
            code="AUTH_UNAVAILABLE",
            message="인증 서비스를 사용할 수 없습니다.",
            status_code=503,
        ) from exc

    if principal is None:
        raise AppException(
            code="INVALID_SESSION",
            message="세션이 유효하지 않거나 만료되었습니다.",
            status_code=401,
        )

    return principal

# 로그인이 필요한 경우(익명 요청 불가능)
async def require_principal(
    principal: Annotated[
        Principal | None,
        Depends(get_optional_principal)
    ],
) -> Principal:
    if principal is None:
        raise AppException(
            code="AUTH_REQUIRED",
            message="로그인이 필요합니다.",
            status_code=401
        )

    return principal