# ruff: noqa: S101, S106

from pathlib import Path

from app.core.config import LOCAL_ENV_FILE, Settings


def test_local_env_file_points_to_backend_env():
    assert LOCAL_ENV_FILE == Path(__file__).resolve().parents[2] / ".env"


def test_database_url_is_built_from_db_components(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    settings = Settings(
        _env_file=None,
        SECRET_KEY="test-secret",
        DB_USER="local-user",
        DB_PASSWORD="local-password",
        DB_NAME="local-db",
        DB_HOST="127.0.0.1",
        DB_PORT=5433,
    )

    assert settings.DATABASE_URL == (
        "postgresql+psycopg2://local-user:local-password@127.0.0.1:5433/local-db"
    )


def test_database_url_takes_precedence_over_db_components():
    settings = Settings(
        _env_file=None,
        SECRET_KEY="test-secret",
        DATABASE_URL="postgresql+psycopg2://override:pw@db:5432/override_db",
        DB_PASSWORD="ignored",
    )

    assert settings.DATABASE_URL == "postgresql+psycopg2://override:pw@db:5432/override_db"
