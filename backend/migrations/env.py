import os
import sys
from logging.config import fileConfig
from pathlib import Path
from dotenv import load_dotenv

from alembic import context
from sqlalchemy import engine_from_config, pool

# Load environment variables from .env file before initializing config
load_dotenv()

# Set project root to ensure internal app modules are discoverable
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

config = getattr(context, "config", None)
if config is not None and config.config_file_name is not None:
    fileConfig(config.config_file_name)

def get_url() -> str:
    """
    Retrieves the database connection string. 
    Prioritizes DATABASE_URL environment variable, falls back to 
    component-based construction for local development.
    """
    url = os.getenv("DATABASE_URL")
    if url:
        # Log connection host for visibility during deployment
        safe_url = url.split("@")[-1] if "@" in url else url
        print(f"DATABASE_LOG: Using connection string at {safe_url}")
        return url

    # Fallback: construct URL from individual environment components
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME")
    
    if user and password and db_name:
        url = f"postgresql://{user}:{password}@localhost:5432/{db_name}"
        print(f"DATABASE_LOG: URL constructed from environment components")
        return url

    # Last resort: use the hardcoded URL in alembic.ini
    if config is None:
        raise RuntimeError("Neither DATABASE_URL nor alembic.ini config is available.")
    return config.get_main_option("sqlalchemy.url")

def _prepare_app_imports() -> None:
    """
    Sets up required environment variables for the FastAPI app 
    configuration to prevent initialization errors during migration.
    """
    db_url = get_url()
    os.environ.setdefault("DATABASE_URL", db_url)
    
    # Defaults for non-critical services during the migration process
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
    """
    Imports the SQLAlchemy Base and models to provide Alembic 
    with the target schema for autogeneration.
    """
    _prepare_app_imports()
    
    # Importing models here ensures they are registered with the Base metadata
    from app.models import Customer 
    from app.core.database import Base

    return Base.metadata

def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    Configures the context with a URL and emits SQL for the database.
    """
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
    """
    Run migrations in 'online' mode.
    Creates an engine and established a direct connection to the database.
    """
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

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()