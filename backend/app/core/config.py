from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOCAL_ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    PROJECT_NAME: str = "Occacia"

    # Optional: only required when calling AI endpoints.
    LANGFLOW_URL: str | None = None
    LANGFLOW_ORG_ID: str | None = None
    LANGFLOW_TOKEN: str | None = None

    DATABASE_URL: str | None = None

    DB_USER: str = "admin"
    DB_PASSWORD: str | None = None
    DB_NAME: str = "occacia_db"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DOCKER_SOCKET: str = "N/A"

    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    model_config = SettingsConfigDict(
        # Local development reads backend/.env when it exists.
        # Production should inject environment variables directly.
        env_file=str(LOCAL_ENV_FILE) if LOCAL_ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
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

    @model_validator(mode="after")
    def assemble_database_url(self) -> "Settings":
        if self.DATABASE_URL:
            return self

        if not self.DB_PASSWORD:
            raise ValueError("DATABASE_URL is required when DB_PASSWORD is not set.")

        self.DATABASE_URL = (
            f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )
        return self

    REDIS_URL: str | None = "redis://redis:6379"

    SENDGRID_API_KEY: str | None = None
    FROM_EMAIL: str = "noreply@occacia.com"

    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    GOOGLE_REDIRECT_URI: str | None = None
    GOOGLE_CALENDAR_SCOPES: str = (
        "openid email https://www.googleapis.com/auth/calendar.events "
        "https://www.googleapis.com/auth/calendar.readonly"
    )
    CALENDAR_TOKEN_ENCRYPTION_KEY: str | None = None

    SKIP_EMAIL_VERIFICATION: bool = False
    SKIP_DB_STARTUP: bool = False

settings = Settings()
