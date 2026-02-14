# Occacia Backend (FastAPI)

Python backend for Occacia (FastAPI).

## Requirements

- Python 3.11+
- Poetry
- Postgres (Docker recommended)

## Quickstart (local)

1) Start Postgres (from monorepo root):

```bash
docker compose -f docker-compose-local.yml up -d
```

2) Set env vars

This repo keeps a single env file at the monorepo root: `../.env`.

- macOS/Linux: `cd backend && ln -s ../.env .env`
- Windows (PowerShell): `cd backend; Copy-Item ..\.env .\.env`

Minimum required:

- `SECRET_KEY`
- `DATABASE_URL`

Generate a dev secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

3) Create `.venv` + install dependencies

Poetry is configured to create the virtualenv in-project at `backend/.venv` (`poetry.toml`).

```bash
cd backend
poetry env use python3.11
make install
```

No `make`?

```bash
cd backend
poetry install --sync --no-root
```

4) Run the API

```bash
cd backend
make run
```

No `make`?

```bash
cd backend
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5) Run migrations (when needed)

```bash
cd backend
poetry run alembic upgrade head
```

## Useful commands

- Tests: `make test` (Windows: `poetry run pytest`)
- Lint: `make lint` (Windows: `poetry run ruff check .`)
- Audit: `make audit` (Windows: `poetry run python -m pip install -U pip setuptools wheel; poetry run pip-audit -l`)
- Remove venv: `make clean-venv` (Windows: `Remove-Item -Recurse -Force .venv`)

## Troubleshooting

- Poetry using wrong Python: `cd backend && poetry env use python3.11`
- `.venv` not created in `backend/`: ensure `backend/poetry.toml` has `virtualenvs.in-project = true`, then reinstall: `make clean-venv && make install` (Windows: `Remove-Item -Recurse -Force .venv; poetry install --sync --no-root`)
- PowerShell can’t activate venv: run once `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` (or skip activation and use `poetry run ...`)
- `.env` not being read: confirm `backend/.env` exists (symlink or copy from `../.env`)
- DB connection errors: confirm Postgres is running and `DATABASE_URL` matches the exposed host/port (`localhost:5432` by default)
- Port already in use: stop the conflicting process or change the Uvicorn port (`--port 8001`)
- Lock/deps out of sync: `poetry lock` then `poetry install --sync --no-root`

## URLs

- Swagger UI: `http://localhost:8000/api/docs`
