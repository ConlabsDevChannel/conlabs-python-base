from fastapi import APIRouter
from fastapi.exceptions import HTTPException, RequestValidationError
from pydantic import BaseModel

from app.core.exception.exceptions import AppException

router = APIRouter(prefix="/test")

class TestRequest(BaseModel):
    name: str
    age: int

@router.get("/error")
async def test_error():
    raise AppException(
        code="TE",
        message="테스트 오류",
        status_code=400,
    )

@router.get("/http-error")
async def test_http_error():
    raise HTTPException(
        status_code=403,
        detail="접근권한 없음"
    )

@router.post("/valid-error")
async def valid_error(data: TestRequest):
    return {"name": data.name, "age": data.age}

@router.get("/server-error")
async def test_server_error():
    raise RuntimeError("Internal Server Error")