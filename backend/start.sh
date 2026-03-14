#!/usr/bin/env bash
set -euo pipefail

# nject the virtual environment directly into the system path.
# This tells Linux exactly where to find alembic and uvicorn without needing Poetry.
export PATH="/app/.venv/bin:$PATH"

echo "Running Database Migrations..."
alembic upgrade head

echo "Starting FastAPI Engine..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000