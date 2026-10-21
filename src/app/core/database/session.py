from collections.abc import AsyncIterator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker


def create_session_factory(
    engine: AsyncEngine
) -> async_sessionmaker[AsyncEngine]:
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False, # 비동기 환경에서 ORM 객체 접근 시 불필요한 암시적 DB 조회 여부
        autoflush=False, # 조회 전 변겅사항 자동 Flush 처리여부
    )

# DB 세션 조회
async def get_db_session(
    request: Request
) -> AsyncIterator[AsyncSession]:
    session_factory = request.app.state.db_session_factory

    async with session_factory() as session:
        yield session

    # 중요: 현재 위치에서 commit()을 자동으로 실행하지 않기 때문에 커밋과 롤백은 service 계층에서 명시적으로 관리