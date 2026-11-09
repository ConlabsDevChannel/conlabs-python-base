from datetime import UTC, datetime, timedelta
from typing import Annotated
from unittest.mock import AsyncMock

import pytest
from fastapi import Depends
from httpx import ASGITransport, AsyncClient

from app.core.auth.dependencies import (
    SESSION_COOKIE_NAME,
    get_optional_principal,
    require_principal,
)
from app.core.auth.schemas import AuthSession, Principal
from app.core.auth.service import SessionService
from app.core.auth.store import SessionStore, SessionStoreError


@pytest.fixture
def session_store():
    # DB 대신 사용할 비동기 저장소 대역입니다.
    # 각 테스트에서 조회 결과나 오류를 직접 지정합니다.
    store = AsyncMock(spec=SessionStore)
    store.get.return_value = None

    return store


@pytest.fixture
def auth_service(session_store):
    # 서비스와 Dependency는 실제 구현을 사용합니다.
    return SessionService(
        store=session_store,
        ttl=timedelta(hours=1),
    )


@pytest.fixture
async def auth_client(app, auth_service):
    # app은 tests/conftest.py의 fixture입니다.
    # 공통 AppException 처리기가 이미 등록되어 있습니다.
    app.state.auth_session_service = auth_service

    @app.get("/public")
    async def public():
        return {"status": "ok"}

    @app.get("/optional")
    async def optional(
        principal: Annotated[
            Principal | None,
            Depends(get_optional_principal),
        ],
    ):
        return {
            "subject_id": (
                principal.subject_id
                if principal is not None
                else None
            ),
        }

    @app.get("/protected")
    async def protected(
        principal: Annotated[
            Principal,
            Depends(require_principal),
        ],
    ):
        return {"subject_id": principal.subject_id}

    # 앱 lifespan을 실행하지 않고 테스트용 서비스만 연결합니다.
    # 개발용 DB나 외부 HTTP 클라이언트를 생성하지 않습니다.
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

async def test_optional_without_cookie(auth_client):
    response = await auth_client.get("/optional")

    assert response.status_code == 200
    assert response.json() == {"subject_id": None}


async def test_protected_without_cookie(auth_client):
    response = await auth_client.get("/protected")

    assert response.status_code == 401
    assert response.json()["resCode"] == "AUTH_REQUIRED"        

async def test_protected_with_valid_cookie(
    auth_client,
    session_store,
):
    now = datetime.now(UTC)

    session_store.get.return_value = AuthSession(
        principal=Principal(subject_id="user-1"),
        created_at=now,
        expires_at=now + timedelta(hours=1),
    )

    # 서버가 읽는 이름으로 클라이언트 쿠키를 설정합니다.
    auth_client.cookies.set(
        SESSION_COOKIE_NAME,
        "valid-token",
    )

    response = await auth_client.get("/protected")

    assert response.status_code == 200
    assert response.json() == {"subject_id": "user-1"}    



@pytest.mark.parametrize(
    "token",
    ["unknown-token", ""],
)
async def test_protected_with_invalid_cookie(
    auth_client,
    token,
):
    # 저장소 fixture의 기본 조회 결과는 None입니다.
    auth_client.cookies.set(
        SESSION_COOKIE_NAME,
        token,
    )

    response = await auth_client.get("/protected")

    assert response.status_code == 401
    assert response.json()["resCode"] == "INVALID_SESSION"


async def test_protected_with_expired_session(
    auth_client,
    session_store,
):
    now = datetime.now(UTC)

    # 저장소가 만료 세션을 반환하더라도 서비스가 거부해야 합니다.
    session_store.get.return_value = AuthSession(
        principal=Principal(subject_id="user-1"),
        created_at=now - timedelta(hours=2),
        expires_at=now - timedelta(hours=1),
    )

    auth_client.cookies.set(
        SESSION_COOKIE_NAME,
        "expired-token",
    )

    response = await auth_client.get("/protected")

    assert response.status_code == 401
    assert response.json()["resCode"] == "INVALID_SESSION"    

@pytest.mark.parametrize(
    "path",
    ["/optional", "/protected"],
)
async def test_auth_service_disabled(
    app,
    auth_client,
    path,
):
    # 앱에서 인증 기능을 비활성화한 상태를 재현합니다.
    app.state.auth_session_service = None

    response = await auth_client.get(path)

    assert response.status_code == 503
    assert response.json()["resCode"] == "AUTH_UNAVAILABLE"


async def test_public_when_auth_disabled(
    app,
    auth_client,
):
    app.state.auth_session_service = None

    # 인증 Dependency를 사용하지 않는 공개 API는 계속 동작합니다.
    response = await auth_client.get("/public")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}    

@pytest.mark.parametrize(
    "path",
    ["/optional", "/protected"],
)
async def test_store_error_returns_503(
    auth_client,
    session_store,
    path,
):
    # await store.get(...) 호출 시 저장소 오류를 발생시킵니다.
    session_store.get.side_effect = SessionStoreError(
        "테스트용 저장소 장애",
    )

    # 쿠키가 있어야 실제 저장소 조회까지 진행됩니다.
    auth_client.cookies.set(
        SESSION_COOKIE_NAME,
        "some-token",
    )

    response = await auth_client.get(path)

    assert response.status_code == 503
    assert response.json()["resCode"] == "AUTH_UNAVAILABLE"    