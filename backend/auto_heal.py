import os
import sys
from pathlib import Path
import importlib
import pkgutil

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load environment before initializing database
from dotenv import load_dotenv
load_dotenv()

from app.core.database import Base, engine
import app.models

import sys
from sqlalchemy import inspect

print("Checking database for missing core tables...")
inspector = inspect(engine)
existing_tables = inspector.get_table_names()

if 'users' not in existing_tables:
    print("Core tables missing! Rebuilding database schema from scratch using SQLAlchemy models...")
    try:
        Base.metadata.create_all(engine)
        print("Auto-heal complete! All missing tables restored.")
        sys.exit(2)
    except Exception as e:
        print(f"Error during create_all: {e}")
        sys.exit(1)
else:
    print("Database schema appears intact. Skipping auto-heal.")
    sys.exit(0)

