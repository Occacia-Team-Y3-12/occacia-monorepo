import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


# IMPORTANT:
# `app/core/config.py` instantiates `Settings()` at import time, so we must
# populate *all* required environment variables before importing `app.main`.
_REQUIRED_TEST_ENV: dict[str, str] = {
    "SKIP_DB_STARTUP": "1",
    "LANGFLOW_URL": "http://localhost:7860/api/v1/run",
    "LANGFLOW_ORG_ID": "test-org",
    "LANGFLOW_TOKEN": "test-token",
    "DB_PASSWORD": "password",
    "DOCKER_SOCKET": "/var/run/docker.sock",
    "SECRET_KEY": "test-secret-key",
    "ALGORITHM": "HS256",
    # Use SQLite for tests to avoid needing a running Postgres.
    "DATABASE_URL": "sqlite:///./test.db",
}

for key, value in _REQUIRED_TEST_ENV.items():
    os.environ[key] = value

# Ensure repo root is importable when running pytest from other directories.
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from app.main import app  # noqa: E402 (env must be set before import)


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client
