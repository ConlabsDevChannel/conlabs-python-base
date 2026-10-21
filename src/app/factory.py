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

from app.modules.sample import router

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    engine = create_db_engine(
        database_url=settings.database_url,
        echo=settings.database_echo,
    )

    app.state.db_session_factory = create_session_factory(engine)

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

    app.include_router(router)

    return app