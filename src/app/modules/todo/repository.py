from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Todo
from .schemas import TodoListQuery


class TodoRepository:
    """쿼리와 flush만 담당하며 commit/rollback은 서비스에 맡깁니다."""

    async def add(self, session: AsyncSession, *, title: str, description: str | None) -> Todo:
        todo = Todo(title=title, description=description)
        session.add(todo)
        await session.flush()
        await session.refresh(todo)
        return todo

    async def get(self, session: AsyncSession, todo_id: int) -> Todo | None:
        return await session.get(Todo, todo_id)

    async def list(self, session: AsyncSession, query: TodoListQuery) -> tuple[list[Todo], int]:
        filters = []
        if query.q is not None:
            filters.append(or_(
                Todo.title.icontains(query.q, autoescape=True),
                Todo.description.icontains(query.q, autoescape=True),
            ))
        if query.completed is not None:
            filters.append(Todo.completed == query.completed)

        total = await session.scalar(select(func.count()).select_from(Todo).where(*filters))
        # 검증된 필드만 매핑하고, 동률일 때 ID로 순서를 확정합니다.
        columns = {name: getattr(Todo, name) for name in (
            "id", "title", "created_at", "updated_at"
        )}
        column = columns[query.sort]
        order = [column.asc() if query.direction == "asc" else column.desc()]
        if query.sort != "id":
            order.append(Todo.id.asc() if query.direction == "asc" else Todo.id.desc())
        statement = (
            select(Todo).where(*filters).order_by(*order)
            .offset(query.offset).limit(query.size)
        )
        return list((await session.scalars(statement)).all()), int(total or 0)

    async def update(self, session: AsyncSession, todo: Todo, changes: dict) -> Todo:
        for field, value in changes.items():
            setattr(todo, field, value)
        await session.flush()
        await session.refresh(todo)
        return todo

    async def delete(self, session: AsyncSession, todo: Todo) -> None:
        await session.delete(todo)
        await session.flush()
