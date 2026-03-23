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

# Only stamp heads if the database was completely empty (no migrations ever run)
# Otherwise, always run upgrade heads to ensure columns/schema match models.
if [ $HEAL_STATUS -eq 2 ]; then
    echo "Database missing tables were restored. Ensuring all migrations are applied..."
    alembic upgrade heads
else
    echo "Running Database Migrations..."
    alembic upgrade heads
fi

if [ "${RUN_DB_SEED_ON_STARTUP:-1}" = "1" ]; then
    echo "Running startup seed script..."
    python -m app.scripts.seed
else
    echo "RUN_DB_SEED_ON_STARTUP is disabled. Skipping seed script."
fi

echo "Starting FastAPI Engine..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
