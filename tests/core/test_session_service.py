import hashlib
from datetime import UTC, datetime, timedelta
from typing import Annotated
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.auth.db_store import DatabaseSessionStore
from app.core.auth.models import AuthSessionRecord
from app.core.auth.schemas import AuthSession, Principal
from app.core.auth.service import SessionService
from app.core.database.session import create_session_factory
from app.core.auth.store import (
    SessionAlreadyExistsError,
    SessionStoreError
)

from fastapi import Depends
from httpx import ASGITransport, AsyncClient

from app.core.auth.dependencies import (
    SESSION_COOKIE_NAME,
    get_optional_principal,
    require_principal,
)

import app.core.auth.db_store as db_store_module
import app.core.auth.service as service_module

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

@pytest.fixture
def clock(monkeypatch):
    class TestClock:
        now = datetime(2026, 1, 1, tzinfo=UTC)

    clock = TestClock()

    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            # 타임존을 지정하여 현재시각 읽기
            if tz is None:
                raise AssertionError("timezone을 지정해야 합니다.")

            return clock.now.astimezone(tz)

    # 테스트 종료 후 변경을 자동으로 되돌림
    monkeypatch.setattr(service_module, "datetime", FixedDatetime)
    monkeypatch.setattr(db_store_module, "datetime", FixedDatetime)

    return clock

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

@pytest.mark.parametrize(
    "elapsed, expected_valid",
    [
        (timedelta(hours=1) - timedelta(microseconds=1), True),
        (timedelta(hours=1), False),
        (timedelta(hours=1, seconds=1), False)
    ],
)
async def test_session_expiration(
    session_service,
    clock,
    elapsed,
    expected_valid,
):
    principal = Principal(subject_id="user-1")
    token = await session_service.issue(principal)

    # 발급 시점에서 만료직전, 정확한 시간, 만료 이후로 이동
    clock.now += elapsed

    resolved = await session_service.resolve(token)

    if expected_valid:
        # 세션이 살아있는 시점
        assert resolved == principal
    else:
        # 세션이 만료된 시점
        assert resolved is None

async def test_resolve_does_not_extend_expiration(
    session_factory,
    session_service,
    clock,
):
    principal = Principal(subject_id="user-1")
    token = await session_service.issue(principal)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

    async with session_factory() as db:
        record = await db.get(AuthSessionRecord, token_hash)
        assert record is not None
        original_expiration = record.expires_at

    clock.now += timedelta(minutes=30)

    assert await session_service.resolve(token) == principal

    # 별도 DB 세션 조회하여 만료시각 유지 확인
    async with session_factory() as db:
        record = await db.get(AuthSessionRecord, token_hash)
        assert record is not None
        assert record.expires_at == original_expiration

    # 중간 조회 시 원래 만료시각에는 인증되지 않아야 함
    clock.now += timedelta(minutes=30)

    assert await session_service.resolve(token) is None

# 중복 키가 기존 세션을 덮어쓰지 않는지 확인하기
async def test_store_rejects_duplicate_key(
    session_factory,
    clock,
):
    store = DatabaseSessionStore(
        session_factory=session_factory,
    )

    key = "a" * 64

    original = AuthSession(
        principal=Principal(subject_id="user-1"),
        created_at=clock.now,
        expires_at=clock.now + timedelta(hours=1),
    )
    replacement = AuthSession(
        principal=Principal(subject_id="user-2"),
        created_at=clock.now,
        expires_at=clock.now + timedelta(hours=1),
    )

    await store.create(key=key, session=original)

    # 같은 키로 다른 사용자의 세션을 저장하면 거부해야 함
    with pytest.raises(SessionAlreadyExistsError):
        await store.create(key=key, session=replacement)

    # 실패 후에도 기존 데이터가 유지되어야 함
    saved = await store.get(key=key)

    assert saved == original

# 이미 만료된 세션은 저장하지 않아야 함을 테스트
async def test_store_rejects_expired_session(
    session_factory,
    clock,
):
    store = DatabaseSessionStore(
        session_factory=session_factory,
    )
    key = "b" * 64

    # 2시간 전에 생성, 1시간 전에 만료
    expired_session = AuthSession(
        principal=Principal(subject_id="user-1"),
        created_at=clock.now - timedelta(hours=2),
        expires_at=clock.now - timedelta(hours=1),
    )

    with pytest.raises(SessionStoreError):
        await store.create(key=key, session=expired_session)

    # 만료된 데이터는 db에 저장되면 안됨
    async with session_factory() as db:
        record = await db.get(AuthSessionRecord, key)

        assert record is None

# 손상된 payload는 오류로 처리
async def test_store_rejects_corrupted(
    session_factory,
    clock,
):
    store = DatabaseSessionStore(
        session_factory=session_factory,
    )
    key = "c" * 64

    # 손상된 데이터 생성
    async with session_factory() as db:
        async with db.begin():
            db.add(
                AuthSessionRecord(
                    token_hash=key,
                    payload="invalid-json",
                    expires_at=(
                        clock.now + timedelta(hours=1)
                    ).replace(tzinfo=None),
                ),
            )

    # 데이터 손상인 경우 저장소 오류로 전달
    with pytest.raises(SessionStoreError):
        await store.get(key=key)