import logging.config # 로깅 표준 라이브러리의 설정
from pathlib import Path

LOG_FORMAT = (
    "[%(asctime)s]"
    "[%(levelname)-5s] "
    "[trace=%(trace_id)s] "
    "%(process)d "
    "[%(threadName)s]"
    "[%(name)s:%(lineno)d] "
    "%(message)s"
)

def setup_logging(
    level: str,
    log_path: str,
    file_name: str,
    max_bytes: int,
    backup_count: int,
) -> None:

    # 경로 OS별 처리
    log_dir = Path(log_path).resolve()
    # 로그 파일을 저장할 폴더를 생성
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{file_name}.log"

    # 로그 설정
    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,

        "formatters": {
            "default": {
                "format": LOG_FORMAT,
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
        },
                #Trace ID용 필터
        "filters": {
            "trace_id": {
                "()": "app.core.logging.filters.TraceIdFilter"
            }
        },

        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": "default",
                "stream": "ext://sys.stdout",
                "filters": ["trace_id"],
            },
            "file": {
                "class": (
                    "concurrent_log_handler."
                    "ConcurrentTimedRotatingFileHandler"
                ),
                "level": "DEBUG",
                "formatter": "default",
                "filename": str(log_file),
                "when": "midnight",
                "interval": 1,
                "maxBytes": max_bytes,
                "backupCount": backup_count,
                "encoding": "utf-8",
                "use_gzip": False,
                "filters": ["trace_id"],
            },
        },

        # 루트 레벨 지정
        "root": {
            "level": level.upper(),
            "handlers": ["console", "file"],
        },

        # 특정 클래스의 로깅 레벨 정의
        "loggers": {
            "uvicorn": {
                "level": "WARNING",
                "handlers": [],
                "propagate": True,
            },
            "uvicorn.error": {
                "level": "INFO",
                "handlers": [],
                "propagate": True,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": [],
                "propagate": True,
            },
            "sqlalchemy.engine": {
                "level": "WARNING",
            },
            "sqlalchemy.pool": {
                "level": "WARNING",
            },
        }
    })