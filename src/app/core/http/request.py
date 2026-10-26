import logging

import httpx2

from app.core.exception.exceptions import HttpClientException

logger = logging.getLogger(__name__)

async def send_request(
    client: httpx2.AsyncClient,
    method: str,
    url: str,
    **kwargs,
) -> httpx2.Response:
    try:
        response = await client.request(
            method=method,
            url=url,
            **kwargs,
        )

        logger.debug(
            "HTTP %s %s -> %s",
            method,
            url,
            response.status_code
        )

        return response

    except httpx2.TimeoutException as exc:
        logger.warning(
            "HTTP timeout: %s %s",
            method,
            url
        )
        raise HttpClientException(
            message="외부 응답 시간이 초과되었습니다.",
            url=url
        ) from exc

    except httpx2.RequestError as exc:
        logger.warning(
            "HTTP request failed: %s %s",
            method,
            url,
            exc_info=True
        )
        raise HttpClientException(
            message="외부 통신 중 오류가 발생했습니다.",
            url=url,
        ) from exc