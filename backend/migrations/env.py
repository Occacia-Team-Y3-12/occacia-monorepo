import os
import sys
from logging.config import fileConfig
from pathlib import Path
from dotenv import load_dotenv
from alembic import context
from sqlalchemy import engine_from_config, pool

# =============================================================================
# 1. INJECT  - Must happen before any 'app' imports
# =============================================================================
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# =============================================================================
# 2. SATISFY  - Feed dummy vars so FastAPI doesn't crash on import
# =============================================================================
load_dotenv()

dummy_env = {
    "LANGFLOW_URL": "http://localhost:7860/api/v1/run",
    "LANGFLOW_ORG_ID": "migration",
    "LANGFLOW_TOKEN": "migration",
    "DB_PASSWORD": "migration",
    "SECRET_KEY": "migration-secret-key",
    "ALGORITHM": "HS256",
}
for key, value in dummy_env.items():
    os.environ.setdefault(key, value)

# =============================================================================
# 3. MAP  - THIS CANNOT BE HIDDEN IN A FUNCTION
# =============================================================================
from app.core.database import Base

target_metadata = Base.metadata

# =============================================================================
# ALEMBIC ENGINE LOGIC
# =============================================================================
config = getattr(context, "config", None)
if config is not None and config.config_file_name is not None:
    fileConfig(config.config_file_name)

def get_url() -> str:
    url = os.getenv("DATABASE_URL")
    if url:
        safe_url = url.split("@")[-1] if "@" in url else url
        print(f"DATABASE_LOG: Using connection string at {safe_url}")
        return url

    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME")
    
    if user and password and db_name:
        return f"postgresql://{user}:{password}@localhost:5432/{db_name}"

    if config is None:
        raise RuntimeError("Neither DATABASE_URL nor alembic.ini config is available.")
    return config.get_main_option("sqlalchemy.url")

def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        {"sqlalchemy.url": get_url()},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
