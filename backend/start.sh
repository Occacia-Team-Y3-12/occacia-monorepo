#!/bin/bash
# 'set -e' tells the script to explode (stop) if any command fails. 
# This prevents the app from starting if the database migration fails!
set -e 

echo "🏗️  STAGING: Running Database Migrations..."
# This command looks at your migrations/versions folder and updates OCI Postgres
alembic upgrade head

echo "🚀 IGNITION: Starting FastAPI Engine..."
# Bind to 0.0.0.0 so Nginx can reach the container
uvicorn main:app --host 0.0.0.0 --port 8000