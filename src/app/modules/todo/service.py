from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.transaction import transactional
from app.core.exception.exceptions import AppException
from app.core.pagination.helpers import create_page
from app.core.pagination.schemas import PageResponse

from .models import Todo
from .repository import TodoRepository
from .schemas import TodoCreate, TodoListQuery, TodoRead, TodoUpdate


class TodoService:
    def __init__(self, repository: TodoRepository | None = None):
        self.repository = repository if repository is not None else TodoRepository()

    async def _require(self, session: AsyncSession, todo_id: int) -> Todo:
        todo = await self.repository.get(session, todo_id)
        if todo is None:
            raise AppException("TODO_NOT_FOUND", "Todo를 찾을 수 없습니다.", 404)
        return todo

    @transactional
    async def create(self, data: TodoCreate, *, session: AsyncSession) -> TodoRead:
        todo = await self.repository.add(session, **data.model_dump())
        return TodoRead.model_validate(todo)

    @transactional
    async def get(self, todo_id: int, *, session: AsyncSession) -> TodoRead:
        return TodoRead.model_validate(await self._require(session, todo_id))

    @transactional
    async def list(self, query: TodoListQuery, *, session: AsyncSession) -> PageResponse[TodoRead]:
        items, total = await self.repository.list(session, query)
        return create_page([TodoRead.model_validate(item) for item in items], total, query)

    @transactional
    async def update(self, todo_id: int, data: TodoUpdate, *, session: AsyncSession) -> TodoRead:
        todo = await self._require(session, todo_id)
        todo = await self.repository.update(session, todo, data.model_dump(exclude_unset=True))
        return TodoRead.model_validate(todo)

    @transactional
    async def delete(self, todo_id: int, *, session: AsyncSession) -> None:
        await self.repository.delete(session, await self._require(session, todo_id))
