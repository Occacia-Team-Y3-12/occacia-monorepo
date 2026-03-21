"""
tests/Integration/test_manage_customers_uc29.py
Integration tests for UC-29: Manage Customers
"""

import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.core.security import get_password_hash, create_access_token
from app.models.customer import Customer
from app.models.admin import Admin


@pytest.fixture(scope="function")
def db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    Session = sessionmaker(bind=db_engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session):
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


def _uid():
    return str(uuid.uuid4())[:8]


def _make_admin(db, email=None):
    email = email or f"admin_{_uid()}@test.com"
    a = Admin(
        email=email,
        password_hash=get_password_hash("AdminPass1!"),
        staff_role="staff",
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


def _make_customer(db, email=None, status="ACTIVE"):
    email = email or f"cust_{_uid()}@test.com"
    c = Customer(
        email=email,
        full_name=f"Customer {_uid()}",
        password_hash=get_password_hash("Password1!"),
        phone="+94771234567",
        locale="en",
        email_verified=True,
        status=status,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def _admin_token(admin_id: str) -> str:
    import jwt
    from app.core.security import SECRET_KEY, ALGORITHM
    return jwt.encode(
        {"sub": admin_id, "type": "admin"},
        SECRET_KEY, algorithm=ALGORITHM,
    )


def _auth_headers_admin(admin_id: str) -> dict:
    return {"Authorization": f"Bearer {_admin_token(admin_id)}"}


class TestListCustomers:
    URL = "/api/v1/admin/customers"

    def test_list_customers_authenticated(self, client, db_session):
        admin = _make_admin(db_session)
        _make_customer(db_session, status="ACTIVE")
        _make_customer(db_session, status="PENDING")
        
        resp = client.get(self.URL, headers=_auth_headers_admin(str(admin.admin_id)))
        
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert len(body["items"]) == 2

    def test_list_customers_filter_by_status(self, client, db_session):
        admin = _make_admin(db_session)
        _make_customer(db_session, status="ACTIVE")
        _make_customer(db_session, status="SUSPENDED")
        _make_customer(db_session, status="ACTIVE")
        
        resp = client.get(
            self.URL,
            params={"status": "ACTIVE"},
            headers=_auth_headers_admin(str(admin.admin_id)),
        )
        
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["items"]) == 2
        for item in body["items"]:
            assert item["status"] == "ACTIVE"

    def test_list_customers_empty(self, client, db_session):
        admin = _make_admin(db_session)
        
        resp = client.get(self.URL, headers=_auth_headers_admin(str(admin.admin_id)))
        
        assert resp.status_code == 200
        body = resp.json()
        assert body["items"] == []

    def test_list_customers_unauthenticated_401(self, client):
        resp = client.get(self.URL)
        assert resp.status_code == 401

    def test_list_customers_non_admin_401(self, client, db_session):
        customer = _make_customer(db_session)
        token = create_access_token({"sub": customer.email})
        
        resp = client.get(self.URL, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401

    def test_list_customers_pagination(self, client, db_session):
        admin = _make_admin(db_session)
        for _ in range(5):
            _make_customer(db_session)
        
        resp = client.get(
            self.URL,
            params={"limit": 3},
            headers=_auth_headers_admin(str(admin.admin_id)),
        )
        
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["items"]) == 3
        assert body.get("nextCursor") is not None


class TestGetCustomerDetail:
    def test_get_customer_by_id(self, client, db_session):
        admin = _make_admin(db_session)
        customer = _make_customer(db_session, status="ACTIVE")
        
        resp = client.get(
            f"/api/v1/admin/customers/{customer.customer_id}",
            headers=_auth_headers_admin(str(admin.admin_id)),
        )
        
        assert resp.status_code == 200
        body = resp.json()
        assert body["customer_id"] == customer.customer_id
        assert body["email"] == customer.email
        assert body["full_name"] == customer.full_name
        assert body["status"] == "ACTIVE"

    def test_get_customer_not_found_404(self, client, db_session):
        admin = _make_admin(db_session)
        
        resp = client.get(
            "/api/v1/admin/customers/CUS-NOTFOUND",
            headers=_auth_headers_admin(str(admin.admin_id)),
        )
        
        assert resp.status_code == 404

    def test_get_customer_unauthenticated_401(self, client, db_session):
        customer = _make_customer(db_session)
        
        resp = client.get(f"/api/v1/admin/customers/{customer.customer_id}")
        assert resp.status_code == 401


class TestUpdateCustomerStatus:
    def test_update_status_to_active(self, client, db_session):
        admin = _make_admin(db_session)
        customer = _make_customer(db_session, status="PENDING")
        
        resp = client.put(
            f"/api/v1/admin/customers/{customer.customer_id}/status",
            json={"status": "ACTIVE"},
            headers=_auth_headers_admin(str(admin.admin_id)),
        )
        
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ACTIVE"
        
        # Verify DB state
        db_session.refresh(customer)
        assert customer.status == "ACTIVE"

    def test_update_status_to_suspended(self, client, db_session):
        admin = _make_admin(db_session)
        customer = _make_customer(db_session, status="ACTIVE")
        
        resp = client.put(
            f"/api/v1/admin/customers/{customer.customer_id}/status",
            json={"status": "SUSPENDED"},
            headers=_auth_headers_admin(str(admin.admin_id)),
        )
        
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "SUSPENDED"
        
        db_session.refresh(customer)
        assert customer.status == "SUSPENDED"

    def test_update_status_to_disabled(self, client, db_session):
        admin = _make_admin(db_session)
        customer = _make_customer(db_session, status="ACTIVE")
        
        resp = client.put(
            f"/api/v1/admin/customers/{customer.customer_id}/status",
            json={"status": "DISABLED"},
            headers=_auth_headers_admin(str(admin.admin_id)),
        )
        
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "DISABLED"

    def test_update_status_invalid_status_400(self, client, db_session):
        admin = _make_admin(db_session)
        customer = _make_customer(db_session)
        
        resp = client.put(
            f"/api/v1/admin/customers/{customer.customer_id}/status",
            json={"status": "INVALID"},
            headers=_auth_headers_admin(str(admin.admin_id)),
        )
        
        assert resp.status_code == 422  # Pydantic validation error

    def test_update_status_customer_not_found_404(self, client, db_session):
        admin = _make_admin(db_session)
        
        resp = client.put(
            "/api/v1/admin/customers/CUS-NOTFOUND/status",
            json={"status": "ACTIVE"},
            headers=_auth_headers_admin(str(admin.admin_id)),
        )
        
        assert resp.status_code == 404

    def test_update_status_unauthenticated_401(self, client, db_session):
        customer = _make_customer(db_session)
        
        resp = client.put(
            f"/api/v1/admin/customers/{customer.customer_id}/status",
            json={"status": "ACTIVE"},
        )
        
        assert resp.status_code == 401

    def test_update_status_non_admin_401(self, client, db_session):
        customer = _make_customer(db_session)
        another_customer = _make_customer(db_session)
        token = create_access_token({"sub": another_customer.email})
        
        resp = client.put(
            f"/api/v1/admin/customers/{customer.customer_id}/status",
            json={"status": "SUSPENDED"},
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert resp.status_code == 401

    def test_update_status_persists_correctly(self, client, db_session):
        admin = _make_admin(db_session)
        customer = _make_customer(db_session, status="ACTIVE")
        original_email = customer.email
        
        resp = client.put(
            f"/api/v1/admin/customers/{customer.customer_id}/status",
            json={"status": "SUSPENDED"},
            headers=_auth_headers_admin(str(admin.admin_id)),
        )
        
        assert resp.status_code == 200
        
        # Verify other fields unchanged
        db_session.refresh(customer)
        assert customer.email == original_email
        assert customer.status == "SUSPENDED"

    def test_failed_update_does_not_persist(self, client, db_session):
        admin = _make_admin(db_session)
        customer = _make_customer(db_session, status="ACTIVE")
        
        # Try invalid status
        resp = client.put(
            f"/api/v1/admin/customers/{customer.customer_id}/status",
            json={"status": "BANANA"},
            headers=_auth_headers_admin(str(admin.admin_id)),
        )
        
        assert resp.status_code == 422
        
        # Verify status unchanged
        db_session.refresh(customer)
        assert customer.status == "ACTIVE"
