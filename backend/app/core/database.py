import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)

# Pull the database URL directly from our centralized Pydantic settings
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

try:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    logger.info("Database engine initialized successfully.")
except Exception as e:
    logger.critical(f"Fatal Database Error: {e}")
    raise e

# FastAPI dependency to manage database session lifecycles per request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()