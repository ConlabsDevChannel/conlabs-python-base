import pytest

from app.core.auth.passwords import (
    Argon2PasswordHasher,
    PasswordHashError,
)

@pytest.fixture
def password_hasher():
    return Argon2PasswordHasher()

@pytest.mark.parametrize(
    "candidate, expected",
    [
        ("correct-password", True),
        ("wrong-password", False),
    ],
)
async def test_verify_password(
    password_hasher,
    candidate,
    expected,
):
    password_hash = await password_hasher.hash(
        password="correct-password",
    )

    result = await password_hasher.verify(
        password=candidate,
        password_hash=password_hash,
    )

    assert result is expected


async def test_hash_uses_argon2id_and_random_salt(
    password_hasher,
):
    first = await password_hasher.hash(
        password="same-password",
    )
    second = await password_hasher.hash(
        password="same-password",
    )

    assert first.startswith("$argon2id$")
    assert second.startswith("$argon2id$")

    # 같은 비밀번호라도 매번 다른 salt를 사용합니다.
    assert first != second


async def test_invalid_hash_raises_error(password_hasher):
    with pytest.raises(PasswordHashError):
        await password_hasher.verify(
            password="some-password",
            password_hash="invalid-hash",
        )