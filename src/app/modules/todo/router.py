from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.session import get_db_session
from app.core.pagination.schemas import PageResponse
from app.core.response.helpers import success_response
from app.core.response.schemas import BaseResponse

from .schemas import TodoCreate, TodoListQuery, TodoRead, TodoUpdate
from .service import TodoService

router = APIRouter(prefix="/todos", tags=["Todo sample"])
Session = Annotated[AsyncSession, Depends(get_db_session)]
TodoId = Annotated[int, Path(gt=0)]
service = TodoService()

# 공통 helper는 비특정 Generic 모델을 반환하므로, alias 사전으로 변환하여
# FastAPI가 구체적인 response_model로 검증하도록 합니다. core 수정은 없습니다.


@router.post("", response_model=BaseResponse[TodoRead], status_code=201)
async def create_todo(data: TodoCreate, session: Session):
    return success_response(data=await service.create(data, session=session)).model_dump(by_alias=True)


@router.get("", response_model=BaseResponse[PageResponse[TodoRead]])
async def list_todos(query: Annotated[TodoListQuery, Query()], session: Session):
    return success_response(data=await service.list(query, session=session)).model_dump(by_alias=True)


@router.get("/{todo_id}", response_model=BaseResponse[TodoRead])
async def get_todo(todo_id: TodoId, session: Session):
    return success_response(data=await service.get(todo_id, session=session)).model_dump(by_alias=True)


@router.patch("/{todo_id}", response_model=BaseResponse[TodoRead])
async def update_todo(todo_id: TodoId, data: TodoUpdate, session: Session):
    return success_response(data=await service.update(todo_id, data, session=session)).model_dump(by_alias=True)


@router.delete("/{todo_id}", response_model=BaseResponse[None])
async def delete_todo(todo_id: TodoId, session: Session):
    await service.delete(todo_id, session=session)
    return success_response(message="Todo가 삭제되었습니다.").model_dump(by_alias=True)
