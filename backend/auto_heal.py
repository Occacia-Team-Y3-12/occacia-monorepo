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

print("Loading all database models...")
# Dynamically import all models so SQLAlchemy registers them on Base.metadata
for _, module_name, _ in pkgutil.iter_modules(app.models.__path__):
    importlib.import_module(f"app.models.{module_name}")

print("Running auto-heal: executing CREATE TABLE IF NOT EXISTS for all models...")
Base.metadata.create_all(engine)
print("Auto-heal complete! All missing tables restored.")
