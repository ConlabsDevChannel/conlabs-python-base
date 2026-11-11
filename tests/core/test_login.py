from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from app.core.auth.accounts import (
    AccountProvider,
    PasswordAccount,
)
from app.core.auth.login import PasswordLoginService
from app.core.auth.passwords import (
    PasswordHashError,
    PasswordVerifier,
)
from app.core.auth.results import (
    Authenticated,
    SecondFactorRequired,
)
from app.core.auth.second_factor import (
    SecondFactorError,
    SecondFactorStarter,
)
from app.core.exception.exceptions import AppException


@pytest.fixture
def account():
    return PasswordAccount(
        subject_id="user-1",
        password_hash="stored-hash",
        is_active=True,
        requires_second_factor=False,
    )


@pytest.fixture
def accounts(account):
    provider = AsyncMock(spec=AccountProvider)
    provider.find_by_login_id.return_value = account

    return provider


@pytest.fixture
def verifier():
    verifier = AsyncMock(spec=PasswordVerifier)
    verifier.verify.return_value = True

    return verifier


@pytest.fixture
def second_factor():
    starter = AsyncMock(spec=SecondFactorStarter)
    starter.begin.return_value = SecondFactorRequired(
        challenge_token="test-challenge",
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
    )

    return starter


@pytest.fixture
def login_service(accounts, verifier, second_factor):
    return PasswordLoginService(
        accounts=accounts,
        password_verifier=verifier,
        # 검증기를 대역으로 사용하므로 테스트에서는 식별용 문자열입니다.
        # 실제 앱에서는 유효한 Argon2id 해시를 전달해야 합니다.
        dummy_password_hash="dummy-hash",
        second_factor=second_factor,
    )


async def test_login_success(
    login_service,
    accounts,
    verifier,
    second_factor,
):
    result = await login_service.login(
        login_id="alice",
        password="correct-password",
    )

    assert isinstance(result, Authenticated)
    assert result.principal.subject_id == "user-1"

    accounts.find_by_login_id.assert_awaited_once_with(
        login_id="alice",
    )
    verifier.verify.assert_awaited_once_with(
        password="correct-password",
        password_hash="stored-hash",
    )
    second_factor.begin.assert_not_awaited()


@pytest.mark.parametrize(
    "reason",
    ["missing", "wrong-password", "inactive"],
)
async def test_login_rejects_invalid_credentials(
    login_service,
    account,
    accounts,
    verifier,
    second_factor,
    reason,
):
    if reason == "missing":
        accounts.find_by_login_id.return_value = None
    elif reason == "wrong-password":
        verifier.verify.return_value = False
    else:
        accounts.find_by_login_id.return_value = account.model_copy(
            update={"is_active": False},
        )

    with pytest.raises(AppException) as caught:
        await login_service.login(
            login_id="alice",
            password="some-password",
        )

    assert caught.value.status_code == 401
    assert caught.value.code == "INVALID_CREDENTIALS"
    assert caught.value.message == "로그인 정보를 확인해 주세요."

    expected_hash = (
        "dummy-hash"
        if reason == "missing"
        else "stored-hash"
    )

    verifier.verify.assert_awaited_once_with(
        password="some-password",
        password_hash=expected_hash,
    )
    second_factor.begin.assert_not_awaited()

async def test_login_requires_second_factor(
    login_service,
    account,
    accounts,
    second_factor,
):
    accounts.find_by_login_id.return_value = account.model_copy(
        update={"requires_second_factor": True},
    )

    result = await login_service.login(
        login_id="alice",
        password="correct-password",
    )

    assert isinstance(result, SecondFactorRequired)
    assert result == second_factor.begin.return_value

    # 요청의 로그인 ID가 아닌 서버의 사용자 식별자를 전달합니다.
    second_factor.begin.assert_awaited_once_with(
        subject_id="user-1",
    )


async def test_login_blocks_when_second_factor_unavailable(
    account,
    accounts,
    verifier,
):
    accounts.find_by_login_id.return_value = account.model_copy(
        update={"requires_second_factor": True},
    )

    service = PasswordLoginService(
        accounts=accounts,
        password_verifier=verifier,
        dummy_password_hash="dummy-hash",
        # 2차 인증 구현을 연결하지 않은 상태입니다.
    )

    with pytest.raises(AppException) as caught:
        await service.login(
            login_id="alice",
            password="correct-password",
        )

    assert caught.value.status_code == 503
    assert caught.value.code == "AUTH_UNAVAILABLE"


async def test_password_error_returns_unavailable(
    login_service,
    verifier,
    second_factor,
):
    verifier.verify.side_effect = PasswordHashError(
        "테스트용 해시 오류",
    )

    with pytest.raises(AppException) as caught:
        await login_service.login(
            login_id="alice",
            password="some-password",
        )

    assert caught.value.status_code == 503
    assert caught.value.code == "AUTH_UNAVAILABLE"

    second_factor.begin.assert_not_awaited()


async def test_second_factor_error_returns_unavailable(
    login_service,
    account,
    accounts,
    second_factor,
):
    accounts.find_by_login_id.return_value = account.model_copy(
        update={"requires_second_factor": True},
    )
    second_factor.begin.side_effect = SecondFactorError(
        "테스트용 인증 진행 정보 저장 오류",
    )

    with pytest.raises(AppException) as caught:
        await login_service.login(
            login_id="alice",
            password="correct-password",
        )

    assert caught.value.status_code == 503
    assert caught.value.code == "AUTH_UNAVAILABLE"    