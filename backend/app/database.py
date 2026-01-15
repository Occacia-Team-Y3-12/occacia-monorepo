from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from pathlib import Path

# 1. SMART LOAD: Find the .env file relative to this file
# This prevents "File Not Found" errors if you run from a different folder
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)

# 2. GET THE CONFIGURATION
# It tries the .env file first (localhost). 
# If that fails/is missing, it defaults to the Docker internal name (db).
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://admin:password@db:5432/occacia_db"
)

# 3. START THE ENGINE
engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from sqlalchemy.orm import declarative_base
Base = declarative_base()

# 4. THE DEPENDENCY (The "Tunnel Opener")
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()