# ruff: noqa: E402

import os
import sys
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

# ── Environment must be set before any app imports ───────────────────
os.environ.update({
    "SKIP_DB_STARTUP": "1",
    "LANGFLOW_URL": "http://localhost:7860/api/v1/run/test-flow",
    "LANGFLOW_ORG_ID": "test-org",
    "LANGFLOW_TOKEN": "test-token",
    "DB_PASSWORD": "password",
    "DOCKER_SOCKET": "/var/run/docker.sock",
    "SECRET_KEY": "test-secret-key-for-testing-only",
    "ALGORITHM": "HS256",
    "DATABASE_URL": "sqlite:///./test.db",
    "REDIS_URL": "redis://localhost:6379",
    "GOOGLE_CLIENT_ID": "test-google-client-id",
    "GOOGLE_CLIENT_SECRET": "test-google-client-secret",
    "GOOGLE_REDIRECT_URI": "https://app.occacia.com/oauth/callback",
    "CALENDAR_TOKEN_ENCRYPTION_KEY": "test-calendar-token-key",
})

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from app.core.database import Base, SessionLocal, engine
from app.core.security import create_access_token, get_password_hash
from app.main import app  # noqa: E402
from app.models import registry  # noqa: F401
from app.models.chat_model import ChatMessage
from app.models.customer import Customer
from app.models.event import Event
from app.models.event_chat_message import EventChatMessage
from app.models.event_persona import EventPersona
from app.models.notification import Notification
from app.models.offering import Offering
from app.models.package import Package
from app.models.package_execution_request import PackageExecutionRequest
from app.models.package_item import PackageItem
from app.models.persona import Persona
from app.models.recommendation_package import RecommendationPackage
from app.models.task import Task
from app.models.task_recommendation import TaskRecommendation
from app.models.task_request import TaskRequest
from app.models.vendor import Vendor
from app.services.google_calendar_service import google_calendar_service


# ── Create all tables once ───────────────────────────────────────────
@pytest.fixture(scope="session", autouse=True)
def create_tables():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# ── Clean all tables between tests ───────────────────────────────────
@pytest.fixture(autouse=True)
def clean_tables():
    yield
    db = SessionLocal()
    try:
        for model in (
            ChatMessage,
            EventChatMessage,
            Notification,
            PackageExecutionRequest,
            TaskRequest,
            PackageItem,
            RecommendationPackage,
            TaskRecommendation,
            Task,
            EventPersona,
            Event,
            Persona,
            Offering,
            Package,
            Vendor,
            Customer,
        ):
            try:
                db.query(model).delete()
            except OperationalError:
                db.rollback()
        db.commit()
    finally:
        db.close()


# ── Base test client ─────────────────────────────────────────────────
@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


# ── Helper: create and activate a customer ───────────────────────────
@pytest.fixture()
def active_customer():
    db = SessionLocal()
    email = f"customer-{uuid4().hex[:8]}@test.com"
    customer = Customer(
        full_name="Test Customer",
        email=email,
        password_hash=get_password_hash("Test1234!"),
        phone="+94771234567",
        email_verified=True,
        status="ACTIVE",
        customer_id=f"CUS-{uuid4().hex[:16]}",
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    db.close()
    return customer


# ── Helper: auth token for a customer ────────────────────────────────
@pytest.fixture()
def auth_token(active_customer):
    return create_access_token(data={"sub": active_customer.email})


# ── Helper: authenticated client ─────────────────────────────────────
@pytest.fixture()
def auth_client(client, auth_token):
    client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return client


@pytest.fixture(autouse=True)
def mock_google_calendar(monkeypatch):
    monkeypatch.setattr(
        google_calendar_service,
        "build_google_auth_url",
        lambda *, state, redirect_uri: (
            "https://accounts.google.com/o/oauth2/v2/auth"
            f"?state={state}&redirect_uri={redirect_uri}"
        ),
    )
    monkeypatch.setattr(
        google_calendar_service,
        "exchange_google_code",
        lambda *, code, redirect_uri: {
            "access_token": "google-access-token",
            "refresh_token": "google-refresh-token",
            "expires_in": 3600,
            "scope": "openid email https://www.googleapis.com/auth/calendar.events",
            "token_type": "Bearer",
        },
    )
    monkeypatch.setattr(
        google_calendar_service,
        "get_google_account_profile",
        lambda *, access_token: {
            "email": "calendar-user@example.com",
            "calendar_id": "primary",
        },
    )
    monkeypatch.setattr(
        google_calendar_service,
        "create_google_event",
        lambda *, access_token, calendar_id, payload: {
            "id": "google-event-123",
            "htmlLink": "https://calendar.google.com/event?eid=google-event-123",
        },
    )
    monkeypatch.setattr(
        google_calendar_service,
        "update_google_event",
        lambda *, access_token, calendar_id, event_id, payload: {
            "id": event_id,
            "htmlLink": f"https://calendar.google.com/event?eid={event_id}",
        },
    )
    monkeypatch.setattr(
        google_calendar_service,
        "delete_google_event",
        lambda *, access_token, calendar_id, event_id: None,
    )
    monkeypatch.setattr(
        google_calendar_service,
        "refresh_google_access_token",
        lambda *, refresh_token: {
            "access_token": "google-access-token-refreshed",
            "expires_in": 3600,
            "scope": "openid email https://www.googleapis.com/auth/calendar.events",
            "token_type": "Bearer",
        },
    )


# ── Helper: create a verified vendor with packages ───────────────────
@pytest.fixture()
def vendor_with_packages():
    db = SessionLocal()
    vendor = Vendor(
        business_name="Test Venue",
        display_name="Test Venue Display",
        email=f"vendor-{uuid4().hex[:8]}@test.com",
        is_verified=True,
        location_base="Colombo",
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)

    packages = [
        Package(
            vendor_id=vendor.id,
            name="Romantic Dinner",
            description="Candlelit dinner for two",
            price=300.0,
            price_per_head=150.0,
            min_guests=2,
            max_guests=10,
            tags=["romantic", "luxury", "private-dining"],
            location_coverage="Colombo",
        ),
        Package(
            vendor_id=vendor.id,
            name="Birthday Party",
            description="Fun birthday celebration",
            price=500.0,
            price_per_head=50.0,
            min_guests=10,
            max_guests=50,
            tags=["party", "kids", "family"],
            location_coverage="Kandy",
        ),
        Package(
            vendor_id=vendor.id,
            name="Nature Retreat",
            description="Outdoor adventure experience",
            price=200.0,
            price_per_head=50.0,
            min_guests=5,
            max_guests=20,
            tags=["nature", "adventure", "camping"],
            location_coverage="Ella",
        ),
    ]
    for p in packages:
        db.add(p)
    db.commit()
    db.close()
    return vendor
