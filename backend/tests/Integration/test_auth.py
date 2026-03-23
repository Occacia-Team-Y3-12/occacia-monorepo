"""
tests/Integration/test_auth.py

Full auth test suite covering:
  - Customer registration, verification, login, refresh, logout [E05]
  - Vendor registration, verification, login, logout [E06]
  - Password reset OTP flow (customer + vendor)
  - Token blacklist enforcement after logout
  - Edge cases: duplicate email, wrong password, expired/invalid tokens
  - Redis-down graceful degradation

Redis strategy
--------------
The CI runner does not have the `redis` Python package installed and has no
Redis server.  All tests that need to seed or check Redis use the
_seed_otp / _FakeRedis helpers below, which patch `_get_redis` at the
auth_service level with an in-process dict-backed fake.  No direct
`import redis` calls appear in test code.
"""
from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch
from uuid import uuid4

import pytest

from app.core.database import SessionLocal
from app.core.security import create_access_token, create_refresh_token
from app.models.customer import Customer
from app.models.organization import Organization
from app.models.vendor import Vendor
from app.services.auth_service import auth_service


# ─────────────────────────────────────────────────────────────────────────────
# In-process fake Redis  (no redis package required)
# ─────────────────────────────────────────────────────────────────────────────

class _FakeRedis:
    """Minimal dict-backed Redis fake — supports get / setex / delete / exists."""

    def __init__(self):
        self._store: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self._store.get(key)

    def setex(self, key: str, ttl: int, value: str) -> None:
        self._store[key] = value

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def exists(self, key: str) -> int:
        return 1 if key in self._store else 0

    def ping(self) -> bool:
        return True


def _make_fake_redis() -> _FakeRedis:
    return _FakeRedis()


def _seed_otp(fake_redis: _FakeRedis, role: str, email: str, otp: str) -> None:
    fake_redis.setex(f"pwd_otp:{role}:{email}", 300, otp)


# ─────────────────────────────────────────────────────────────────────────────
# Shared test helpers
# ─────────────────────────────────────────────────────────────────────────────

def _uid() -> str:
    return uuid4().hex[:8]


def _customer_email() -> str:
    return f"customer-{_uid()}@test.com"


def _vendor_email() -> str:
    return f"vendor-{_uid()}@test.com"


def _register_customer(client, email: str, password: str = "Pass12345!"):
    return client.post("/api/v1/auth/customer/register", json={
        "fullName": "Test User",
        "email": email,
        "password": password,
        "phone": "+94771234567",
    })


def _activate_customer(email: str) -> Customer:
    db = SessionLocal()
    try:
        c = db.query(Customer).filter(Customer.email == email).first()
        assert c is not None, f"Customer {email} not found"
        c.email_verified = True
        c.status = "ACTIVE"
        db.commit()
        db.refresh(c)
        return c
    finally:
        db.close()


def _register_vendor(client, email: str, password: str = "Pass123!"):
    return client.post("/api/v1/auth/vendor/register", json={
        "business_name": f"Biz {_uid()}",
        "email": email,
        "password": password,
    })


def _activate_vendor(email: str) -> Vendor:
    db = SessionLocal()
    try:
        v = db.query(Vendor).filter(Vendor.email == email).first()
        assert v is not None, f"Vendor {email} not found"
        v.is_verified = True
        v.approval_status = "APPROVED"
        db.commit()
        db.refresh(v)
        return v
    finally:
        db.close()


def _login_customer(client, email: str, password: str = "Pass12345!"):
    return client.post("/api/v1/auth/customer/login",
                       data={"username": email, "password": password})


def _login_vendor(client, email: str, password: str = "Pass123!"):
    return client.post("/api/v1/auth/vendor/login",
                       data={"username": email, "password": password})


# ─────────────────────────────────────────────────────────────────────────────
# 1. CUSTOMER REGISTRATION
# ─────────────────────────────────────────────────────────────────────────────

class TestCustomerRegistration:

    def test_register_success(self, client):
        r = _register_customer(client, _customer_email())
        assert r.status_code == 201
        assert r.json()["message"] == "Registration successful. Please verify your email."

    def test_register_duplicate_email(self, client):
        email = _customer_email()
        _register_customer(client, email)
        assert _register_customer(client, email).status_code == 400

    def test_register_missing_required_fields(self, client):
        r = client.post("/api/v1/auth/customer/register",
                        json={"email": _customer_email()})
        assert r.status_code == 422

    def test_register_invalid_email_format(self, client):
        r = client.post("/api/v1/auth/customer/register", json={
            "fullName": "Test", "email": "not-an-email", "password": "Pass12345!",
        })
        assert r.status_code == 422

    def test_register_creates_pending_status(self, client):
        email = _customer_email()
        _register_customer(client, email)
        db = SessionLocal()
        try:
            c = db.query(Customer).filter(Customer.email == email).first()
            assert c is not None
            assert c.status == "PENDING"
            assert c.email_verified is False
        finally:
            db.close()

    def test_register_stores_verification_token(self, client):
        email = _customer_email()
        _register_customer(client, email)
        db = SessionLocal()
        try:
            c = db.query(Customer).filter(Customer.email == email).first()
            assert c.verification_token is not None
        finally:
            db.close()


# ─────────────────────────────────────────────────────────────────────────────
# 2. CUSTOMER EMAIL VERIFICATION
# ─────────────────────────────────────────────────────────────────────────────

class TestCustomerEmailVerification:

    def _token(self, email: str) -> str:
        db = SessionLocal()
        try:
            return db.query(Customer).filter(Customer.email == email).first().verification_token
        finally:
            db.close()

    def test_verify_success(self, client):
        email = _customer_email()
        _register_customer(client, email)
        r = client.get("/api/v1/auth/customer/verify-email",
                       params={"token": self._token(email)})
        assert r.status_code == 200
        assert "verified" in r.json()["message"].lower()

    def test_verify_activates_customer(self, client):
        email = _customer_email()
        _register_customer(client, email)
        client.get("/api/v1/auth/customer/verify-email",
                   params={"token": self._token(email)})
        db = SessionLocal()
        try:
            c = db.query(Customer).filter(Customer.email == email).first()
            assert c.status == "ACTIVE"
            assert c.email_verified is True
        finally:
            db.close()

    def test_verify_invalid_token(self, client):
        r = client.get("/api/v1/auth/customer/verify-email",
                       params={"token": "bad-token"})
        assert r.status_code == 400

    def test_verify_already_verified(self, client):
        email = _customer_email()
        _register_customer(client, email)
        token = self._token(email)
        client.get("/api/v1/auth/customer/verify-email", params={"token": token})
        r = client.get("/api/v1/auth/customer/verify-email", params={"token": token})
        assert r.status_code == 200
        assert "already" in r.json()["message"].lower()

    def test_resend_success(self, client):
        email = _customer_email()
        _register_customer(client, email)
        r = client.post("/api/v1/auth/customer/email-verification/resend",
                        json={"email": email})
        assert r.status_code == 200
        assert "resent" in r.json()["message"].lower()

    def test_resend_unknown_email(self, client):
        r = client.post("/api/v1/auth/customer/email-verification/resend",
                        json={"email": "nobody@test.com"})
        assert r.status_code == 400

    def test_resend_already_active(self, client):
        email = _customer_email()
        _register_customer(client, email)
        _activate_customer(email)
        r = client.post("/api/v1/auth/customer/email-verification/resend",
                        json={"email": email})
        assert r.status_code == 400


