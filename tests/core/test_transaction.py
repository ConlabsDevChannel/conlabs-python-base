import pytest

from sqlalchemy import Integer, String, select
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.database.base import Base
from app.core.database.transaction import (
    transactional,
    UnexpectedRollbackError,
)


class TransactionTestUser(Base):
    __tablename__ = "transaction_test_user"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    username: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )


@transactional
async def create_user(
    *,
    session: AsyncSession,
    username: str,
):
    session.add(TransactionTestUser(username=username))
    await session.flush()


@transactional
async def create_user_and_fail(
    *,
    session: AsyncSession,
    username: str,
):
    session.add(TransactionTestUser(username=username))
    await session.flush()
    raise ValueError("Test rollback")


@transactional
async def create_two_users(
    *,
    session: AsyncSession,
):
    await create_user(session=session, username="user1")
    await create_user(session=session, username="user2")


@transactional
async def create_user_with_caught_error(
    *,
    session: AsyncSession,
):
    await create_user(session=session, username="user1")

    try:
        await create_user_and_fail(
            session=session,
            username="user2",
        )
    except ValueError:
        pass

@pytest.fixture
async def session_factory():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
    )

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(
        engine,
        expire_on_commit=False,
    )

    yield factory

    await engine.dispose()

@pytest.fixture
async def session_factory():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
    )

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(
        engine,
        expire_on_commit=False,
    )

    yield factory

    await engine.dispose()    


@pytest.mark.asyncio
async def test_transaction_commit(session_factory):
    async with session_factory() as session:
        await create_user(
            session=session,
            username="tester",
        )

    async with session_factory() as session:
        result = await session.execute(
            select(TransactionTestUser)
        )
        users = result.scalars().all()

    assert len(users) == 1
    assert users[0].username == "tester"

@pytest.mark.asyncio
async def test_transaction_rollback(session_factory):
    async with session_factory() as session:
        with pytest.raises(ValueError):
            await create_user_and_fail(
                session=session,
                username="tester",
            )

    async with session_factory() as session:
        result = await session.execute(
            select(TransactionTestUser)
        )
        users = result.scalars().all()

    assert len(users) == 0

@pytest.mark.asyncio
async def test_nested_transaction(session_factory):
    async with session_factory() as session:
        await create_two_users(session=session)

    async with session_factory() as session:
        result = await session.execute(
            select(TransactionTestUser)
        )
        users = result.scalars().all()

    assert len(users) == 2

@pytest.mark.asyncio
async def test_rollback_only(session_factory):
    async with session_factory() as session:
        with pytest.raises(UnexpectedRollbackError):
            await create_user_with_caught_error(
                session=session,
            )

    async with session_factory() as session:
        result = await session.execute(
            select(TransactionTestUser)
        )
        users = result.scalars().all()

    assert len(users) == 0    