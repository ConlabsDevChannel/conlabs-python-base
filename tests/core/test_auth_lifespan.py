import hashlib
from datetime import timedelta

import pytest
from httpx import ASGITransport, AsyncClient

import app.factory as factory_module
from app.core.auth.models import AuthSessionRecord
from app.core.auth.schemas import AuthSession, Principal
from app.core.auth.service import SessionService
from app.core.config import Settings


@pytest.fixture
def test_settings(monkeypatch):
    settings = Settings(
        # 개발용 .env를 읽지 않고 테스트 설정을 직접 지정합니다.
        _env_file=None,
        database_url="sqlite+aiosqlite:///:memory:",
        database_echo=False,
        db_migration_auto_upgrade=False,
        auth_session_enabled=False,
        # 기본값과 다른 값으로 설정 전달 여부를 확인합니다.
        auth_session_ttl_seconds=900,
        debug=False,
    )

    # factory.py가 사용하는 설정 조회 함수를 교체합니다.
    # 실제 get_settings()의 캐시에는 영향을 주지 않습니다.
    monkeypatch.setattr(
        factory_module,
        "get_settings",
        lambda: settings,
    )

    # 이번 테스트는 서비스 등록 검증에 집중합니다.
    # 전역 로깅 설정 변경과 로그 파일 생성을 방지합니다.
    monkeypatch.setattr(
        factory_module,
        "setup_logging",
        lambda **kwargs: None,
    )

    return settings


@pytest.fixture
async def started_auth_app(test_settings):
    test_settings.auth_session_enabled = True

    app = factory_module.create_app()

    # 실제 앱 시작·종료 처리를 실행합니다.
    async with app.router.lifespan_context(app):
        session_factory = app.state.db_session_factory

        # 자동 마이그레이션은 끄고 필요한 테이블만 준비합니다.
        # 앱이 생성한 DB 세션 팩토리를 그대로 사용합니다.
        async with session_factory() as db:
            async with db.begin():
                connection = await db.connection()

                await connection.run_sync(
                    AuthSessionRecord.__table__.create,
                )

        yield app

    # context를 벗어나면 실제 lifespan의 종료 처리가 실행됩니다.

# 테스트 인증 비활성화 테스트
async def test_auth_disabled(test_settings):
    app = factory_module.create_app()

    async with app.router.lifespan_context(app):
        assert app.state.auth_session_service is None

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/health")

        # 인증을 끈 상태에서도 공개 API는 정상 동작합니다.
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}    

# 앱이 등록한 인스턴스로 발급, 조회, 폐기 확인
async def test_registered_service_lifecycle(started_auth_app):
    service = started_auth_app.state.auth_session_service

    assert isinstance(service, SessionService)

    principal = Principal(subject_id="user-1")

    token = await service.issue(principal)

    assert await service.resolve(token) == principal

    await service.revoke(token)

    assert await service.resolve(token) is None        

# ttl 적용 확인 테스트
async def test_registered_service_uses_configured_ttl(
    started_auth_app,
    test_settings,
):
    service = started_auth_app.state.auth_session_service

    token = await service.issue(
        Principal(subject_id="user-1"),
    )
    token_hash = hashlib.sha256(
        token.encode("utf-8"),
    ).hexdigest()

    session_factory = started_auth_app.state.db_session_factory

    async with session_factory() as db:
        record = await db.get(
            AuthSessionRecord,
            token_hash,
        )

        assert record is not None

        saved_session = AuthSession.model_validate_json(
            record.payload,
        )

        actual_ttl = (
            saved_session.expires_at - saved_session.created_at
        )

        assert actual_ttl == timedelta(
            seconds=test_settings.auth_session_ttl_seconds,
        )