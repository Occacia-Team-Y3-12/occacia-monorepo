from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve the .env file path dynamically (checks backend root, then monorepo root)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE_CANDIDATES = (
    BASE_DIR / ".env",
    BASE_DIR.parent / ".env",
)
ENV_FILE_PATH = next((p for p in ENV_FILE_CANDIDATES if p.exists()), None)


class Settings(BaseSettings):
    # --- App Configuration ---
    PROJECT_NAME: str = "Occacia"
    
    # --- AI (Langflow) ---
    LANGFLOW_URL: Optional[str] = None
    LANGFLOW_ORG_ID: Optional[str] = None
    LANGFLOW_TOKEN: Optional[str] = None

    # --- Database ---
    DATABASE_URL: str
    DB_USER: str = "admin"
    DB_PASSWORD: Optional[str] = None
    DB_NAME: str = "occacia_db"

    # --- Infrastructure ---
    DOCKER_SOCKET: str = "N/A"
    REDIS_URL: Optional[str] = "redis://redis:6379"

    # --- Security ---
    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    # --- Email ---
    SENDGRID_API_KEY: Optional[str] = None
    FROM_EMAIL: str = "noreply@occacia.com"

    # --- Feature Flags ---
    SKIP_EMAIL_VERIFICATION: bool = False
    SKIP_DB_STARTUP: bool = False

    # --- Pydantic Config ---
    model_config = SettingsConfigDict(
        # Pass None if file doesn't exist to prevent Pydantic warnings
        env_file=str(ENV_FILE_PATH) if ENV_FILE_PATH else None,
        env_file_encoding='utf-8',
        extra="ignore" 
    )

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