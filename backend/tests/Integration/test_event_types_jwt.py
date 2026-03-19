"""
tests/Integration/test_event_types_jwt.py

Verifies that GET /event-types and GET /event-templates accept any valid JWT
(customer OR vendor), not just a customer token — the fix applied to
customer_router.py via get_authenticated_user dependency.
"""
from uuid import uuid4

from app.core.database import SessionLocal
from app.core.security import create_access_token
from app.models.customer import Customer
from app.models.vendor import Vendor


def _make_customer_token() -> str:
    db = SessionLocal()
    try:
        email = f"etype-cust-{uuid4().hex[:8]}@test.com"
        customer = Customer(
            full_name="EventType Customer",
            email=email,
            password_hash="x",
            email_verified=True,
            status="ACTIVE",
            customer_id=f"CUS-{uuid4().hex[:16]}",
        )
        db.add(customer)
        db.commit()
        return create_access_token(data={"sub": email})
    finally:
        db.close()


def _make_vendor_token() -> str:
    db = SessionLocal()
    try:
        email = f"etype-vend-{uuid4().hex[:8]}@test.com"
        vendor = Vendor(
            business_name=f"VendorET {uuid4().hex[:6]}",
            display_name="ET Vendor",
            email=email,
            is_verified=True,
            approval_status="APPROVED",
        )
        db.add(vendor)
        db.commit()
        return create_access_token(data={"sub": email})
    finally:
        db.close()


class TestEventTypesJWT:

    def test_event_types_requires_auth(self, client):
        r = client.get("/api/v1/event-types")
        assert r.status_code == 401

    def test_event_types_accessible_with_customer_token(self, client):
        token = _make_customer_token()
        r = client.get("/api/v1/event-types", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        body = r.json()
        assert "items" in body
        assert isinstance(body["items"], list)
        assert len(body["items"]) > 0

    def test_event_types_accessible_with_vendor_token(self, client):
        token = _make_vendor_token()
        r = client.get("/api/v1/event-types", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        body = r.json()
        assert "items" in body
        assert isinstance(body["items"], list)

    def test_event_types_returns_non_empty_list(self, auth_client):
        r = auth_client.get("/api/v1/event-types")
        assert r.status_code == 200
        assert len(r.json()["items"]) >= 1

    def test_event_types_invalid_token_returns_401(self, client):
        r = client.get("/api/v1/event-types", headers={"Authorization": "Bearer bad.token.here"})
        assert r.status_code == 401


class TestEventTemplatesJWT:

    def test_event_templates_requires_auth(self, client):
        r = client.get("/api/v1/event-templates")
        assert r.status_code == 401

    def test_event_templates_accessible_with_customer_token(self, client):
        token = _make_customer_token()
        r = client.get("/api/v1/event-templates", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        body = r.json()
        assert "items" in body
        assert isinstance(body["items"], list)
        assert len(body["items"]) > 0

    def test_event_templates_accessible_with_vendor_token(self, client):
        token = _make_vendor_token()
        r = client.get("/api/v1/event-templates", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        body = r.json()
        assert "items" in body
        assert isinstance(body["items"], list)

    def test_event_templates_returns_non_empty_list(self, auth_client):
        r = auth_client.get("/api/v1/event-templates")
        assert r.status_code == 200
        assert len(r.json()["items"]) >= 1

    def test_event_templates_invalid_token_returns_401(self, client):
        r = client.get("/api/v1/event-templates", headers={"Authorization": "Bearer bad.token.here"})
        assert r.status_code == 401