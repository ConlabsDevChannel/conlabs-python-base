import json

import httpx2
import pytest

from app.core.http.request import send_request
from app.core.exception.exceptions import HttpClientException


@pytest.fixture
def make_client():
    def factory(handler):
        return httpx2.AsyncClient(
            transport=httpx2.MockTransport(handler)
        )

    return factory


async def test_http_get_success(make_client):
    def handler(request):
        assert request.method == "GET"
        assert request.url.params["page"] == "1"

        return httpx2.Response(
            200,
            json={"result": "success"},
        )

    async with make_client(handler) as client:
        response = await send_request(
            client,
            "GET",
            "https://example.com/users",
            params={"page": 1},
        )

    assert response.status_code == 200
    assert response.json() == {"result": "success"}


async def test_http_post_headers(make_client):
    def handler(request):
        assert request.headers["Authorization"] == "Bearer test-token"
        assert json.loads(request.content) == {"name": "홍길동"}

        return httpx2.Response(201, json={"id": 1})

    async with make_client(handler) as client:
        response = await send_request(
            client,
            "POST",
            "https://example.com/users",
            headers={"Authorization": "Bearer test-token"},
            json={"name": "홍길동"},
        )

    assert response.status_code == 201
    assert response.json()["id"] == 1


async def test_http_timeout(make_client):
    def handler(request):
        raise httpx2.ReadTimeout(
            "Read timeout",
            request=request,
        )

    async with make_client(handler) as client:
        with pytest.raises(HttpClientException):
            await send_request(
                client,
                "GET",
                "https://example.com/timeout",
            )


async def test_http_connection_error(make_client):
    def handler(request):
        raise httpx2.ConnectError(
            "Connection failed",
            request=request,
        )

    async with make_client(handler) as client:
        with pytest.raises(HttpClientException):
            await send_request(
                client,
                "GET",
                "https://example.com/error",
            )


async def test_http_server_error(make_client):
    def handler(request):
        return httpx2.Response(
            500,
            json={"error": "Internal Server Error"},
        )

    async with make_client(handler) as client:
        response = await send_request(
            client,
            "GET",
            "https://example.com/error",
        )

    assert response.status_code == 500

    with pytest.raises(httpx2.HTTPStatusError):
        response.raise_for_status()