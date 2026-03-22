#!/usr/bin/env bash
set -euo pipefail

# Inject the virtual environment directly into the system path.
# This tells Linux exactly where to find alembic and uvicorn without needing Poetry.
export PATH="/app/.venv/bin:$PATH"

echo "Auto-healing missing database tables (if any)..."
set +e
python auto_heal.py
HEAL_STATUS=$?
set -e

if [ $HEAL_STATUS -eq 2 ]; then
    echo "Database was fully reconstructed. Stamping Alembic to head to gracefully skip duplicated historical migrations..."
    alembic stamp heads
else
    echo "Running Database Migrations..."
    alembic upgrade heads
fi

echo "Starting FastAPI Engine..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
