from typing import Annotated, Literal

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
)

from app.core.auth.schemas import Principal

# 인증 단계 완료 처리
class Authenticated(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    status: Literal["authenticated"] = "authenticated"

    principal: Principal

# 비밀번호 검증 후 2차 인증 처리
class SecondFactorRequired(BaseModel):
    model_config = ConfigDict(
            extra="forbid",
            frozen=True,
        )

    status: Literal["second_factor_required"] = "second_factor_required"

    challenge_token: str = Field(min_length=1, repr=False)

    expires_at: AwareDatetime

LoginResult = Annotated[
    Authenticated | SecondFactorRequired,
    Field(discriminator="status"),
]