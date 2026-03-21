# Occacia Backend

> FastAPI backend service for the Occacia platform.

[Getting Started: macOS/Linux](#getting-started-macoslinux) | [Getting Started: Windows](#getting-started-windows) | [Configuration](#configuration) | [Troubleshooting](#troubleshooting)

## Overview

This service handles the backend APIs for Occacia. Local development in this directory uses:

- `backend/.env` for local-only backend environment variables
- `backend/.env.example` as the local env template
- `backend/docker-compose-local.yml` for local Postgres
- `backend/.venv` for the local Python virtual environment

This README is only for working inside `backend/`. It does not use the monorepo root `.env` or the root `docker-compose.yml`.

## Choose Your Setup Path

Start in the `backend/` directory.

- macOS/Linux: [Install Python 3.11](#install-python) -> [Getting Started: macOS/Linux](#getting-started-macoslinux)
- Windows: [Install Python 3.11](#windows) -> [Getting Started: Windows](#getting-started-windows)

If you are on Windows and PowerShell blocks `.\.venv\Scripts\Activate.ps1`, do not stop there. The Windows setup section includes both:

- an execution policy fix
- a no-activation fallback using Poetry's full executable path

## Tech Stack

- Python `3.11`
- FastAPI
- Poetry
- PostgreSQL

## Prerequisites

Before starting, make sure you have:

- Python `3.11`
- Docker Desktop, or Docker Engine with Docker Compose
- `pip`

## Install Python

### macOS

```bash
brew install python@3.11
python3.11 --version
```

If Homebrew is not installed, install it first from `https://brew.sh`.

### Windows

Install Python first, then restart PowerShell before continuing to the Windows setup steps.

```powershell
winget install Python.Python.3.11
py -3.11 --version
```

If `winget` is unavailable, install Python 3.11 from `https://www.python.org/downloads/windows/` and enable `Add python.exe to PATH`.

## Getting Started: macOS/Linux

1. Create and activate the virtual environment.

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install poetry
```

2. Install dependencies.

```bash
poetry sync --no-root
```

3. Create the local env file.

```bash
cp .env.example .env
```

4. Update `backend/.env` with at least:

- `SECRET_KEY`
- `DB_PASSWORD`

Generate a secret if needed:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

5. Start Postgres.

```bash
docker compose -f docker-compose-local.yml up -d
```

6. Run migrations.

```bash
poetry run alembic upgrade head
```

7. Start the API.

```bash
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Getting Started: Windows

Open Windows PowerShell after Python 3.11 is installed, then continue here.

1. Install Poetry.

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

Use Poetry directly from its installed location in the current PowerShell session:

```powershell
$Poetry = "$env:APPDATA\Python\Scripts\poetry.exe"
& $Poetry --version
```

Optional: add Poetry to your user `PATH` for future terminals:

```powershell
[Environment]::SetEnvironmentVariable("Path", [Environment]::GetEnvironmentVariable("Path", "User") + ";$env:APPDATA\Python\Scripts", "User")
```

Then restart PowerShell. In the steps below, you can keep using `& $Poetry ...` even if you do not update `PATH`.

2. Create the virtual environment.

```powershell
cd backend
py -3.11 -m venv .venv
```

3. Activate it.

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation because script execution is disabled, choose one of these:

Current terminal only:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Current user:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

No activation:

```powershell
.\.venv\Scripts\python -m pip install --upgrade pip
& $Poetry sync --no-root
```

4. If activation worked, install dependencies.

```powershell
python -m pip install --upgrade pip
& $Poetry sync --no-root
```

5. Create the local env file.

```powershell
Copy-Item .env.example .env
```

6. Update `backend/.env` with at least:

- `SECRET_KEY`
- `DB_PASSWORD`

Generate a secret if needed:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

7. Start Postgres.

```powershell
docker compose -f docker-compose-local.yml up -d
```

8. Run migrations.

Activated venv:

```powershell
& $Poetry run alembic upgrade head
```

No activation:

```powershell
& $Poetry run alembic upgrade head
```

9. Start the API.

Activated venv:

```powershell
& $Poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

No activation:

```powershell
& $Poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Configuration

Required variables in local-only `backend/.env`:

- `SECRET_KEY`
- `DB_PASSWORD`

Defaults already provided in local-only `backend/.env.example`:

- `DB_USER`
- `DB_NAME`
- `DB_HOST`
- `DB_PORT`

Optional variables:

- `DATABASE_URL`
- `LANGFLOW_URL`
- `LANGFLOW_TOKEN`
- `LANGFLOW_ORG_ID`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI`
- `GOOGLE_CALENDAR_SCOPES`
- `CALENDAR_TOKEN_ENCRYPTION_KEY`
- `REDIS_URL`
- `SKIP_EMAIL_VERIFICATION`

`DATABASE_URL` overrides the assembled local database connection string.

## Running the Service

Local API URL:

- `http://localhost:8000`

Useful endpoints:

- Health: `http://localhost:8000/api/v1/health`
- Swagger UI: `http://localhost:8000/api/docs`

## Common Commands

- Install dependencies:
  `poetry sync --no-root`
- Run migrations:
  `poetry run alembic upgrade head`
- Start API:
  `poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- Run tests:
  `poetry run pytest`
- Run lint:
  `poetry run ruff check .`
- Run audit:
  `poetry run python -m pip install -U pip setuptools wheel && poetry run pip-audit -l`
- Start Postgres:
  `docker compose -f docker-compose-local.yml up -d`
- Stop Postgres:
  `docker compose -f docker-compose-local.yml down`
- Reset Postgres volume:
  `docker compose -f docker-compose-local.yml down -v`

## Makefile Shortcuts

If `make` is available, `backend/Makefile` provides:

- `make install`
- `make run`
- `make test`
- `make lint`
- `make audit`
- `make clean-venv`

Windows setup should not depend on `make`.

## Alternative Migration Path

You can run migrations using the helper container instead of your local venv:

```bash
docker compose -f docker-compose-local.yml --profile tools run --rm migrate
```

## Troubleshooting

- Poetry uses the wrong Python:
  - macOS/Linux: `poetry env use python3.11`
  - Windows: `& "$env:APPDATA\Python\Scripts\poetry.exe" env use 3.11`
- `backend/.env` is not being read:
  Ensure it exists and contains `SECRET_KEY` plus either `DB_PASSWORD` or `DATABASE_URL`.
- Database auth errors after changing credentials:
  Reset the local database volume with `docker compose -f docker-compose-local.yml down -v`.
- Port `8000` is already in use:
  Start Uvicorn on another port, for example `--port 8001`.
- `.venv` is broken:
  Delete `.venv`, recreate it, reinstall Poetry, and run `poetry sync --no-root` again.
