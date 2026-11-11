from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

# 비밀번호 인증 공통 계정 정보
class PasswordAccount(BaseModel):

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    # 인증 완료 후 사용할 Principal.subject_id 식별자
    subject_id: str = Field(
        min_length=1,
        max_length=200,
    )

    # 저장된 비밀번호 해시
    # repr=False는 객체 출력시 해시 노출 최소화
    password_hash: str = Field(
        min_length=1,
        repr=False,
    )

    # 서비스별 계정 상태롤 로그인 허용 여부로 변환한 값
    is_active: bool

    # 2차 인증 사용여부
    requires_second_factor: bool

# 각 서비스가 구현해야 함
class AccountProvider(Protocol):

    async def find_by_login_id(
        self,
        *,
        login_id: str,
    ) -> PasswordAccount | None:
        """
        로그인 ID 계정 정보 반환
        없으면 None 반환
        비밀번호 검증, 세션 발급 미수행
        DB 장애등으로 발생한 조회 실패는 None으로 숨기지 않음
        """
        