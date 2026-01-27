from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"

class Settings(BaseSettings):
    DATABASE_URL: str
    
    # New simplified config
    LANGFLOW_URL: str
    LANGFLOW_TOKEN: str
    LANGFLOW_ORG_ID: str

    model_config = SettingsConfigDict(env_file=ENV_PATH, env_file_encoding='utf-8', extra="ignore")

settings = Settings()