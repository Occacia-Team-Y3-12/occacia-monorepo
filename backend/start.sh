#!/usr/bin/env bash
set -euo pipefail

echo "🏗️  STAGING: Running Database Migrations..."
# This command looks at your migrations/versions folder and updates OCI Postgres
poetry run alembic upgrade head

echo "🚀 IGNITION: Starting FastAPI Engine..."
# Bind to 0.0.0.0 so Nginx can reach the container
exec poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000