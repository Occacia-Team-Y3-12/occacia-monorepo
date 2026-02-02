import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv, find_dotenv 

# 1. SETUP LOGGING
# Crucial for monitoring database health and connection status.
logger = logging.getLogger(__name__)

# 2. SMART FINDER
# Automatically locates your .env file in a monorepo structure.
env_file = find_dotenv()
if env_file:
    logger.info(f"✅ Found .env file at: {env_file}")
    load_dotenv(env_file)
else:
    logger.critical("❌ CRITICAL: Could not find any .env file!")

# 3. Get URL
# In Docker, this should be: postgresql://postgres:password@db:5432/occacia_db
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# 4. FALLBACK
# Used for local development or if the .env is missing.
if not SQLALCHEMY_DATABASE_URL:
    logger.warning("⚠️ .env failed. Using Hardcoded Docker Credentials.")
    # Note: Use 'db' instead of '127.0.0.1' if running inside a Docker network.
    SQLALCHEMY_DATABASE_URL = "postgresql://postgres:password@db:5432/occacia_db"

# 5. Connect
try:
    # The 'engine' is the actual socket connection to Postgres.
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    # SessionLocal is the factory that creates unique sessions for each user request.
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Base is the parent class that all your models (User, Venue, Chat) must inherit from.
    Base = declarative_base()
    
    logger.info("🔌 Database engine initialized.")
except Exception as e:
    logger.critical(f"🔥 Fatal Database Error: {e}")
    raise e

# 6. Dependency
# This 'Janitor' function opens the door for a request and cleans up after it's done.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()