# ─────────────────────────────────────────────────────────────────────────────
# 3. CUSTOMER LOGIN
# ─────────────────────────────────────────────────────────────────────────────

class TestCustomerLogin:

    def test_login_success(self, client, monkeypatch):
        monkeypatch.setenv("SKIP_EMAIL_VERIFICATION", "true")
        email = _customer_email()
        _register_customer(client, email)
        _activate_customer(email)
        r = _login_customer(client, email)
        assert r.status_code == 200
        data = r.json()
        assert "accessToken" in data
        assert "refreshToken" in data
        assert data["user"]["role"] == "CUSTOMER"

    def test_login_wrong_password(self, client):
        email = _customer_email()
        _register_customer(client, email)
        _activate_customer(email)
        assert _login_customer(client, email, "WrongPass!").status_code == 401

    def test_login_unknown_email(self, client):
        assert _login_customer(client, "nobody@test.com").status_code == 401

    def test_login_unverified_blocked(self, client, monkeypatch):
        monkeypatch.delenv("SKIP_EMAIL_VERIFICATION", raising=False)
        email = _customer_email()
        _register_customer(client, email)
        assert _login_customer(client, email).status_code in (401, 403)

    def test_login_inactive_account_blocked(self, client, monkeypatch):
        monkeypatch.setenv("SKIP_EMAIL_VERIFICATION", "true")
        email = _customer_email()
        _register_customer(client, email)
        db = SessionLocal()
        try:
            c = db.query(Customer).filter(Customer.email == email).first()
            c.email_verified = True  # verified but not ACTIVE
            db.commit()
        finally:
            db.close()
        assert _login_customer(client, email).status_code == 403

    def test_login_user_fields_shape(self, client, monkeypatch):
        monkeypatch.setenv("SKIP_EMAIL_VERIFICATION", "true")
        email = _customer_email()
        _register_customer(client, email)
        _activate_customer(email)
        user = _login_customer(client, email).json()["user"]
        for field in ("userId", "email", "role", "status"):
            assert field in user


# ─────────────────────────────────────────────────────────────────────────────
# 4. CUSTOMER TOKEN REFRESH
# ─────────────────────────────────────────────────────────────────────────────

class TestCustomerTokenRefresh:

    def _tokens(self, client, monkeypatch) -> dict:
        monkeypatch.setenv("SKIP_EMAIL_VERIFICATION", "true")
        email = _customer_email()
        _register_customer(client, email)
        _activate_customer(email)
        return _login_customer(client, email).json()

    def test_refresh_success(self, client, monkeypatch):
        tokens = self._tokens(client, monkeypatch)
        r = client.post("/api/v1/auth/customer/token/refresh",
                        json={"refreshToken": tokens["refreshToken"]})
        assert r.status_code == 200
        assert "accessToken" in r.json()

    def test_refresh_invalid_token(self, client):
        r = client.post("/api/v1/auth/customer/token/refresh",
                        json={"refreshToken": "not-a-token"})
        assert r.status_code == 401

    def test_refresh_access_token_rejected(self, client, monkeypatch):
        tokens = self._tokens(client, monkeypatch)
        r = client.post("/api/v1/auth/customer/token/refresh",
                        json={"refreshToken": tokens["accessToken"]})
        assert r.status_code == 401

    def test_refresh_after_account_suspended(self, client, monkeypatch):
        tokens = self._tokens(client, monkeypatch)
        email = tokens["user"]["email"]
        db = SessionLocal()
        try:
            c = db.query(Customer).filter(Customer.email == email).first()
            c.status = "SUSPENDED"
            db.commit()
        finally:
            db.close()
        r = client.post("/api/v1/auth/customer/token/refresh",
                        json={"refreshToken": tokens["refreshToken"]})
        assert r.status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
# 5. CUSTOMER LOGOUT [E05]
# ─────────────────────────────────────────────────────────────────────────────

