import asyncio
from typing import Protocol

from argon2 import PasswordHasher, Type
from argon2.exceptions import (
    HashingError,
    InvalidHashError,
    VerificationError,
    VerifyMismatchError,
)

class PasswordHashError(RuntimeError):
    """비밀번호 해시 생성/검증 작업 실패."""

class PasswordVerifier(Protocol):
    """입력 비밀번호와 저장된 해시 비교"""

    async def verify(
        self,
        *,
        password: str,
        password_hash: str,
    ) -> bool:
        """
        비밀번호가 일치하면 True, 일치하지 않으면 False 반환
        """

class Argon2PasswordHasher:
    def __init__(self) -> None:
        # OWASP 최소 지침 기준
        self._hasher = PasswordHasher(
            type=Type.ID, # Argon2id 사용
            memory_cost=19 * 1024, # 작업당 19MiB 메모리 사모
            time_cost=2, # 계산 반복 횟수
            parallelism=1, # 내부 병렬 처리 수준
        )

    async def hash(self, *, password: str) -> str:
        try:
            return await asyncio.to_thread(
                self._hasher.hash,
                password,
            )

        except HashingError as exc:
            raise PasswordHashError(
                "비밀번호 해시 생성 오류"
            ) from exc

    async def verify(
        self, 
        *,
        password: str,
        password_hash: str,
    ) -> bool:
        try:
            return await asyncio.to_thread(
                self._hasher.verify,
                password_hash,
                password,
            )

        except VerifyMismatchError:
            # 해시는 맞으나 비밀번호가 틀림
            return False

        except (InvalidHashError, VerificationError) as exc:
            # 손상된 해시 또는 검증 장애로 처리
            raise PasswordHashError(
                "비밀번호 해시 검증 불가"
            ) from exc