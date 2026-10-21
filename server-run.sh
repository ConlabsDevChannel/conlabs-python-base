#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f .env ]]; then
    echo "[ERROR] .env file not found."
    exit 1
fi

DB_URL=$(sed -n 's/^DATABASE_URL=//p' .env | tail -n 1)

case "$DB_URL" in
    sqlite+aiosqlite:*)
        DB_EXTRA="sqlite"
        ;;
    mysql+asyncmy:*)
        DB_EXTRA="mysql"
        ;;
    postgresql+asyncpg:*)
        DB_EXTRA="postgres"
        ;;
    *)
        echo "[ERROR] Unsupported DATABASE_URL driver."
        exit 1
        ;;
esac

echo "[INFO] Selected DB extra: $DB_EXTRA"

exec uv run --extra "$DB_EXTRA" uvicorn app.main:app --reload