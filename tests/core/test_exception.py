import pytest

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.exception.exceptions import AppException

# 테스트용 변수(Validation)
class SampleRequest(BaseModel):
    name: str
    age: int

router = APIRouter(prefix="/test")

# 사용자 지정 AppException 응답 검사를 위한 경로
@router.get("/error")
async def raise_app_error():
    raise AppException(
        code="TE",
        message="테스트 오류",
        status_code=400,
    )

# HTTPException 검사를 위한 경로
@router.get("/http-error")
async def raise_http_error():
    raise HTTPException(
        status_code=403,
        detail="접근권한 없음",
    )

# ValidationException 검사를 위한 경로
@router.post("/valid-error")
async def raise_valid_error(data: SampleRequest):
    return {"name": data.name, "age": data.age}

# 이 외의 예외 처리 검사를 위한 경로
@router.get("/server-error")
async def raise_server_error():
    raise RuntimeError("Internal Server Error")

# 라우터 등록
@pytest.fixture
def client_with_routes(client, app):
    app.include_router(router)
    return client

# 요청 테스트
def test_app_exception(client_with_routes):
    response = client_with_routes.get("/test/error")

    assert response.status_code == 400
    assert response.json() == {
        "successCode": "F",
        "resCode": "TE",
        "resMessage": "테스트 오류",
    }


def test_http_exception(client_with_routes):
    response = client_with_routes.get("/test/http-error")

    assert response.status_code == 403
    assert response.json() == {
        "successCode": "F",
        "resCode": "HTTP_403",
        "resMessage": "접근권한 없음",
    }


def test_validation_exception(client_with_routes):
    response = client_with_routes.post(
        "/test/valid-error",
        json={
            "name": "홍길동",
            "age": "abc",
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert body["successCode"] == "F"
    assert body["resCode"] == "VE"
    assert body["resMessage"] == "요청 데이터가 올바르지 않습니다."
    assert body["data"][0]["field"] == "body.age"


def test_unhandled_exception(client_with_routes):
    response = client_with_routes.get("/test/server-error")

    assert response.status_code == 500
    assert response.json() == {
        "successCode": "F",
        "resCode": "ISE",
        "resMessage": "서버 내부 오류가 발생했습니다.",
    }