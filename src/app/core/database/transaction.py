from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from dataclasses import dataclass
from functools import wraps
from typing import ParamSpec, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

P = ParamSpec("P")
R = TypeVar("R")

class UnexpectedRollbackError(RuntimeError):
    pass

# 현재 트랜잭션 Rollback Only 상태
_rollback_only: ContextVar[bool | None] = ContextVar(
    "transaction_rollback_only",
    default=None
)

@dataclass
class TransactionState:
    session: AsyncSession
    rollback_only: bool = False

_transaction_state: ContextVar[TransactionState | None] = ContextVar(
    "transaction_state",
    default=None
)

def transactional(
    func: Callable[P, Awaitable[R]],
) -> Callable[P, Awaitable[R]]:

    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:

        # Service Method의 Session 인자 가져오기
        session = kwargs.get("session")

        # 세션이 없는 경우
        if session is None:
            raise RuntimeError(
                "@transactional은 session keyword 인자가 필요합니다."
            )

        if not isinstance(session, AsyncSession):
            raise TypeError(
                "session은 AsyncSession이어야 합니다."
            )

        state = _transaction_state.get()

        # 이미 시작된 트랜잭션에 참여 (REQUIRED)
        if state is not None:

            if state.session is not session:
                raise RuntimeError(
                    "연관된 트랜잭션 서비스는 반드시 동일한 AsyncSession이어야 합니다."
                )

            try:
                return await func(*args, **kwargs)
            except Exception:
                state.rollback_only = True
                raise

        # 최상위 서비스에서 트랜잭션 생성
        state = TransactionState(session=session)
        token = _transaction_state.set(state)

        try:
            async with session.begin():
                result = await func(*args, **kwargs)

                if state.rollback_only:
                    raise UnexpectedRollbackError(
                        "Rollback Only로 지정된 항목으로, Transaction 롤백 처리되었습니다."
                    )

                return result

        finally:
            _transaction_state.reset(token)

    return wrapper