class TestCustomerLogout:

    def _login(self, client, monkeypatch) -> tuple[str, str]:
        monkeypatch.setenv("SKIP_EMAIL_VERIFICATION", "true")
        email = _customer_email()
        _register_customer(client, email)
        _activate_customer(email)
        return _login_customer(client, email).json()["accessToken"], email

    def test_logout_returns_200(self, client, monkeypatch):
        token, _ = self._login(client, monkeypatch)
        r = client.post("/api/v1/auth/customer/logout",
                        headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200

    def test_logout_returns_message(self, client, monkeypatch):
        token, _ = self._login(client, monkeypatch)
        r = client.post("/api/v1/auth/customer/logout",
                        headers={"Authorization": f"Bearer {token}"})
        assert "logged out" in r.json()["message"].lower()

    def test_logout_requires_auth(self, client):
        assert client.post("/api/v1/auth/customer/logout").status_code in (401, 403)

    def test_logout_invalid_token_rejected(self, client):
        r = client.post("/api/v1/auth/customer/logout",
                        headers={"Authorization": "Bearer fake"})
        assert r.status_code in (401, 403)

    def test_logout_blacklists_token(self, client, monkeypatch):
        """Token must be rejected after logout (fake Redis — no real Redis needed)."""
        fake_redis = _make_fake_redis()
        monkeypatch.setenv("SKIP_EMAIL_VERIFICATION", "true")
        email = _customer_email()
        _register_customer(client, email)
        _activate_customer(email)

        with patch("app.services.auth_service._get_redis", return_value=fake_redis), \
             patch("app.core.security.is_token_blacklisted",
                   side_effect=lambda t: bool(fake_redis.exists(f"blacklist:{t}"))):
            token = _login_customer(client, email).json()["accessToken"]

            assert client.get("/api/v1/customers/me",
                              headers={"Authorization": f"Bearer {token}"}).status_code == 200

            client.post("/api/v1/auth/customer/logout",
                        headers={"Authorization": f"Bearer {token}"})

            assert client.get("/api/v1/customers/me",
                              headers={"Authorization": f"Bearer {token}"}).status_code == 401

    def test_logout_does_not_affect_other_sessions(self, client, monkeypatch):
        """Token A blacklisted after logout must not affect token B (a different session)."""
        fake_redis = _make_fake_redis()
        monkeypatch.setenv("SKIP_EMAIL_VERIFICATION", "true")
        email = _customer_email()
        _register_customer(client, email)
        _activate_customer(email)

        # Log in once to get token_a (the one we will log out).
        # Mint token_b directly with a unique jti so it is a genuinely different
        # JWT string even when both are created within the same second.
        with patch("app.services.auth_service._get_redis", return_value=fake_redis), \
             patch("app.core.security.is_token_blacklisted",
                   side_effect=lambda t: bool(fake_redis.exists(f"blacklist:{t}"))):
            token_a = _login_customer(client, email).json()["accessToken"]
            token_b = create_access_token(
                data={"sub": email, "role": "CUSTOMER", "jti": _uid()},
                expires_delta=timedelta(hours=1),
            )

            client.post("/api/v1/auth/customer/logout",
                        headers={"Authorization": f"Bearer {token_a}"})

            assert client.get("/api/v1/customers/me",
                              headers={"Authorization": f"Bearer {token_b}"}).status_code == 200

    def test_logout_redis_down_still_200(self, client, monkeypatch):
        token, _ = self._login(client, monkeypatch)
        monkeypatch.setattr("app.services.auth_service._get_redis", lambda: None)
        r = client.post("/api/v1/auth/customer/logout",
                        headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200

    def test_logout_expired_token_rejected(self, client, monkeypatch):
        monkeypatch.setenv("SKIP_EMAIL_VERIFICATION", "true")
        email = _customer_email()
        _register_customer(client, email)
        _activate_customer(email)
        expired = create_access_token(
            data={"sub": email, "role": "CUSTOMER"},
            expires_delta=timedelta(seconds=-1),
        )
        r = client.post("/api/v1/auth/customer/logout",
                        headers={"Authorization": f"Bearer {expired}"})
        assert r.status_code in (401, 403)


# ─────────────────────────────────────────────────────────────────────────────
# 6. CUSTOMER PASSWORD RESET (OTP flow)
# ─────────────────────────────────────────────────────────────────────────────

class TestCustomerPasswordReset:

    def test_forgot_known_email(self, client):
        email = _customer_email()
        _register_customer(client, email)
        fake_redis = _make_fake_redis()
        with patch("app.services.auth_service._get_redis", return_value=fake_redis):
            r = client.post("/api/v1/auth/customer/password/forgot",
                            json={"email": email})
        assert r.status_code == 200

    def test_forgot_unknown_email_still_200(self, client):
        r = client.post("/api/v1/auth/customer/password/forgot",
                        json={"email": "nobody@test.com"})
        assert r.status_code == 200

    def test_resend_otp_replaces_previous_customer_otp(self, client):
        email = _customer_email()
        _register_customer(client, email)
        fake_redis = _make_fake_redis()
        with patch("app.services.auth_service._get_redis", return_value=fake_redis), \
             patch("app.services.auth_service._generate_otp", side_effect=["111111", "222222"]):
            first = client.post("/api/v1/auth/customer/password/forgot",
                                json={"email": email})
            resend = client.post("/api/v1/auth/customer/password/forgot/resend-otp",
                                 json={"email": email})
            old_otp = client.post("/api/v1/auth/customer/password/verify-otp",
                                  json={"email": email, "otp": "111111"})
            new_otp = client.post("/api/v1/auth/customer/password/verify-otp",
                                  json={"email": email, "otp": "222222"})
        assert first.status_code == 200
        assert resend.status_code == 200
        assert old_otp.status_code == 400
        assert new_otp.status_code == 200

    def test_reset_invalid_token(self, client):
        r = client.post("/api/v1/auth/customer/password/reset",
                        json={"reset_token": "bad", "new_password": "NewPass123!"})
        assert r.status_code == 400

    def test_verify_otp_wrong_code(self, client):
        email = _customer_email()
        _register_customer(client, email)
        fake_redis = _make_fake_redis()
        _seed_otp(fake_redis, "customer", email, "123456")
        with patch("app.services.auth_service._get_redis", return_value=fake_redis):
            r = client.post("/api/v1/auth/customer/password/verify-otp",
                            json={"email": email, "otp": "000000"})
        assert r.status_code == 400

    def test_verify_otp_consumed_after_use(self, client):
        email = _customer_email()
        _register_customer(client, email)
        fake_redis = _make_fake_redis()
        _seed_otp(fake_redis, "customer", email, "777666")
        with patch("app.services.auth_service._get_redis", return_value=fake_redis):
            client.post("/api/v1/auth/customer/password/verify-otp",
                        json={"email": email, "otp": "777666"})
            r2 = client.post("/api/v1/auth/customer/password/verify-otp",
                             json={"email": email, "otp": "777666"})
        assert r2.status_code == 400

    def test_verify_otp_expired_key(self, client):
        email = _customer_email()
        _register_customer(client, email)
        fake_redis = _make_fake_redis()  # empty — no OTP seeded
        with patch("app.services.auth_service._get_redis", return_value=fake_redis):
            r = client.post("/api/v1/auth/customer/password/verify-otp",
                            json={"email": email, "otp": "123456"})
        assert r.status_code in (400, 503)

    def test_full_otp_reset_flow(self, client, monkeypatch):
        monkeypatch.setenv("SKIP_EMAIL_VERIFICATION", "true")
        email = _customer_email()
        _register_customer(client, email)
        _activate_customer(email)

        fake_redis = _make_fake_redis()
        _seed_otp(fake_redis, "customer", email, "654321")

        with patch("app.services.auth_service._get_redis", return_value=fake_redis):
            r2 = client.post("/api/v1/auth/customer/password/verify-otp",
                             json={"email": email, "otp": "654321"})
            assert r2.status_code == 200
            reset_token = r2.json()["resetToken"]

            r3 = client.post("/api/v1/auth/customer/password/reset",
                             json={"reset_token": reset_token,
                                   "new_password": "NewPass999!"})
            assert r3.status_code == 200

        assert _login_customer(client, email, "NewPass999!").status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# 7. VENDOR REGISTRATION
# ─────────────────────────────────────────────────────────────────────────────

class TestVendorRegistration:

    def test_register_success(self, client):
        assert _register_vendor(client, _vendor_email()).status_code == 201

    def test_register_duplicate_email(self, client):
        email = _vendor_email()
        _register_vendor(client, email)
        assert _register_vendor(client, email).status_code == 400

    def test_register_duplicate_business_name(self, client):
        name = f"SameName-{_uid()}"
        client.post("/api/v1/auth/vendor/register",
                    json={"business_name": name, "email": _vendor_email(),
                          "password": "Pass123!"})
        r = client.post("/api/v1/auth/vendor/register",
                        json={"business_name": name, "email": _vendor_email(),
                              "password": "Pass123!"})
        assert r.status_code == 400

    def test_register_missing_fields(self, client):
        r = client.post("/api/v1/auth/vendor/register",
                        json={"email": _vendor_email()})
        assert r.status_code == 422

    def test_register_creates_pending_vendor(self, client):
        email = _vendor_email()
        _register_vendor(client, email)
        db = SessionLocal()
        try:
            v = db.query(Vendor).filter(Vendor.email == email).first()
            assert v is not None
            assert v.approval_status == "PENDING"
        finally:
            db.close()

    def test_register_with_display_name_contract(self, client):
        r = client.post("/api/v1/auth/vendor/register", json={
            "email": _vendor_email(),
            "password": "Pass123!",
            "displayName": "Vendor Display",
        })
        assert r.status_code == 201

    def test_register_join_existing_organization(self, client):
        db = SessionLocal()
        try:
            org = Organization(
                name=f"Org {_uid()}",
                registration_number=f"ORG-{_uid()}",
                email=f"org-{_uid()}@test.com",
                status="approved",
            )
            db.add(org)
            db.commit()
            db.refresh(org)
            org_code = org.registration_number
            org_id = org.id
            org_name = org.name
        finally:
            db.close()

        email = _vendor_email()
        r = client.post("/api/v1/auth/vendor/register", json={
            "email": email,
            "password": "Pass123!",
            "displayName": "Vendor Display",
            "organizationCode": org_code,
        })
        assert r.status_code == 201

        db = SessionLocal()
        try:
            v = db.query(Vendor).filter(Vendor.email == email).first()
            assert v is not None
            assert v.organization_id == org_id
            assert v.business_name == org_name
        finally:
            db.close()

    def test_register_create_organization(self, client):
        email = _vendor_email()
        registration_number = f"REG-{_uid()}"
        organization_name = f"Org {_uid()}"
        r = client.post("/api/v1/auth/vendor/register", json={
            "email": email,
            "password": "Pass123!",
            "displayName": "Vendor Display",
            "organization": {
                "name": organization_name,
                "registrationNumber": registration_number,
                "email": f"org-{_uid()}@test.com",
                "phone": "+94770000000",
                "address": "Colombo",
                "kymDetails": {
                    "businessRegNumber": registration_number,
                },
            },
        })
        assert r.status_code == 201

        db = SessionLocal()
        try:
            v = db.query(Vendor).filter(Vendor.email == email).first()
            org = db.query(Organization).filter(
                Organization.registration_number == registration_number
            ).first()
            assert v is not None
            assert org is not None
            assert v.organization_id == org.id
            assert v.business_name == organization_name
        finally:
            db.close()


# ─────────────────────────────────────────────────────────────────────────────
# 8. VENDOR EMAIL VERIFICATION
# ─────────────────────────────────────────────────────────────────────────────

class TestVendorEmailVerification:

    def test_resend_success(self, client):
        email = _vendor_email()
        _register_vendor(client, email)
        r = client.post("/api/v1/auth/vendor/email-verification/resend",
                        json={"email": email})
        assert r.status_code == 200

    def test_resend_unknown_email(self, client):
        r = client.post("/api/v1/auth/vendor/email-verification/resend",
                        json={"email": "nobody@vendor.com"})
        assert r.status_code == 400

    def test_verify_invalid_token(self, client):
        r = client.get("/api/v1/auth/vendor/verify-email",
                       params={"token": "bad-token"})
        assert r.status_code == 400

    def test_resend_already_verified_rejected(self, client):
        email = _vendor_email()
        _register_vendor(client, email)
        db = SessionLocal()
        try:
            v = db.query(Vendor).filter(Vendor.email == email).first()
            v.is_verified = True
            db.commit()
        finally:
            db.close()
        r = client.post("/api/v1/auth/vendor/email-verification/resend",
                        json={"email": email})
        assert r.status_code == 400

    def test_verify_sets_pending_admin_message(self, client):
        email = _vendor_email()
        _register_vendor(client, email)
        token, _ = auth_service._create_verification_token(
            email,
            token_type="verify_vendor_email",
            hours=24,
        )

        r = client.get("/api/v1/auth/vendor/verify-email", params={"token": token})
        assert r.status_code == 200
        assert "pending admin approval" in r.json()["message"].lower()

        db = SessionLocal()
        try:
            vendor = db.query(Vendor).filter(Vendor.email == email).first()
            assert vendor.is_verified is True
            assert vendor.approval_status == "PENDING"
        finally:
            db.close()


# ─────────────────────────────────────────────────────────────────────────────
# 9. VENDOR LOGIN
# ─────────────────────────────────────────────────────────────────────────────

class TestVendorLogin:

    def test_login_success(self, client, monkeypatch):
        monkeypatch.setenv("SKIP_EMAIL_VERIFICATION", "true")
        email = _vendor_email()
        _register_vendor(client, email)
        _activate_vendor(email)
        r = _login_vendor(client, email)
        assert r.status_code == 200
        data = r.json()
        assert "accessToken" in data or "access_token" in data

    def test_login_wrong_password(self, client):
        email = _vendor_email()
        _register_vendor(client, email)
        assert _login_vendor(client, email, "WrongPass!").status_code == 401

    def test_login_unknown_email(self, client):
        assert _login_vendor(client, "nobody@vendor.com").status_code == 401

    def test_login_returns_tokens(self, client, monkeypatch):
        monkeypatch.setenv("SKIP_EMAIL_VERIFICATION", "true")
        email = _vendor_email()
        _register_vendor(client, email)
        _activate_vendor(email)
        data = _login_vendor(client, email).json()
        assert "accessToken" in data or "access_token" in data
        assert "refreshToken" in data or "refresh_token" in data

    def test_pending_vendor_blocked_from_login(self, client, monkeypatch):
        monkeypatch.setenv("SKIP_EMAIL_VERIFICATION", "true")
        email = _vendor_email()
        _register_vendor(client, email)
        r = _login_vendor(client, email)
        assert r.status_code == 403
        assert "pending admin approval" in r.json()["detail"].lower()

    def test_approved_vendor_accesses_protected_routes(self, client, monkeypatch):
        monkeypatch.setenv("SKIP_EMAIL_VERIFICATION", "true")
        email = _vendor_email()
        _register_vendor(client, email)
        _activate_vendor(email)
        data = _login_vendor(client, email).json()
        token = data.get("accessToken") or data.get("access_token")
        r = client.get("/api/v1/vendors/me",
                       headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200

    def test_pending_vendor_blocked_on_approval_routes(self, client, monkeypatch):
        monkeypatch.setenv("SKIP_EMAIL_VERIFICATION", "true")
        email = _vendor_email()
        _register_vendor(client, email)
        assert _login_vendor(client, email).status_code == 403


# ─────────────────────────────────────────────────────────────────────────────
# 10. VENDOR LOGOUT [E06]
# ─────────────────────────────────────────────────────────────────────────────

class TestVendorLogout:

    def _login(self, client, monkeypatch) -> str:
        monkeypatch.setenv("SKIP_EMAIL_VERIFICATION", "true")
        email = _vendor_email()
        _register_vendor(client, email)
        _activate_vendor(email)
        data = _login_vendor(client, email).json()
        return data.get("accessToken") or data.get("access_token")

    def test_logout_returns_200(self, client, monkeypatch):
        token = self._login(client, monkeypatch)
        r = client.post("/api/v1/auth/vendor/logout",
                        headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200

    def test_logout_returns_message(self, client, monkeypatch):
        token = self._login(client, monkeypatch)
        r = client.post("/api/v1/auth/vendor/logout",
                        headers={"Authorization": f"Bearer {token}"})
        assert "logged out" in r.json()["message"].lower()

    def test_logout_requires_auth(self, client):
        assert client.post("/api/v1/auth/vendor/logout").status_code in (401, 403)

    def test_logout_invalid_token_rejected(self, client):
        r = client.post("/api/v1/auth/vendor/logout",
                        headers={"Authorization": "Bearer fake"})
        assert r.status_code in (401, 403)

    def test_logout_blacklists_token(self, client, monkeypatch):
        fake_redis = _make_fake_redis()
        monkeypatch.setenv("SKIP_EMAIL_VERIFICATION", "true")
        email = _vendor_email()
        _register_vendor(client, email)
        _activate_vendor(email)

        with patch("app.services.auth_service._get_redis", return_value=fake_redis), \
             patch("app.core.security.is_token_blacklisted",
                   side_effect=lambda t: bool(fake_redis.exists(f"blacklist:{t}"))):
            data = _login_vendor(client, email).json()
            token = data.get("accessToken") or data.get("access_token")

            assert client.get("/api/v1/vendors/me",
                              headers={"Authorization": f"Bearer {token}"}).status_code == 200

            client.post("/api/v1/auth/vendor/logout",
                        headers={"Authorization": f"Bearer {token}"})

            assert client.get("/api/v1/vendors/me",
                              headers={"Authorization": f"Bearer {token}"}).status_code == 401

    def test_logout_does_not_affect_other_sessions(self, client, monkeypatch):
        """Token A blacklisted after logout must not affect token B (a different session)."""
        fake_redis = _make_fake_redis()
        monkeypatch.setenv("SKIP_EMAIL_VERIFICATION", "true")
        email = _vendor_email()
        _register_vendor(client, email)
        _activate_vendor(email)

        # Log in once to get token_a (the one we will log out).
        # Mint token_b directly with a unique jti so it is a genuinely different
        # JWT string even when both are created within the same second.
        with patch("app.services.auth_service._get_redis", return_value=fake_redis), \
             patch("app.core.security.is_token_blacklisted",
                   side_effect=lambda t: bool(fake_redis.exists(f"blacklist:{t}"))):
            d_a = _login_vendor(client, email).json()
            token_a = d_a.get("accessToken") or d_a.get("access_token")
            token_b = create_access_token(
                data={"sub": email, "role": "VENDOR", "jti": _uid()},
                expires_delta=timedelta(hours=1),
            )

            client.post("/api/v1/auth/vendor/logout",
                        headers={"Authorization": f"Bearer {token_a}"})

            assert client.get("/api/v1/vendors/me",
                              headers={"Authorization": f"Bearer {token_b}"}).status_code == 200

    def test_logout_redis_down_still_200(self, client, monkeypatch):
        token = self._login(client, monkeypatch)
        monkeypatch.setattr("app.services.auth_service._get_redis", lambda: None)
        r = client.post("/api/v1/auth/vendor/logout",
                        headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200

    def test_logout_expired_token_rejected(self, client, monkeypatch):
        monkeypatch.setenv("SKIP_EMAIL_VERIFICATION", "true")
        email = _vendor_email()
        _register_vendor(client, email)
        expired = create_access_token(
            data={"sub": email, "role": "VENDOR"},
            expires_delta=timedelta(seconds=-1),
        )
        r = client.post("/api/v1/auth/vendor/logout",
                        headers={"Authorization": f"Bearer {expired}"})
        assert r.status_code in (401, 403)


# ─────────────────────────────────────────────────────────────────────────────
# 11. VENDOR PASSWORD RESET (OTP flow)
# ─────────────────────────────────────────────────────────────────────────────

class TestVendorPasswordReset:

    def test_forgot_known_email(self, client):
        email = _vendor_email()
        _register_vendor(client, email)
        fake_redis = _make_fake_redis()
        with patch("app.services.auth_service._get_redis", return_value=fake_redis):
            r = client.post("/api/v1/auth/vendor/password/forgot",
                            json={"email": email})
        assert r.status_code == 200

    def test_forgot_unknown_email_still_200(self, client):
        r = client.post("/api/v1/auth/vendor/password/forgot",
                        json={"email": "nobody@vendor.com"})
        assert r.status_code == 200

    def test_resend_otp_replaces_previous_vendor_otp(self, client):
        email = _vendor_email()
        _register_vendor(client, email)
        fake_redis = _make_fake_redis()
        with patch("app.services.auth_service._get_redis", return_value=fake_redis), \
             patch("app.services.auth_service._generate_otp", side_effect=["333333", "444444"]):
            first = client.post("/api/v1/auth/vendor/password/forgot",
                                json={"email": email})
            resend = client.post("/api/v1/auth/vendor/password/forgot/resend-otp",
                                 json={"email": email})
            old_otp = client.post("/api/v1/auth/vendor/password/verify-otp",
                                  json={"email": email, "otp": "333333"})
            new_otp = client.post("/api/v1/auth/vendor/password/verify-otp",
                                  json={"email": email, "otp": "444444"})
        assert first.status_code == 200
        assert resend.status_code == 200
        assert old_otp.status_code == 400
        assert new_otp.status_code == 200

    def test_reset_invalid_token(self, client):
        r = client.post("/api/v1/auth/vendor/password/reset",
                        json={"reset_token": "bad", "new_password": "NewPass123!"})
        assert r.status_code == 400

    def test_verify_otp_wrong_code(self, client):
        email = _vendor_email()
        _register_vendor(client, email)
        fake_redis = _make_fake_redis()
        _seed_otp(fake_redis, "vendor", email, "888777")
        with patch("app.services.auth_service._get_redis", return_value=fake_redis):
            r = client.post("/api/v1/auth/vendor/password/verify-otp",
                            json={"email": email, "otp": "000000"})
        assert r.status_code == 400

    def test_verify_otp_consumed_after_use(self, client):
        email = _vendor_email()
        _register_vendor(client, email)
        fake_redis = _make_fake_redis()
        _seed_otp(fake_redis, "vendor", email, "222111")
        with patch("app.services.auth_service._get_redis", return_value=fake_redis):
            client.post("/api/v1/auth/vendor/password/verify-otp",
                        json={"email": email, "otp": "222111"})
            r2 = client.post("/api/v1/auth/vendor/password/verify-otp",
                             json={"email": email, "otp": "222111"})
        assert r2.status_code == 400

    def test_verify_otp_expired_key(self, client):
        email = _vendor_email()
        _register_vendor(client, email)
        fake_redis = _make_fake_redis()
        with patch("app.services.auth_service._get_redis", return_value=fake_redis):
            r = client.post("/api/v1/auth/vendor/password/verify-otp",
                            json={"email": email, "otp": "000000"})
        assert r.status_code in (400, 503)

    def test_full_otp_reset_flow(self, client, monkeypatch):
        monkeypatch.setenv("SKIP_EMAIL_VERIFICATION", "true")
        email = _vendor_email()
        _register_vendor(client, email)
        fake_redis = _make_fake_redis()
        _seed_otp(fake_redis, "vendor", email, "112233")

        with patch("app.services.auth_service._get_redis", return_value=fake_redis):
            r2 = client.post("/api/v1/auth/vendor/password/verify-otp",
                             json={"email": email, "otp": "112233"})
            assert r2.status_code == 200
            reset_token = r2.json()["resetToken"]

            r3 = client.post("/api/v1/auth/vendor/password/reset",
                             json={"reset_token": reset_token,
                                   "new_password": "NewVend999!"})
            assert r3.status_code == 200

        _activate_vendor(email)
        assert _login_vendor(client, email, "NewVend999!").status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# 12. VENDOR TOKEN REFRESH
# ─────────────────────────────────────────────────────────────────────────────

class TestVendorTokenRefresh:

    def _tokens(self, client, monkeypatch) -> dict:
        monkeypatch.setenv("SKIP_EMAIL_VERIFICATION", "true")
        email = _vendor_email()
        _register_vendor(client, email)
        _activate_vendor(email)
        return _login_vendor(client, email).json()

    def test_refresh_success(self, client, monkeypatch):
        tokens = self._tokens(client, monkeypatch)
        refresh = tokens.get("refreshToken") or tokens.get("refresh_token")
        r = client.post("/api/v1/auth/vendor/token/refresh",
                        json={"refreshToken": refresh})
        assert r.status_code == 200
        data = r.json()
        assert "accessToken" in data or "access_token" in data

    def test_refresh_invalid_token(self, client):
        r = client.post("/api/v1/auth/vendor/token/refresh",
                        json={"refreshToken": "not-a-token"})
        assert r.status_code == 401

    def test_refresh_access_token_rejected(self, client, monkeypatch):
        tokens = self._tokens(client, monkeypatch)
        access = tokens.get("accessToken") or tokens.get("access_token")
        r = client.post("/api/v1/auth/vendor/token/refresh",
                        json={"refreshToken": access})
        assert r.status_code == 401

    def test_refresh_wrong_role_rejected(self, client, monkeypatch):
        """Customer refresh token must not work on vendor endpoint."""
        monkeypatch.setenv("SKIP_EMAIL_VERIFICATION", "true")
        email = _customer_email()
        _register_customer(client, email)
        _activate_customer(email)
        customer_refresh = _login_customer(client, email).json()["refreshToken"]
        r = client.post("/api/v1/auth/vendor/token/refresh",
                        json={"refreshToken": customer_refresh})
        assert r.status_code == 401

    def test_refresh_pending_vendor_rejected(self, client, monkeypatch):
        monkeypatch.setenv("SKIP_EMAIL_VERIFICATION", "true")
        email = _vendor_email()
        _register_vendor(client, email)
        db = SessionLocal()
        try:
            v = db.query(Vendor).filter(Vendor.email == email).first()
            assert v is not None
            v.is_verified = True
            db.commit()
        finally:
            db.close()
        refresh = create_refresh_token(
            data={"sub": email, "role": "VENDOR"}, expires_delta=timedelta(days=7),
        )
        r = client.post("/api/v1/auth/vendor/token/refresh",
                        json={"refreshToken": refresh})
        assert r.status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
# 13. TOKEN BLACKLIST EDGE CASES
# ─────────────────────────────────────────────────────────────────────────────

class TestTokenBlacklist:

    def test_blacklisted_token_rejected_on_all_routes(self, client, monkeypatch):
        fake_redis = _make_fake_redis()
        monkeypatch.setenv("SKIP_EMAIL_VERIFICATION", "true")
        email = _customer_email()
        _register_customer(client, email)
        _activate_customer(email)

        with patch("app.services.auth_service._get_redis", return_value=fake_redis), \
             patch("app.core.security.is_token_blacklisted",
                   side_effect=lambda t: bool(fake_redis.exists(f"blacklist:{t}"))):
            token = _login_customer(client, email).json()["accessToken"]
            client.post("/api/v1/auth/customer/logout",
                        headers={"Authorization": f"Bearer {token}"})

            for method, path in [
                ("GET", "/api/v1/customers/me"),
                ("GET", "/api/v1/customers/events"),
            ]:
                r = client.request(method, path,
                                   headers={"Authorization": f"Bearer {token}"})
                assert r.status_code == 401, \
                    f"{method} {path} returned {r.status_code}, expected 401"

    def test_is_token_blacklisted_returns_false_for_valid_token(self):
        from app.core.security import is_token_blacklisted
        token = create_access_token(data={"sub": "test@test.com", "role": "CUSTOMER"})
        with patch("app.core.security.is_token_blacklisted", return_value=False):
            assert is_token_blacklisted(token) is False

    def test_vendor_blacklisted_token_rejected(self, client, monkeypatch):
        fake_redis = _make_fake_redis()
        monkeypatch.setenv("SKIP_EMAIL_VERIFICATION", "true")
        email = _vendor_email()
        _register_vendor(client, email)
        _activate_vendor(email)

        with patch("app.services.auth_service._get_redis", return_value=fake_redis), \
             patch("app.core.security.is_token_blacklisted",
                   side_effect=lambda t: bool(fake_redis.exists(f"blacklist:{t}"))):
            data = _login_vendor(client, email).json()
            token = data.get("accessToken") or data.get("access_token")

            client.post("/api/v1/auth/vendor/logout",
                        headers={"Authorization": f"Bearer {token}"})

            assert client.get("/api/v1/vendors/me",
                              headers={"Authorization": f"Bearer {token}"}).status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
# 14. RESET TOKEN ROLE ISOLATION
# ─────────────────────────────────────────────────────────────────────────────

class TestResetTokenRoleIsolation:

    def _customer_reset_token(self, client, email: str) -> str | None:
        fake_redis = _make_fake_redis()
        _seed_otp(fake_redis, "customer", email, "444555")
        with patch("app.services.auth_service._get_redis", return_value=fake_redis):
            resp = client.post("/api/v1/auth/customer/password/verify-otp",
                               json={"email": email, "otp": "444555"})
        return resp.json().get("resetToken") if resp.status_code == 200 else None

    def _vendor_reset_token(self, client, email: str) -> str | None:
        fake_redis = _make_fake_redis()
        _seed_otp(fake_redis, "vendor", email, "666777")
        with patch("app.services.auth_service._get_redis", return_value=fake_redis):
            resp = client.post("/api/v1/auth/vendor/password/verify-otp",
                               json={"email": email, "otp": "666777"})
        return resp.json().get("resetToken") if resp.status_code == 200 else None

    def test_customer_token_rejected_on_vendor_reset(self, client):
        email = _customer_email()
        _register_customer(client, email)
        token = self._customer_reset_token(client, email)
        assert token is not None
        r = client.post("/api/v1/auth/vendor/password/reset",
                        json={"reset_token": token, "new_password": "NewPass999!"})
        assert r.status_code == 400

    def test_vendor_token_rejected_on_customer_reset(self, client):
        email = _vendor_email()
        _register_vendor(client, email)
        token = self._vendor_reset_token(client, email)
        assert token is not None
        r = client.post("/api/v1/auth/customer/password/reset",
                        json={"reset_token": token, "new_password": "NewPass999!"})
        assert r.status_code == 400


# ─────────────────────────────────────────────────────────────────────────────
# 15. UNAUTHENTICATED ACCESS
# ─────────────────────────────────────────────────────────────────────────────

class TestUnauthenticatedAccess:

    def test_no_token_customer_route(self, client):
        assert client.get("/api/v1/customers/me").status_code in (401, 403)

    def test_no_token_vendor_route(self, client):
        assert client.get("/api/v1/vendors/me").status_code in (401, 403)

    def test_no_token_customer_logout(self, client):
        assert client.post("/api/v1/auth/customer/logout").status_code in (401, 403)

    def test_no_token_vendor_logout(self, client):
        assert client.post("/api/v1/auth/vendor/logout").status_code in (401, 403)

    def test_no_token_admin_logout(self, client):
        assert client.post("/api/v1/auth/admin/logout").status_code in (401, 403)

    def test_malformed_bearer_header(self, client):
        r = client.get("/api/v1/customers/me",
                       headers={"Authorization": "NotBearer xyz"})
        assert r.status_code in (401, 403)

    def test_empty_bearer_token(self, client):
        r = client.get("/api/v1/customers/me",
                       headers={"Authorization": "Bearer "})
        assert r.status_code in (401, 403)


# ─────────────────────────────────────────────────────────────────────────────
# 16. ADMIN AUTH ROUTES
# ─────────────────────────────────────────────────────────────────────────────

class TestAdminAuth:

    def _create_admin(self) -> tuple[str, str]:
        from app.core.security import get_password_hash
        from app.models.admin import Admin
        db = SessionLocal()
        email = f"admin-{_uid()}@test.com"
        password = "AdminPass123!"
        admin = Admin(
            admin_id=f"ADM-{_uid()}",
            email=email,
            password_hash=get_password_hash(password),
        )
        db.add(admin)
        db.commit()
        db.close()
        return email, password

    def test_login_unknown_email(self, client):
        r = client.post("/api/v1/auth/admin/login",
                        json={"email": "nobody@admin.com", "password": "Pass123!"})
        assert r.status_code in (401, 404)

    def test_login_wrong_password(self, client):
        email, _ = self._create_admin()
        r = client.post("/api/v1/auth/admin/login",
                        json={"email": email, "password": "WrongPass!"})
        assert r.status_code == 401

    def test_login_valid_credentials(self, client):
        email, password = self._create_admin()
        fake_redis = _make_fake_redis()
        with patch("app.services.auth_service._get_redis", return_value=fake_redis):
            r = client.post("/api/v1/auth/admin/login",
                            json={"email": email, "password": password})
        assert r.status_code in (200, 503)

    def test_verify_otp_wrong_code(self, client):
        email, password = self._create_admin()
        fake_redis = _make_fake_redis()
        with patch("app.services.auth_service._get_redis", return_value=fake_redis):
            client.post("/api/v1/auth/admin/login",
                        json={"email": email, "password": password})
            r = client.post("/api/v1/auth/admin/login/verify-otp",
                            json={"email": email, "otp": "000000"})
        assert r.status_code in (400, 503)

    def test_reset_password_invalid_token(self, client):
        r = client.post("/api/v1/auth/admin/password/reset",
                        json={"reset_token": "bad", "new_password": "NewAdmin123!"})
        assert r.status_code == 400

    def test_forgot_password_unknown_email(self, client):
        fake_redis = _make_fake_redis()
        with patch("app.services.auth_service._get_redis", return_value=fake_redis):
            r = client.post("/api/v1/auth/admin/password/forgot",
                            json={"email": "nobody@admin.com"})
        assert r.status_code in (200, 404)

    def test_admin_token_refresh_success(self, client):
        from app.models.admin import Admin
        db = SessionLocal()
        try:
            admin = Admin(
                admin_id=f"ADM-{_uid()}",
                email=f"admin-refresh-{_uid()}@test.com",
                password_hash="hash",
                staff_role="staff",
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            token = create_refresh_token({"sub": admin.admin_id, "role": "ADMIN"})
        finally:
            db.close()
        r = client.post("/api/v1/auth/admin/token/refresh", json={"refreshToken": token})
        assert r.status_code == 200
        body = r.json()
        assert "accessToken" in body
        assert "refreshToken" in body
        assert body["user"]["userId"] == admin.admin_id

    def test_admin_token_refresh_invalid_token(self, client):
        r = client.post("/api/v1/auth/admin/token/refresh", json={"refreshToken": "bad-token"})
        assert r.status_code == 401

    def test_admin_token_refresh_access_token_rejected(self, client):
        token = create_access_token({"sub": "ADM-bad", "type": "admin", "role": "staff"})
        r = client.post("/api/v1/auth/admin/token/refresh", json={"refreshToken": token})
        assert r.status_code == 401

    def test_admin_token_refresh_wrong_role_rejected(self, client):
        token = create_refresh_token({"sub": "ADM-bad", "role": "CUSTOMER"})
        r = client.post("/api/v1/auth/admin/token/refresh", json={"refreshToken": token})
        assert r.status_code == 401

    def test_admin_token_refresh_unknown_admin_rejected(self, client):
        token = create_refresh_token({"sub": "ADM-UNKNOWN", "role": "ADMIN"})
        r = client.post("/api/v1/auth/admin/token/refresh", json={"refreshToken": token})
        assert r.status_code == 401

    def test_admin_logout_success(self, client):
        from app.models.admin import Admin
        email, _ = self._create_admin()
        db = SessionLocal()
        try:
            admin = db.query(Admin).filter(Admin.email == email).first()
            assert admin is not None
            access = create_access_token({"sub": admin.admin_id, "type": "admin", "role": "staff"})
        finally:
            db.close()
        r = client.post("/api/v1/auth/admin/logout", headers={"Authorization": f"Bearer {access}"})
        assert r.status_code == 200
        assert "message" in r.json()

    def test_admin_logout_blacklisted_token_rejected_on_reuse(self, client):
        from app.models.admin import Admin
        email, _ = self._create_admin()
        db = SessionLocal()
        try:
            admin = db.query(Admin).filter(Admin.email == email).first()
            assert admin is not None
            access = create_access_token({"sub": admin.admin_id, "type": "admin", "role": "staff"})
        finally:
            db.close()

        fake_redis = _make_fake_redis()
        with patch("app.services.admin_service._get_redis", return_value=fake_redis), \
             patch("app.core.security.is_token_blacklisted",
                   side_effect=lambda t: bool(fake_redis.exists(f"blacklist:{t}"))):
            first = client.post("/api/v1/auth/admin/logout", headers={"Authorization": f"Bearer {access}"})
            second = client.post("/api/v1/auth/admin/logout", headers={"Authorization": f"Bearer {access}"})
        assert first.status_code == 200
        assert second.status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
# 17. SECURITY HARDENING
# ─────────────────────────────────────────────────────────────────────────────

class TestSecurityHardening:

    def test_sql_injection_in_email(self, client):
        r = client.post("/api/v1/auth/customer/register", json={
            "fullName": "Hacker",
            "email": "' OR 1=1; --@test.com",
            "password": "Pass12345!",
        })
        assert r.status_code == 422

    def test_very_long_email_rejected(self, client):
        r = client.post("/api/v1/auth/customer/register", json={
            "fullName": "Test",
            "email": "a" * 300 + "@test.com",
            "password": "Pass12345!",
        })
        assert r.status_code == 422

    def test_unicode_name_accepted(self, client):
        r = client.post("/api/v1/auth/customer/register", json={
            "fullName": "සිංහල නම",
            "email": _customer_email(),
            "password": "Pass12345!",
        })
        assert r.status_code == 201

    def test_tampered_token_rejected(self, client, monkeypatch):
        monkeypatch.setenv("SKIP_EMAIL_VERIFICATION", "true")
        email = _customer_email()
        _register_customer(client, email)
        _activate_customer(email)
        real_token = _login_customer(client, email).json()["accessToken"]
        tampered = real_token[:-1] + ("A" if real_token[-1] != "A" else "B")
        r = client.get("/api/v1/customers/me",
                       headers={"Authorization": f"Bearer {tampered}"})
        assert r.status_code == 401

    def test_forgot_password_invalid_email_format(self, client):
        r = client.post("/api/v1/auth/customer/password/forgot",
                        json={"email": "not-an-email"})
        assert r.status_code == 422

    def test_customer_refresh_rejected_on_vendor_endpoint(self, client, monkeypatch):
        monkeypatch.setenv("SKIP_EMAIL_VERIFICATION", "true")
        email = _customer_email()
        _register_customer(client, email)
        _activate_customer(email)
        customer_refresh = _login_customer(client, email).json()["refreshToken"]
        r = client.post("/api/v1/auth/vendor/token/refresh",
                        json={"refreshToken": customer_refresh})
        assert r.status_code == 401


class TestCustomerPasswordChange:

    def test_change_password_success(self, client, monkeypatch):
        monkeypatch.setenv("SKIP_EMAIL_VERIFICATION", "true")
        email = _customer_email()
        _register_customer(client, email)
        _activate_customer(email)
        token = _login_customer(client, email, "Pass12345!").json()["accessToken"]
        r = client.post(
            "/api/v1/auth/customer/password/change",
            json={"current_password": "Pass12345!", "new_password": "Pass54321!"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        assert _login_customer(client, email, "Pass12345!").status_code == 401
        assert _login_customer(client, email, "Pass54321!").status_code == 200

    def test_change_password_wrong_current_password(self, client, monkeypatch):
        monkeypatch.setenv("SKIP_EMAIL_VERIFICATION", "true")
        email = _customer_email()
        _register_customer(client, email)
        _activate_customer(email)
        token = _login_customer(client, email, "Pass12345!").json()["accessToken"]
        r = client.post(
            "/api/v1/auth/customer/password/change",
            json={"current_password": "WrongPass123!", "new_password": "Pass54321!"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 400


class TestVendorPasswordChange:

    def test_change_password_success(self, client, monkeypatch):
        monkeypatch.setenv("SKIP_EMAIL_VERIFICATION", "true")
        email = _vendor_email()
        _register_vendor(client, email)
        _activate_vendor(email)
        token = _login_vendor(client, email, "Pass123!").json()["accessToken"]
        r = client.post(
            "/api/v1/auth/vendor/password/change",
            json={"current_password": "Pass123!", "new_password": "VendPass123!"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        assert _login_vendor(client, email, "Pass123!").status_code == 401
        assert _login_vendor(client, email, "VendPass123!").status_code == 200

    def test_change_password_wrong_current_password(self, client, monkeypatch):
        monkeypatch.setenv("SKIP_EMAIL_VERIFICATION", "true")
        email = _vendor_email()
        _register_vendor(client, email)
        _activate_vendor(email)
        token = _login_vendor(client, email, "Pass123!").json()["accessToken"]
        r = client.post(
            "/api/v1/auth/vendor/password/change",
            json={"current_password": "WrongPass123!", "new_password": "VendPass123!"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 400
