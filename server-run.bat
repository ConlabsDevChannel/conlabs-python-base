@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "DB_EXTRA="
set "SERVER_PORT=8000"

if not exist ".env" (
    echo [ERROR] .env file not found.
    exit /b 1
)

for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    if /i "%%A"=="DATABASE_URL" (
        set "DB_URL=%%B"
    )
    if /i "%%A"=="SERVER_PORT" (
        set "SERVER_PORT=%%B"
    )
)

if not defined DB_URL (
    echo [ERROR] DATABASE_URL is missing.
    exit /b 1
)

if /i "!DB_URL:~0,17!"=="sqlite+aiosqlite:" (
    set "DB_EXTRA=sqlite"
)

if /i "!DB_URL:~0,14!"=="mysql+asyncmy:" (
    set "DB_EXTRA=mysql"
)

if /i "!DB_URL:~0,19!"=="postgresql+asyncpg:" (
    set "DB_EXTRA=postgres"
)

if not defined DB_EXTRA (
    echo [ERROR] Unsupported DATABASE_URL driver.
    exit /b 1
)

echo [INFO] Selected DB extra: !DB_EXTRA!

uv run --extra !DB_EXTRA! uvicorn app.main:app --reload --port "!SERVER_PORT!"

endlocal