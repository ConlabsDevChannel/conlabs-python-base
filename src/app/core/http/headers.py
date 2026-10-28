from app.core.logging.context import get_trace_id

TRACE_HEADER = "X-Trace-ID"

def build_request_headers(
    headers: dict[str, str] | None = None,
    propagate_trace: bool = False, # 외부 공개 API를 호출할 때는 Trace ID를 자동으로 전달하지 않음, 즉 내부 서비스에만 활성
) -> dict[str, str]:
    result = dict(headers or {})

    if propagate_trace:
        trace_id = get_trace_id()

        if trace_id:
            result[TRACE_HEADER] = trace_id

    return result