from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App Config
    PROJECT_NAME: str = "Occacia"
    
    # ✅ AI (Langflow)
    LANGFLOW_URL: str
    LANGFLOW_ORG_ID: str
    LANGFLOW_TOKEN: str

    # ✅ Database (The URL used by SQLAlchemy)
    DATABASE_URL: str

    # 🛠️ ADDED: Infrastructure Variables (Fixes the validation error)
    # These match the variables inside your .env file
    DB_USER: str = "admin"
    DB_PASSWORD: str
    DB_NAME: str = "occacia_db"
    DOCKER_SOCKET: str

    # ⚙️ CONFIGURATION
    model_config = SettingsConfigDict(
        env_file=".env",
        # 🛡️ SAFETY NET: This prevents the crash! 
        # It tells Pydantic to ignore any other random variables in your .env
        extra="ignore" 
    )

settings = Settings()