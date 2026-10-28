import logging
import time
from uuid import UUID, uuid4

from fastapi import FastAPI, Request

from app.core.logging.context import (
    set_trace_id,
    reset_trace_id,
)

logger = logging.getLogger(__name__)

TRACE_HEADER = "X-Trace-ID"

# traceID가 UUID4 기준에 맞는지 확인
def resolve_trace_id(value: str | None) -> str:
    if value:
        try:
            return str(UUID(value))
        except ValueError:
            pass

    return str(uuid4())

def setup_tracing(app: FastAPI) -> None:

    @app.middleware("http")
    async def tracing_middleware(request: Request, call_next):
        # Header에서 X-Trace-ID 추출
        trace_id = resolve_trace_id(
            request.headers.get(TRACE_HEADER)
        )

        token = set_trace_id(trace_id)
        request.state.trace_id = trace_id

        start_time = time.perf_counter()
        status_code = 500

        try:
            response = await call_next(request)

            status_code = response.status_code
            response.headers[TRACE_HEADER] = trace_id

            return response

        except Exception:
            logger.exception(
                "Unhandled request error: %s %s",
                request.method,
                request.url.path,
            )
            raise

        finally:
            elapsed_ms = (
                time.perf_counter() - start_time
            ) * 1000

            logger.info(
                "HTTP %s %s %s %.2fms",
                request.method,
                request.url.path,
                status_code,
                elapsed_ms,
            )

            reset_trace_id(token)