from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch
from uuid import uuid4

from app.core.database import SessionLocal
from app.core.security import create_access_token, create_refresh_token, get_password_hash
from app.models.customer import Customer
from app.models.vendor import Vendor


class _FakeRedis:
    def __init__(self):
        self._store: dict[str, tuple[str, int | None]] = {}

    def ping(self):
        return True

    def setex(self, key: str, ttl: int, value: str):
        self._store[key] = (value, ttl)
        return True

    def exists(self, key: str) -> int:
        return 1 if key in self._store else 0


def _create_customer(password: str = "Pass12345!") -> Customer:
    db = SessionLocal()
    customer = Customer(
        customer_id=f"CUS-{uuid4().hex[:16]}",
        full_name="Test Customer",
        email=f"customer-{uuid4().hex[:8]}@test.com",
        password_hash=get_password_hash(password),
        phone="+94770000000",
        email_verified=True,
        status="ACTIVE",
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    db.close()
    return customer


def _create_vendor(password: str = "VendPass123!", approved: bool = True) -> Vendor:
    db = SessionLocal()
    vendor = Vendor(
        vendor_id=f"VEN-{uuid4().hex[:16]}",
        business_name="Test Vendor",
        display_name="Test Vendor",
        email=f"vendor-{uuid4().hex[:8]}@test.com",
        password_hash=get_password_hash(password),
        is_verified=True,
        approval_status="APPROVED" if approved else "PENDING",
        location_base="Colombo",
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    db.close()
    return vendor


def test_customer_refresh_rejects_access_token(client):
    access = create_access_token({"sub": "user@test.com", "role": "CUSTOMER"})
    r = client.post("/api/v1/auth/customer/token/refresh", json={"refreshToken": access})
    assert r.status_code == 401


def test_customer_refresh_rejects_wrong_role(client):
    refresh = create_refresh_token({"sub": "user@test.com", "role": "VENDOR"})
    r = client.post("/api/v1/auth/customer/token/refresh", json={"refreshToken": refresh})
    assert r.status_code == 401


def test_customer_refresh_expired_token(client):
    refresh = create_refresh_token(
        {"sub": "user@test.com", "role": "CUSTOMER"},
        expires_delta=timedelta(seconds=-1),
    )
    r = client.post("/api/v1/auth/customer/token/refresh", json={"refreshToken": refresh})
    assert r.status_code == 401


def test_vendor_refresh_rejects_wrong_role(client):
    refresh = create_refresh_token({"sub": "user@test.com", "role": "CUSTOMER"})
    r = client.post("/api/v1/auth/vendor/token/refresh", json={"refreshToken": refresh})
    assert r.status_code == 401


def test_password_reset_verify_otp_requires_redis(client, monkeypatch):
    monkeypatch.setenv("SKIP_EMAIL_VERIFICATION", "true")
    customer = _create_customer()
    with patch("app.services.auth_service._get_redis", return_value=None):
        r = client.post(
            "/api/v1/auth/customer/password/verify-otp",
            json={"email": customer.email, "otp": "123456"},
        )
    assert r.status_code == 503


def test_delete_customer_blacklists_token(client):
    customer = _create_customer()
    token = create_access_token({"sub": customer.email, "role": "CUSTOMER"})
    fake_redis = _FakeRedis()
    with patch("app.services.auth_service._get_redis", return_value=fake_redis), patch(
        "app.core.security.is_token_blacklisted",
        side_effect=lambda t: bool(fake_redis.exists(f"blacklist:{t}")),
    ):
        deleted = client.delete(
            "/api/v1/auth/customer/delete",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert deleted.status_code == 200
        # token should be rejected after delete/blacklist
        r = client.get("/api/v1/customers/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 401


def test_delete_vendor_blacklists_token(client):
    vendor = _create_vendor()
    token = create_access_token({"sub": vendor.email, "role": "VENDOR"})
    fake_redis = _FakeRedis()
    with patch("app.services.auth_service._get_redis", return_value=fake_redis), patch(
        "app.core.security.is_token_blacklisted",
        side_effect=lambda t: bool(fake_redis.exists(f"blacklist:{t}")),
    ):
        deleted = client.delete(
            "/api/v1/auth/vendor/delete",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert deleted.status_code == 200
        r = client.get("/api/v1/vendors/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 401
