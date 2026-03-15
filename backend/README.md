# Occacia Backend (FastAPI)

Python backend for Occacia (FastAPI).

## Requirements

- Python 3.11+
- Poetry
- Postgres (Docker recommended)

## Quickstart (local)

1) Create `backend/.env`

Copy [`backend/.env.example`](./.env.example) to `backend/.env` and set at least:

- `SECRET_KEY`
- `DB_PASSWORD`

Optional:

- `DATABASE_URL` to override the assembled local connection string
- `LANGFLOW_URL`
- `LANGFLOW_TOKEN`
- `LANGFLOW_ORG_ID`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI`
- `CALENDAR_TOKEN_ENCRYPTION_KEY`

Generate a dev secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

2) Start local Postgres from `backend/`

```bash
cd backend
docker compose -f docker-compose-local.yml up -d
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
poetry sync --no-root
```

4) Run migrations

```bash
poetry run alembic upgrade head
```

Or run the one-off migration container:

```bash
docker compose -f docker-compose-local.yml --profile tools run --rm migrate
```

5) Run the API

```bash
make run
```

## Useful commands

- Tests: `make test` (Windows: `poetry run pytest`)
- Lint: `make lint` (Windows: `poetry run ruff check .`)
- Audit: `make audit` (Windows: `poetry run python -m pip install -U pip setuptools wheel; poetry run pip-audit -l`)
- Remove venv: `make clean-venv` (Windows: `Remove-Item -Recurse -Force .venv`)

## Troubleshooting

- Poetry using wrong Python: `cd backend && poetry env use python3.11`
- `.venv` not created in `backend/`: ensure `backend/poetry.toml` has `virtualenvs.in-project = true`, then reinstall: `make clean-venv && make install` (Windows: `Remove-Item -Recurse -Force .venv; poetry sync --no-root`)
- PowerShell can’t activate venv: run once `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` (or skip activation and use `poetry run ...`)
- `.env` not being read: confirm `backend/.env` exists and includes `SECRET_KEY` plus either `DATABASE_URL` or `DB_PASSWORD`
- DB connection errors: confirm Postgres is running from `backend/docker-compose-local.yml` and that `DB_HOST=localhost`, `DB_PORT=5432`
- Port already in use: stop the conflicting process or change the Uvicorn port (`--port 8001`)
- Lock/deps out of sync: `poetry lock` then `poetry sync --no-root`

## Monorepo Boundary

- `backend/.env` is the local backend development env file.
- `backend/docker-compose-local.yml` is the local backend Docker entrypoint.
- The monorepo root `.env` and root `docker-compose.yml` are for root-level orchestration and deployment, not backend-local startup.

## URLs

- Swagger UI: `http://localhost:8000/api/docs`
