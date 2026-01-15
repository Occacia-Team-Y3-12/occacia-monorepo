import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# 1. MOVEMENT: Ensure Python can find models.py in the backend root
sys.path.append(os.path.join(os.getcwd()))
from app.models import Base

# 2. CONFIG: This is the Alembic Config object.
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def get_url():
    """THE SHIELD: Priority is Environment Variable (OCI) then .ini (Local)"""
    url = os.getenv("DATABASE_URL")
    if url:
        # Censors password for logs but shows host for debugging
        safe_url = url.split('@')[-1] if '@' in url else url
        print(f"✅ DEPLOYMENT LOG: Using DATABASE_URL at {safe_url}")
        return url
    
    print("❌ DEPLOYMENT LOG: DATABASE_URL not found, using alembic.ini")
    return config.get_main_option("sqlalchemy.url")

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emits SQL strings)."""
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
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

# 3. TRIGGER: The Logic that Flake8 was crying about
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()