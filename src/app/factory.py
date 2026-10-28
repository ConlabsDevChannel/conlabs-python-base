import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError

from app.core.config import get_settings
from app.core.logging.config import setup_logging
from app.core.exception.exceptions import AppException
from app.core.exception.handlers import (
    app_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler
)
from app.core.database.engine import create_db_engine
from app.core.database.session import create_session_factory
from app.core.database.migration import auto_upgrade_database

from app.core.middleware.cors import setup_core
from app.core.middleware.trace import setup_tracing

from app.core.http.client import create_http_client

from app.health import router as health_router
# 공용 라우터 등록
from app.router import router as api_router

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    # 마이그레이션은 DB엔진 생성 전
    await auto_upgrade_database(
        enabled=settings.db_migration_auto_upgrade,
    )

    engine = create_db_engine(
        database_url=settings.database_url,
        echo=settings.database_echo,
    )

    app.state.db_session_factory = create_session_factory(engine)

    # DB lifespan에 연결
    async with create_http_client(
        timeout=settings.http_timeout,
        max_connections=settings.http_max_connections,
        max_keepalive_connections=settings.http_max_keepalive_connections,
    ) as http_client:
        app.state.http_client = http_client

        try:
            yield
        finally:
            await engine.dispose()

def create_app() -> FastAPI:
    # core/config.py에서 설정한 세팅 가지고 오기
    settings = get_settings()

    # 향후 예외 핸들러, 로깅, 모듈 등록은 여기서 진행
    # 로깅 적용
    setup_logging(
        level=settings.log_level,
        log_path=settings.log_path,
        file_name=settings.log_file_name,
        max_bytes=settings.log_max_bytes,
        backup_count=settings.log_backup_count,
    )

    # FastAPI 앱 생성
    app = FastAPI(
        # env에 설정된 항목을 여기에서 집어넣음
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )

    # 예외처리 핸들러 추가
    app.add_exception_handler(
        AppException,
        app_exception_handler,
    )

    app.add_exception_handler(
        HTTPException,
        http_exception_handler,
    )

    app.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,
    )

    app.add_exception_handler(
        Exception,
        unhandled_exception_handler,
    )

    # Trace ID 및 요청 로깅
    setup_tracing(app)

    # CORS 등록
    setup_core(
        app=app,
        origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
    )

    # 헬스체크용 라우터 등록
    app.include_router(health_router)

    # 공용 라우터
    app.include_router(api_router, prefix="/api")

    return app