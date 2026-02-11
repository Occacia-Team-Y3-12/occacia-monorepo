import os
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# CRITICAL: SET ENV VARS BEFORE IMPORTING APP
# --------------------------------------------------------------------------
# This code runs immediately when pytest starts, BEFORE it imports your app.
os.environ["DATABASE_URL"] = "postgresql://admin:password@localhost:5432/occacia_db"
os.environ["SKIP_DB_STARTUP"] = "1"
os.environ.setdefault("LANGFLOW_URL", "http://localhost:7860/api/v1/run")
os.environ.setdefault("LANGFLOW_ORG_ID", "test-org")
os.environ.setdefault("LANGFLOW_TOKEN", "test-token")
os.environ.setdefault("DB_PASSWORD", "password")
os.environ.setdefault("DOCKER_SOCKET", "/var/run/docker.sock")

# Also add the backend folder to Python path just in case
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Now we can import pytest
import pytest
from fastapi.testclient import TestClient
from app.main import app

# --------------------------------------------------------------------------
# THE TEST CLIENT FIXTURE
# --------------------------------------------------------------------------
@pytest.fixture(scope="module")
def client():
    # This gives every test a fresh robot browser
    with TestClient(app) as c:
        yield c