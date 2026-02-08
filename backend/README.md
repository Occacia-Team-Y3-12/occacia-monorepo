# Occacia Backend (FastAPI)

This is the **Python backend** for Occacia.  
It provides REST APIs for authentication, customers, vendors, and other MVP features.

> Monorepo note: This folder is the backend part of the Occacia monorepo.

---

## Tech Stack

- **Python**: 3.14+
- **Framework**: FastAPI
- **Server**: Uvicorn
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Migrations**: Alembic
- **Testing**: Pytest
- **Password Hashing**: bcrypt (via passlib)

---

## Folder Structure

```text
backend/
  app/
    main.py

    core/
      core_config.py
      core_db.py
      core_errors.py
      security/
        security_passwords.py
        security_tokens.py

    auth/
      auth_router.py
      auth_schemas.py
      auth_service.py
      auth_models.py
      auth_email_service.py

    health/
      health_router.py

  migrations/
  tests/
  alembic.ini
  pyproject.toml
  poetry.lock  # generated after `poetry lock`
  Dockerfile
  start.sh
  README.md
```

---

## Setup

### Linux/macOS

```bash
poetry install
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Windows (PowerShell)

```powershell
poetry install
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Dependency Updates

```bash
poetry update
poetry lock
```

## Tests

```bash
poetry run pytest
```

## Dependency Security Checks

Linux/macOS:
```bash
make audit
```

Windows:
```powershell
poetry run pip-audit -l
```
