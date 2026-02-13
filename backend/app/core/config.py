import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# 🛠️ DYNAMIC PATH CALCULATION
# This finds the directory where config.py lives, then goes up to the project root.
# Structure: /app/app/core/config.py -> /app/ (the project root)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE_PATH = BASE_DIR / ".env"

class Settings(BaseSettings):
    # ==========================================
    # 📝 APP CONFIGURATION
    # ==========================================
    PROJECT_NAME: str = "Occacia"
    
    # ✅ AI (Langflow)
    LANGFLOW_URL: str
    LANGFLOW_ORG_ID: str
    LANGFLOW_TOKEN: str

    # ✅ Database
    DATABASE_URL: str

    # 🛡️ Infrastructure (Synced with .env / Docker Compose)
    DB_USER: str = "admin"
    DB_PASSWORD: str
    DB_NAME: str = "occacia_db"
    DOCKER_SOCKET: str = "N/A"

    # 🛡️ SECURITY SEEDS
    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    # ==========================================
    # ⚙️ CONFIGURATION & THE SILENCER
    # ==========================================
    model_config = SettingsConfigDict(
        # 🛠️ THE REAL FIX: Check the ABSOLUTE path.
        # If it doesn't exist, we pass None so Pydantic remains silent.
        env_file=str(ENV_FILE_PATH) if ENV_FILE_PATH.exists() else None,
        env_file_encoding='utf-8',
        extra="ignore" 
    )

    # 🛠️ LOGIC: Priority of Truth
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        return init_settings, env_settings, dotenv_settings

# Initialize settings
settings = Settings()