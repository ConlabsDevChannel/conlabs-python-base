from typing import Protocol

from app.core.auth.schemas import AuthSession

class SessionStoreError(RuntimeError):
    """세션 저장소 작업 실패"""

class SessionAlreadyExistsError(SessionStoreError):
    """동일한 키의 세션이 이미 존재"""

class SessionStore(Protocol):
    async def create(
        self,
        key: str,
        session: AuthSession
    ) -> None:
        """
        세션을 신규 저장
        
        key는 원본 토큰이 아닌 Hash값.
        만료 시작까지 저장하며, 기존 키를 덮어쓰지 않음

        SessionAlreadyExistsError: 키가 이미 있을 경우
        SessionStoreError: 연결 장애 등으로 저장 실패 시
        """

    async def get(
        self,
        key: str,
    ) -> AuthSession | None:
        """
        유효 세션 반환

        세션이 없으거나 만료 시 None 반환
        데이터가 손상되거나 실패하면 SessionStoreError 발생
        """

    async def delete(
        self,
        key: str
    ) -> None:
        """
        세션을 삭제한다.

        이미 없는 키를 삭제해도 성공으로 처리한다.
        """