from uuid import UUID

from fastapi.testclient import TestClient

from app.factory import create_app


def test_generate_trace_id():
    app = create_app()

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200

    trace_id = response.headers["X-Trace-ID"]

    assert UUID(trace_id).version == 4


def test_reuse_trace_id():
    app = create_app()

    trace_id = "123e4567-e89b-42d3-a456-426614174000"

    with TestClient(app) as client:
        response = client.get(
            "/health",
            headers={"X-Trace-ID": trace_id},
        )

    assert response.status_code == 200
    assert response.headers["X-Trace-ID"] == trace_id


def test_invalid_trace_id():
    app = create_app()

    with TestClient(app) as client:
        response = client.get(
            "/health",
            headers={"X-Trace-ID": "invalid-trace-id"},
        )

    assert response.status_code == 200

    trace_id = response.headers["X-Trace-ID"]

    assert trace_id != "invalid-trace-id"
    assert UUID(trace_id).version == 4