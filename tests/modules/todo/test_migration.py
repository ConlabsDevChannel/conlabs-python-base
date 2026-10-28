from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import MetaData, create_engine, inspect

from app.core.config import get_settings
from app.core.database.base import Base
from app.modules.todo.models import Todo


def test_todo_migration_round_trip(tmp_path, monkeypatch):
    # 기존 .env의 DB에 접속하지 않고 임시 SQLite 파일만 사용합니다.
    db = tmp_path / "migration.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db.as_posix()}")
    get_settings.cache_clear()
    root = Path(__file__).resolve().parents[3]
    config = Config(str(root / "alembic.ini"))
    # 기존 트랜잭션 테스트가 Base에 등록한 테스트 전용 테이블은 비교에서 제외합니다.
    metadata = MetaData()
    Todo.__table__.to_metadata(metadata)
    monkeypatch.setattr(Base, "metadata", metadata)
    engine = create_engine(f"sqlite:///{db.as_posix()}")
    try:
        command.upgrade(config, "head")
        assert "sample_todos" in inspect(engine).get_table_names()
        command.check(config)
        command.downgrade(config, "2d1b09739f06")
        assert "sample_todos" not in inspect(engine).get_table_names()
        command.upgrade(config, "head")
        assert "sample_todos" in inspect(engine).get_table_names()
    finally:
        engine.dispose()
        get_settings.cache_clear()
