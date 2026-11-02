import hashlib
import secrets

from datetime import UTC, datetime, timedelta

from app.core.auth.schemas import AuthSession, Principal
from app.core.auth.store import SessionStore

class SessionService:
    def __init__(
        self,
        store: SessionStore,
        *,
        ttl: timedelta,
    ) -> None:
        if ttl <= timedelta(0):
            raise ValueError("세션 유효 시간은 0보다 커야 합니다.")

        self._store = store
        self._ttl = ttl

    # 해시 토큰 생성
    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    # 새 세션 저장 후 클라이언트에 전달할 원본 토큰 반환
    async def issue(self, principal: Principal) -> str:
        token = secrets.token_urlsafe(32)
        now = datetime.now(UTC)

        session = AuthSession(
            principal=principal,
            created_at=now,
            expires_at=now + self._ttl,
        )

        await self._store.create(
            key=self._hash_token(token),
            session=session,
        )

        return token

    # 토큰이 유효한 경우 인증 ID를 반환한다.
    async def resolve(self, token: str) -> Principal | None:
        # 토큰이 없으면 None 반환
        if not token:
            return None

        session = await self._store.get(
            key=self._hash_token(token),
        )

        # 세션이 없으면 None 반환
        if session is None:
            return None

        # 저장소 조회 직후 만료되는 경우에도 None 반환
        if session.is_expired(now=datetime.now(UTC)):
            return None

        return session.principal

    # 세션 페기 처리
    async def revoke(self, token: str) -> None:
        if not token:
            return

        await self._store.delete(
            key=self._hash_token(token),
        )