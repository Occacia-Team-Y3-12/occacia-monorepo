import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Ensure Python can find models.py
sys.path.append(os.path.join(os.getcwd()))
from models import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def get_url():
    # THE FIX: Force it to check the Environment Variable first!
    url = os.getenv("DATABASE_URL")
    if url:
        # Censors the password but shows us the HOST so we can debug
        safe_url = url.split('@')[-1] if '@' in url else url
        print(f"✅ DEPLOYMENT LOG: Using DATABASE_URL at {safe_url}")
        return url
    
    print("❌ DEPLOYMENT LOG: DATABASE_URL not found, falling back to alembic.ini")
    return config.get_main_option("sqlalchemy.url")

def run_migrations_online() -> None:
    connectable = engine_from_config(
        {"sqlalchemy.url": get_url()}, # INJECT THE DYNAMIC URL HERE
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

# ... (Keep the rest of the file the same) ...
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()