import logging

from app.core.logging.context import get_trace_id

class TraceIdFilter(logging.Filter):
    # 로그 발생 시의 TraceID를 LogRecord에 추가, 이 때 "-"는 서버 시작, 종료, 배치 로그 등을 ㅟㅇ한 기본값.
    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = get_trace_id() or ("-")
        return True