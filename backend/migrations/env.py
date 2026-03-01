import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Ensure imports work no matter where Alembic is invoked from.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

config = getattr(context, "config", None)
if config is not None and config.config_file_name is not None:
    fileConfig(config.config_file_name)


def get_url() -> str:
    """THE SHIELD: Priority is Environment Variable (OCI) then .ini (Local)"""
    url = os.getenv("DATABASE_URL")
    if url:
        # Censors password for logs but shows host for debugging
        safe_url = url.split("@")[-1] if "@" in url else url
        print(f"✅ DEPLOYMENT LOG: Using DATABASE_URL at {safe_url}")
        return url

    print("❌ DEPLOYMENT LOG: DATABASE_URL not found, using alembic.ini")
    if config is None:
        raise RuntimeError("Alembic config is unavailable and DATABASE_URL is not set.")
    return config.get_main_option("sqlalchemy.url")


def _prepare_app_imports() -> None:
    """
    app/core/config.py instantiates Settings() at import time and requires several
    environment variables. For migrations, only DATABASE_URL is truly required, but
    we provide safe defaults for other required settings if they are missing.
    """
    os.environ.setdefault("DATABASE_URL", get_url())
    defaults: dict[str, str] = {
        "LANGFLOW_URL": "http://localhost:7860/api/v1/run",
        "LANGFLOW_ORG_ID": "migration",
        "LANGFLOW_TOKEN": "migration",
        "DB_PASSWORD": "migration",
        "DOCKER_SOCKET": "/var/run/docker.sock",
        "SECRET_KEY": "migration-secret-key",
        "ALGORITHM": "HS256",
    }
    for key, value in defaults.items():
        os.environ.setdefault(key, value)


def _get_target_metadata():
    _prepare_app_imports()
    from app.core.database import Base  # noqa: E402
    from app.models import chat_model  # noqa: F401,E402
    from app.models import models  # noqa: F401,E402

    return Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emits SQL strings)."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=_get_target_metadata(),
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode (talks to the live DB)."""
    # Force SQLAlchemy to use our dynamic URL
    connectable = engine_from_config(
        {"sqlalchemy.url": get_url()},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=_get_target_metadata(),
        )

        with context.begin_transaction():
            context.run_migrations()

# 3. TRIGGER: The Logic that Flake8 was crying about
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()