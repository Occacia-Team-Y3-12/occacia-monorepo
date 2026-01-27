from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv, find_dotenv # <--- Import find_dotenv

# 1. SMART FINDER: Hunts for .env in current and parent folders
env_file = find_dotenv()
if env_file:
    print(f"✅ Found .env file at: {env_file}")
    load_dotenv(env_file)
else:
    print("❌ CRITICAL: Could not find any .env file!")

# 2. Get URL
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# 3. FALLBACK: If .env is empty or fails, use the Docker default directly
if not SQLALCHEMY_DATABASE_URL:
    print("⚠️ .env failed. Using Hardcoded Docker Credentials.")
    SQLALCHEMY_DATABASE_URL = "postgresql://postgres:password@127.0.0.1:5432/occacia_db"

# 4. Connect
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()