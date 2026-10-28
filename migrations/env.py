import asyncio

# alembic, db 설정
from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import get_settings
from app.core.database.base import Base
from app.modules.todo import models as todo_models  # noqa: F401 — Alembic metadata 등록

config = context.config

settings = get_settings()

config.set_main_option(
    "sqlalchemy.url",
    settings.database_url.replace("%", "%%"), # DB에서 사용하는 %를 %%로 변경 처리(DB 인식)
)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")

    # 마이그레이션 db 컨텍스트 생성
    context.config(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True
    )

    # 트랜잭션 시작시 함께 마이그레이션 시작
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=False, # sqlite일 때만 True, 나머지는 False
        render_as_batch=connection.dialect.name == "mysql", # sqlite, mysql, postgresql 로 지정
    )

    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    try:
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
    finally:
        await connectable.dispose()

# 마이그레이션 상태(온라인, 오프라인 여부 분기)
def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
