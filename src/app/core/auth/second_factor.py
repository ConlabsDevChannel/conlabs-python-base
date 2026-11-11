from typing import Protocol

from app.core.auth.results import SecondFactorRequired

class SecondFactorError(RuntimeError):
    """2차 인증 처리 중 오류 발생"""

class SecondFactorStarter(Protocol):
    async def begin(
        self,
        *,
        subject_id: str,
    ) -> SecondFactorRequired:
        """
        비밀번호 검증 통과한 사용자의 인증 진행 정보 생성

        - 로그인 세션은 발급하지 않음
        - 생성한 진행정보의 토큰과 만료시간 반환
        - 오류는 SecondFactorError로 전달
        """