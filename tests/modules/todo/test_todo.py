import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.database.session import create_session_factory, get_db_session
from app.modules.todo.models import Todo
from app.modules.todo.repository import TodoRepository
from app.modules.todo.router import router
from app.modules.todo.schemas import TodoCreate
from app.modules.todo.service import TodoService


@pytest.fixture
async def todo_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Todo.__table__.create)
    yield create_session_factory(engine)
    await engine.dispose()


@pytest.fixture
async def todo_client(app, todo_factory):
    async def session_override():
        async with todo_factory() as session:
            yield session

    app.include_router(router, prefix="/api/sample")
    app.dependency_overrides[get_db_session] = session_override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


URL = "/api/sample/todos"


async def test_crud(todo_client):
    response = await todo_client.post(URL, json={"title": "  첫 Todo  ", "description": "설명"})
    assert response.status_code == 201
    body = response.json()
    assert body["successCode"] == "S"
    todo = body["data"]
    assert todo["title"] == "첫 Todo"
    assert todo["completed"] is False
    assert todo["created_at"] and todo["updated_at"]
    item_url = f"{URL}/{todo['id']}"
    assert (await todo_client.get(item_url)).json()["data"] == todo
    response = await todo_client.patch(item_url, json={"completed": True, "description": None})
    assert response.status_code == 200
    updated = response.json()["data"]
    assert updated["completed"] is True
    assert updated["description"] is None
    assert updated["title"] == "첫 Todo"
    assert (await todo_client.delete(item_url)).status_code == 200
    for method in ("get", "patch", "delete"):
        kwargs = {"json": {"title": "missing"}} if method == "patch" else {}
        response = await getattr(todo_client, method)(item_url, **kwargs)
        assert response.status_code == 404
        assert response.json()["resCode"] == "TODO_NOT_FOUND"


async def test_search_sort_and_pagination(todo_client):
    ids = []
    for title, description in (("same", "needle"), ("same", "needle"), ("other", "no")):
        result = await todo_client.post(URL, json={"title": title, "description": description})
        ids.append(result.json()["data"]["id"])
    await todo_client.patch(f"{URL}/{ids[2]}", json={"completed": True})
    params = {"q": "NEEDLE", "completed": False, "sort": "title", "direction": "asc", "size": 1}
    page = (await todo_client.get(URL, params=params)).json()["data"]
    assert page["items"][0]["id"] == ids[0]
    assert page["total_elements"] == 2
    assert page["total_pages"] == 2
    assert page["has_next"] is True
    second = (await todo_client.get(URL, params={**params, "page": 2})).json()["data"]
    assert second["items"][0]["id"] == ids[1]
    assert second["has_previous"] is True
    assert second["has_next"] is False
    descending = (await todo_client.get(URL, params={"sort": "id"})).json()["data"]
    assert [item["id"] for item in descending["items"]] == list(reversed(ids))
    empty = (await todo_client.get(URL, params={"q": "absent"})).json()["data"]
    assert empty["items"] == [] and empty["total_pages"] == 0
    beyond = (await todo_client.get(URL, params={"page": 50})).json()["data"]
    assert beyond["items"] == [] and beyond["total_elements"] == 3


@pytest.mark.parametrize("keyword", ["%", "_", "/"])
async def test_search_treats_wildcards_as_text(todo_client, keyword):
    await todo_client.post(URL, json={"title": f"literal{keyword}value"})
    await todo_client.post(URL, json={"title": "unrelated"})
    page = (await todo_client.get(URL, params={"q": keyword})).json()["data"]
    assert page["total_elements"] == 1


@pytest.mark.parametrize("payload", [{}, {"title": " "}, {"title": "x" * 201}, {"title": "ok", "extra": 1}])
async def test_invalid_create(todo_client, payload):
    assert (await todo_client.post(URL, json=payload)).status_code == 422


@pytest.mark.parametrize("payload", [{}, {"title": None}, {"completed": None}, {"title": " "}])
async def test_invalid_patch(todo_client, payload):
    assert (await todo_client.patch(f"{URL}/1", json=payload)).status_code == 422


@pytest.mark.parametrize("params", [
    {"page": 0}, {"size": 101}, {"sort": "description"},
    {"sort": "id; DROP TABLE sample_todos"}, {"direction": "sideways"}, {"q": " "},
])
async def test_invalid_query(todo_client, params):
    assert (await todo_client.get(URL, params=params)).status_code == 422


async def test_service_rollback_after_flush(todo_factory):
    class FailingRepository(TodoRepository):
        async def add(self, session, **kwargs):
            await super().add(session, **kwargs)
            raise RuntimeError("failure after INSERT")

    async with todo_factory() as session:
        with pytest.raises(RuntimeError, match="after INSERT"):
            await TodoService(FailingRepository()).create(TodoCreate(title="rollback"), session=session)
    async with todo_factory() as session:
        assert await session.scalar(select(func.count()).select_from(Todo)) == 0
