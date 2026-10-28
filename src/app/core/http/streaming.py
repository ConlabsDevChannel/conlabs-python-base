# LLM 호출을 위한 스트리밍 클라이언트
import logging
import httpx2

from collections.abc import AsyncIterator
from app.core.exception.exceptions import HttpClientException
from app.core.http.headers import build_request_headers

logger = logging.getLogger(__name__)

async def stream_request(
    client: httpx2.AsyncClient,
    method: str,
    url: str,
    *,
    propagate_trace: bool = False,
    **kwargs,
) -> AsyncIterator[bytes]:

    headers = build_request_headers (
        headers=kwargs.pop("headers", None),
        propagate_trace=propagate_trace
    )
    
    try:
        async with client.stream(
            method=method,
            url=url,
            headers=headers,
            **kwargs,
        ) as response:
            response.raise_for_status()

            logger.debug(
                "HTTP stream %s %s -> %s",
                method,
                url,
                response.status_code,
            )

            # 청크 단위 비동기 처리
            async for chunk in response.aiter_bytes():
                yield chunk

    except httpx2.TimeoutException as exc:
        logger.warning(
            "HTTP stream timeout: %s %s",
            method,
            url
        )

        raise HttpClientException(
            message="외부 스트리밍 응답 시간이 초과되었습니다.",
            url=url,
        ) from exc

    except httpx2.RequestError as exc:
            logger.warning(
                "HTTP streaming request failed: %s %s",
                method,
                url,
                exc_info=True
            )
            raise HttpClientException(
                message="외부 스트리밍 통신 중 오류가 발생했습니다.",
                url=url,
            ) from exc