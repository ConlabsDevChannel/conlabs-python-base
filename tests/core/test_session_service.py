import hashlib
from datetime import timedelta

import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.auth.db_store import DatabaseSessionStore
from app.core.auth.models import AuthSessionRecord
from app.core.auth.schemas import AuthSession, Principal
from app.core.auth.service import SessionService
from app.core.database.session import create_session_factory

@pytest.fixture
async def session_factory():
    # 테스트 전용 DB 호출: SQLite
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
    )

    try:
        async with engine.begin() as connection:
            # 인증 테스트 전용 테이블 생성
            await connection.run_sync(
                AuthSessionRecord.__table__.create,
            )

        yield create_session_factory(engine)

    finally:
        # 테스트 종료 혹은 실패 등 어떤 상태든 DB를 종료시킨다.
        await engine.dispose()

@pytest.fixture
def session_service(session_factory):
    store = DatabaseSessionStore(
        session_factory=session_factory,
    )

    return SessionService(
        store=store,
        ttl=timedelta(hours=1)
    )

async def test_issue_and_resolve(session_service):
    principal = Principal(subject_id="user-1")

    # 토큰 발생
    token = await session_service.issue(principal)

    assert isinstance(token, str)
    assert token

    resolved = await session_service.resolve(token)

    # 세션 확인
    assert resolved == principal

async def test_issue_persists_hashed_token(
    session_factory,
    session_service,
):
    principal = Principal(subject_id="user-1")

    token = await session_service.issue(principal)
    token_hash = hashlib.sha256(
        token.encode("utf-8"),
    ).hexdigest()

    # 별도 세션에서 DB 조회하여 데이터 Commit 여부 확인
    async with session_factory() as db:
        record = await db.get(
            AuthSessionRecord,
            token_hash,
        )

        assert record is not None
        assert record.token_hash == token_hash
        assert record.token_hash != token
        assert token not in record.payload

        # 저장 JSON을 실제 인증 세션 모델로 복원
        saved_session = AuthSession.model_validate_json(
            record.payload,
        )

        assert saved_session.principal == principal
        assert (
            saved_session.expires_at - saved_session.created_at == timedelta(hours=1)
        )


@pytest.mark.parametrize(
    "token",
    ["unknown-token", ""],
)
async def test_resolve_invalid_token(
    session_service,
    token,
):
    resolved = await session_service.resolve(token)

    assert resolved is None

async def test_revoke_deletes_sesion(
    session_factory,
    session_service,
):
    token = await session_service.issue(
        Principal(subject_id="user-1"),
    )

    await session_service.revoke(token)

    assert await session_service.resolve(token) is None

    token_hash = hashlib.sha256(
        token.encode("utf-8"),
    ).hexdigest()

    # 조회만 막힌 것이 아니라 DB에서도 삭제되었는지 확인합니다.
    async with session_factory() as db:
        record = await db.get(
            AuthSessionRecord,
            token_hash,
        )

        assert record is None


async def test_revoke_is_idempotent(session_service):
    token = await session_service.issue(
        Principal(subject_id="user-1"),
    )

    await session_service.revoke(token)

    # 이미 폐기했거나 존재하지 않는 토큰도
    # 오류 없이 처리되어야 합니다.
    await session_service.revoke(token)
    await session_service.revoke("unknown-token")
    await session_service.revoke("")

    assert await session_service.resolve(token) is None