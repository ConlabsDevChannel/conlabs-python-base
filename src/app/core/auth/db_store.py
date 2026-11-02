from datetime import UTC, datetime

from pydantic import ValidationError
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.auth.models import AuthSessionRecord
from app.core.auth.schemas import AuthSession
from app.core.auth.store import (
    SessionAlreadyExistsError,
    SessionStoreError
)

class DatabaseSessionStore:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        self._session_factory = session_factory

    async def create(
        self,
        key: str,
        session: AuthSession
    ) -> None:
        if session.is_expired(now=datetime.now(UTC)):
            raise SessionStoreError("만료된 세션은 저장할 수 없습니다.")

        record = AuthSessionRecord(
            token_hash=key,
            payload=session.model_dump_json(),
            expires_at=(
                session.expires_at.astimezone(UTC).replace(tzinfo=None)
            ),
        )

        try:
            try:
                async with self._session_factory() as db:
                    async with db.begin():
                        db.add(record)

            except IntegrityError as exc:
                # 실패한 트랜잭션 롤백됨
                # 무결성 오류 중복 확인
                async with self._session_factory() as db:
                    existing = await db.get(AuthSessionRecord, key)

                if existing is not None:
                    raise SessionAlreadyExistsError(
                        "동일한 키의 세션이 이미 존재함"
                    ) from exc

                raise SessionStoreError(
                    "세션 저장 중 데이터 무결성 오류 발생"
                ) from exc

        except SQLAlchemyError as exc:
            raise SessionStoreError(
                "세션을 저장할 수 없음"
            ) from exc

    # DB 세션 획득
    async def get(
        self,
        key: str
    ) -> AuthSession | None:
        now = datetime.now(UTC)
        db_now = now.replace(tzinfo=None)

        statement = select(AuthSessionRecord.payload).where(
            AuthSessionRecord.token_hash == key,
            AuthSessionRecord.expires_at > db_now,
        )

        try:
            async with self._session_factory() as db:
                payload = await db.scalar(statement)

        except SQLAlchemyError as exc:
            raise SessionStoreError(
                "세션을 조회할 수 없습니다."
            ) from exc

        if payload is None:
            return None

        try:
            session = AuthSession.model_validate_json(payload)

        except ValidationError as exc:
            raise SessionStoreError(
                "저장된 세션 데이터가 올바르지 않습니다."
            ) from exc

        if session.is_expired(now=datetime.now(UTC)):
            return None

        return session

    # DB 세션 파기
    async def delete(
        self,
        key: str
    ) -> None:
        # 삭제 쿼리
        statement = delete(AuthSessionRecord).where(
            AuthSessionRecord.token_hash == key,
        )

        try:
            async with self._session_factory() as db:
                async with db.begin():
                    await db.execute(statement)

        except SQLAlchemyError as exc:
            raise SessionStoreError(
                "세션을 삭제할 수 없음"
            ) from exc