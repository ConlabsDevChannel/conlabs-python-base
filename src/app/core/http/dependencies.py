from fastapi import Request

import httpx2

def get_http_client(request: Request) -> httpx2.AsyncClient:
    return request.app.state.http_client