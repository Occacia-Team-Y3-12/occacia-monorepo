import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings  # 🎯 The Single Source of Truth

# 1. SETUP LOGGING
logger = logging.getLogger(__name__)

# 2. GET URL FROM SETTINGS
# settings.DATABASE_URL already contains the correct @db:5432 address from Docker
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# 3. CONNECT
try:
    # No more 'find_dotenv' checks here. If we are here, settings are loaded.
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    logger.info("🔌 Database engine initialized using Centralized Settings.")
except Exception as e:
    logger.critical(f"🔥 Fatal Database Error: {e}")
    raise e

# 4. DEPENDENCY
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()