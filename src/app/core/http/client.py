import httpx2

def create_http_client(
    timeout: float = 30.0,
    max_connections: int = 100,
    max_keepalive_connections: int = 20
) -> httpx2.AsyncClient:
    return httpx2.AsyncClient(
        timeout=httpx2.Timeout(timeout),
        limits=httpx2.Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
        ),
        follow_redirects=False,
    )