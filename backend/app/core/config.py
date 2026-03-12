from pathlib import Path
from typing import Optional
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# 🛠️ DYNAMIC PATH CALCULATION
# This finds the directory where config.py lives, then goes up to the project root.
# Structure: /app/app/core/config.py -> /app/ (the project root)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE_CANDIDATES = (
    BASE_DIR / ".env",         # backend/.env (local dev)
    BASE_DIR.parent / ".env",  # monorepo root .env (common)
)
ENV_FILE_PATH = next((p for p in ENV_FILE_CANDIDATES if p.exists()), None)

class Settings(BaseSettings):
    # ==========================================
    # 📝 APP CONFIGURATION
    # ==========================================
    PROJECT_NAME: str = "Occacia"
    
    # ✅ AI (Langflow)
    # Optional: only required when calling AI endpoints.
    LANGFLOW_URL: Optional[str] = None
    LANGFLOW_ORG_ID: Optional[str] = None
    LANGFLOW_TOKEN: Optional[str] = None

    # ✅ Database
    DATABASE_URL: Optional[str] = None

    # 🛡️ Infrastructure (Synced with .env / Docker Compose)
    DB_USER: str = "admin"
    DB_PASSWORD: Optional[str] = None
    DB_NAME: str = "occacia_db"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
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
        env_file=str(ENV_FILE_PATH) if ENV_FILE_PATH else None,
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

    @model_validator(mode="after")
    def assemble_database_url(self):
        if self.DATABASE_URL:
            return self

        if not self.DB_PASSWORD:
            raise ValueError(
                "DATABASE_URL is required when DB_PASSWORD is not set."
            )

        self.DATABASE_URL = (
            f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )
        return self

    # ✅ Redis
    REDIS_URL: Optional[str] = "redis://redis:6379"

    # ✅ Email (SendGrid)
    SENDGRID_API_KEY: Optional[str] = None
    FROM_EMAIL: str = "noreply@occacia.com"

    # ✅ Feature flags — replaces raw os.getenv() calls
    SKIP_EMAIL_VERIFICATION: bool = False
    SKIP_DB_STARTUP: bool = False

# Initialize settings
settings = Settings()
