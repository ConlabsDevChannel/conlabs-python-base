import httpx2
import pytest

from app.core.http.streaming import stream_request
from app.core.exception.exceptions import HttpClientException


async def test_stream_success():
    async def handler(request):
        assert request.method == "POST"
        assert request.headers["Authorization"] == "Bearer test-token"

        return httpx2.Response(
            200,
            headers={"Content-Type": "text/event-stream"},
            content=(
                b'data: {"content":"Hello"}\n\n'
                b'data: {"content":" World"}\n\n'
                b'data: [DONE]\n\n'
            ),
        )

    transport = httpx2.MockTransport(handler)

    async with httpx2.AsyncClient(transport=transport) as client:
        chunks = []

        async for chunk in stream_request(
            client=client,
            method="POST",
            url="https://example.com/v1/chat/completions",
            headers={"Authorization": "Bearer test-token"},
            json={"stream": True},
        ):
            chunks.append(chunk)

    result = b"".join(chunks).decode("utf-8")

    assert 'Hello' in result
    assert ' World' in result
    assert "data: [DONE]" in result


async def test_stream_timeout():
    def handler(request):
        raise httpx2.ReadTimeout(
            "Stream timeout",
            request=request,
        )

    async with httpx2.AsyncClient(
        transport=httpx2.MockTransport(handler)
    ) as client:
        with pytest.raises(HttpClientException):
            async for _ in stream_request(
                client,
                "GET",
                "https://example.com/stream",
            ):
                pass


async def test_stream_http_error():
    def handler(request):
        return httpx2.Response(
            503,
            json={"error": "Service Unavailable"},
        )

    async with httpx2.AsyncClient(
        transport=httpx2.MockTransport(handler)
    ) as client:
        with pytest.raises(httpx2.HTTPStatusError) as exc_info:
            async for _ in stream_request(
                client,
                "GET",
                "https://example.com/stream",
            ):
                pass

    assert exc_info.value.response.status_code == 503