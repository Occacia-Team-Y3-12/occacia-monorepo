import os
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# CRITICAL: SET ENV VARS BEFORE IMPORTING APP
# --------------------------------------------------------------------------
# This code runs immediately when pytest starts, BEFORE it imports your app.
os.environ["DATABASE_URL"] = "postgresql://admin:password@localhost:5432/occacia_db"

# Also add the backend folder to Python path just in case
sys.path.append(str(Path(__file__).parent.parent.parent))

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