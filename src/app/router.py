from fastapi import APIRouter

# 모듈의 라우터 등록
# 예시
from app.modules.sample import router as sample_router

router = APIRouter()

router.include_router(sample_router, prefix="/sample")