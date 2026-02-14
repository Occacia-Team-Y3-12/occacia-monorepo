import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def _set_test_env() -> None:
    # Ensure imports don't require live infrastructure.
    os.environ["SKIP_DB_STARTUP"] = "1"

    # Pydantic Settings (app/core/config.py) requires these at import time.
    os.environ["LANGFLOW_URL"] = "http://localhost:7860/api/v1/run"
    os.environ["LANGFLOW_ORG_ID"] = "test-org"
    os.environ["LANGFLOW_TOKEN"] = "test-token"
    os.environ["DB_PASSWORD"] = "password"
    os.environ["DOCKER_SOCKET"] = "/var/run/docker.sock"
    os.environ["SECRET_KEY"] = "test-secret-key"
    os.environ["ALGORITHM"] = "HS256"

    # Use SQLite for tests to avoid needing a running Postgres.
    os.environ["DATABASE_URL"] = "sqlite:///./test.db"


_set_test_env()

# Ensure repo root is importable when running pytest from other directories.
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from app.main import app  # noqa: E402 (env must be set before import)


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client
