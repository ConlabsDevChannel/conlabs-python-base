from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def setup_core(
    app: FastAPI,
    origins: list[str],
    allow_credentials: bool = False,
) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )