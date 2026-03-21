import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load environment before initializing database
from dotenv import load_dotenv
load_dotenv()

from app.core.database import Base, engine
from app.models import registry  # noqa: F401
from sqlalchemy import inspect

print("Checking database for missing ORM tables...")

# Retry loop — guards against TCP timeout on first container boot
# (Docker healthcheck can pass before postgres accepts remote connections)
inspector = None
for attempt in range(10):
    try:
        inspector = inspect(engine)
        break
    except Exception as e:
        print(f"DB not ready, retrying ({attempt + 1}/10): {e}")
        time.sleep(3)

if inspector is None:
    print("Could not connect to database after 10 attempts. Aborting.")
    sys.exit(1)

existing_tables = set(inspector.get_table_names())
expected_tables = set(Base.metadata.tables.keys())
missing_tables = sorted(expected_tables - existing_tables)

if missing_tables:
    print(
        "Missing tables detected: "
        + ", ".join(missing_tables)
        + ". Rebuilding missing schema objects using SQLAlchemy models..."
    )
    try:
        Base.metadata.create_all(engine)
        print("Auto-heal complete! Missing tables restored.")
        sys.exit(2)
    except Exception as e:
        print(f"Error during create_all: {e}")
        sys.exit(1)
else:
    print("Database schema appears intact. Skipping auto-heal.")
    sys.exit(0)