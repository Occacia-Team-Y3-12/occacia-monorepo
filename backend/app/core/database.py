import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv, find_dotenv 

# 1. SETUP LOGGING
logger = logging.getLogger(__name__)

# 2. SMART FINDER
env_file = find_dotenv()
if env_file:
    logger.info(f"✅ Found .env file at: {env_file}")
    load_dotenv(env_file)
else:
    logger.critical("❌ CRITICAL: Could not find any .env file!")

# 3. Get URL
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# 4. FALLBACK
if not SQLALCHEMY_DATABASE_URL:
    logger.warning("⚠️ .env failed. Using Hardcoded Docker Credentials.")
    SQLALCHEMY_DATABASE_URL = "postgresql://postgres:password@127.0.0.1:5432/occacia_db"

# 5. Connect
try:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    logger.info("🔌 Database engine initialized.")
except Exception as e:
    logger.critical(f"🔥 Fatal Database Error: {e}")
    raise e

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()