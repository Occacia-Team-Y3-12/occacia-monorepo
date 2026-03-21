#!/usr/bin/env bash
set -euo pipefail

# Inject the virtual environment directly into the system path.
# This tells Linux exactly where to find alembic and uvicorn without needing Poetry.
export PATH="/app/.venv/bin:$PATH"

echo "Auto-healing missing database tables (if any)..."
python auto_heal.py

echo "Running Database Migrations..."
alembic upgrade heads

echo "Starting FastAPI Engine..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
