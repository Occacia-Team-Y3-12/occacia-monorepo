#!/usr/bin/env bash
set -euo pipefail

echo "Running database migrations..."
# Ensure the production schema is up to date before the API starts.
poetry run alembic upgrade head

echo "Starting FastAPI..."
# Bind to 0.0.0.0 so the container can serve traffic through the ingress layer.
exec poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000