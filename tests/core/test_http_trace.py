import pytest
import httpx2

from app.core.http.request import send_request
from app.core.logging.context import (
    set_trace_id,
    reset_trace_id,
)


@pytest.mark.asyncio
async def test_trace_id_propagation():
    trace_id = "123e4567-e89b-42d3-a456-426614174000"

    async def handler(request: httpx2.Request):
        assert request.headers["X-Trace-ID"] == trace_id
        return httpx2.Response(200, json={"ok": True})

    transport = httpx2.MockTransport(handler)

    token = set_trace_id(trace_id)

    try:
        async with httpx2.AsyncClient(transport=transport) as client:
            response = await send_request(
                client,
                "GET",
                "https://internal.example/test",
                propagate_trace=True,
            )

        assert response.status_code == 200

    finally:
        reset_trace_id(token)


@pytest.mark.asyncio
async def test_no_trace_propagation_by_default():
    trace_id = "123e4567-e89b-42d3-a456-426614174000"

    async def handler(request: httpx2.Request):
        assert "X-Trace-ID" not in request.headers
        return httpx2.Response(200)

    transport = httpx2.MockTransport(handler)
    token = set_trace_id(trace_id)

    try:
        async with httpx2.AsyncClient(transport=transport) as client:
            response = await send_request(
                client,
                "GET",
                "https://external.example/test",
            )

        assert response.status_code == 200

    finally:
        reset_trace_id(token)