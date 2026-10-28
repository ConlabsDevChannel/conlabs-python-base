from fastapi import APIRouter

# 모듈의 라우터 등록
# 예시
from app.modules.sample import router as sample_router
from app.modules.todo.router import router as todo_router

router = APIRouter()

router.include_router(sample_router, prefix="/sample")
router.include_router(todo_router, prefix="/sample")
