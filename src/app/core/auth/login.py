from app.core.auth.accounts import AccountProvider
from app.core.auth.passwords import (
    PasswordHashError,
    PasswordVerifier,
)
from app.core.auth.results import Authenticated, LoginResult
from app.core.auth.schemas import Principal
from app.core.auth.second_factor import (
    SecondFactorError,
    SecondFactorStarter,
)
from app.core.exception.exceptions import AppException


class PasswordLoginService:
    def __init__(
        self,
        *,
        accounts: AccountProvider,
        password_verifier: PasswordVerifier,
        dummy_password_hash: str,
        second_factor: SecondFactorStarter | None = None,
    ) -> None:
        self._accounts = accounts
        self._password_verifier = password_verifier
        self._dummy_password_hash = dummy_password_hash
        self._second_factor = second_factor

    async def login(
        self,
        *,
        login_id: str,
        password: str,
    ) -> LoginResult:
        account = await self._accounts.find_by_login_id(
            login_id=login_id,
        )

        # 계정이 없어도 해시 검증을 수행합니다.
        # 계정 존재 여부에 따른 처리 시간 차이를 줄이기 위함입니다.
        password_hash = (
            account.password_hash
            if account is not None
            else self._dummy_password_hash
        )

        try:
            matches = await self._password_verifier.verify(
                password=password,
                password_hash=password_hash,
            )

        except PasswordHashError as exc:
            raise AppException(
                code="AUTH_UNAVAILABLE",
                message="인증 서비스를 사용할 수 없습니다.",
                status_code=503,
            ) from exc

        # 계정 없음, 비밀번호 불일치, 비활성 계정은
        # 외부에 같은 오류로 응답합니다.
        if account is None or not matches or not account.is_active:
            raise AppException(
                code="INVALID_CREDENTIALS",
                message="로그인 정보를 확인해 주세요.",
                status_code=401,
            )

        if account.requires_second_factor:
            if self._second_factor is None:
                # 2차 인증을 생략하여 로그인시키지 않습니다.
                raise AppException(
                    code="AUTH_UNAVAILABLE",
                    message="인증 서비스를 사용할 수 없습니다.",
                    status_code=503,
                )

            try:
                return await self._second_factor.begin(
                    subject_id=account.subject_id,
                )

            except SecondFactorError as exc:
                raise AppException(
                    code="AUTH_UNAVAILABLE",
                    message="인증 서비스를 사용할 수 없습니다.",
                    status_code=503,
                ) from exc

        # 비밀번호 검증으로 필요한 인증이 모두 완료된 경우입니다.
        # 실제 세션과 쿠키 발급은 이후 API에서 연결합니다.
        return Authenticated(
            principal=Principal(
                subject_id=account.subject_id,
            ),
        )