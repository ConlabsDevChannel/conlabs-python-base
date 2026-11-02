from datetime import datetime

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

# 인증 사용자 또는 시스템 식별자 정보
class Principal(BaseModel):
    model_config = ConfigDict(
        extra="forbid", # 선언하지 않은 필드가 오면 오류 처리
        frozen=True, # 인증 정보 변경 불가 처리
    )

    # 인증 식별자
    subject_id: str = Field(min_length=1, max_length=200)

# 서버 저장 로그인 상태
class AuthSession(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    principal: Principal
    # AwareDatetime은 Timezone이 명시되어 있어야 함.
    created_at: AwareDatetime
    expires_at: AwareDatetime

    # Validation
    @model_validator(mode="after")
    def validate_expiration(self) -> "AuthSession":
        if self.expires_at <= self.created_at:
            raise ValueError("만료일시는 세션 생성일시보다 이후여야 합니다.")
        return self

    def is_expired(self, *, now: datetime) -> bool:
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("now에는 timezone 정보가 필요합니다.")

        return now >= self.expires_at