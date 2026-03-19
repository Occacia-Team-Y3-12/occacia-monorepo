"""
tests/Integration/test_auth_login_normalisation.py

Verifies that the login endpoints accept the email address placed in the
OAuth2PasswordRequestForm 'username' field — the normalisation fix made to
auth_router.py so that the username field is always treated as an email.
"""
from uuid import uuid4

from app.core.database import SessionLocal
from app.models.customer import Customer
from app.models.vendor import Vendor


def _activate_customer(email: str) -> None:
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.email == email).first()
        assert customer is not None
        customer.email_verified = True
        customer.status = "ACTIVE"
        db.commit()
    finally:
        db.close()


def _activate_vendor(email: str) -> None:
    db = SessionLocal()
    try:
        vendor = db.query(Vendor).filter(Vendor.email == email).first()
        assert vendor is not None
        vendor.email_verified = True
        vendor.status = "ACTIVE"
        db.commit()
    finally:
        db.close()


class TestCustomerLoginEmailNormalisation:

    def test_login_with_email_in_username_field_succeeds(self, client, monkeypatch):
        """Standard flow: email goes into the 'username' form field."""
        email = f"login-norm-{uuid4().hex[:8]}@test.com"
        monkeypatch.setenv("SKIP_EMAIL_VERIFICATION", "true")
        client.post("/api/v1/auth/customer/register", json={
            "full_name": "Norm Test", "email": email, "password": "Pass1234!",
        })
        _activate_customer(email)

        r = client.post(
            "/api/v1/auth/customer/login",
            data={"username": email, "password": "Pass1234!"},
        )
        assert r.status_code == 200
        body = r.json()
        assert "accessToken" in body or "access_token" in body

    def test_login_with_empty_username_returns_error(self, client):
        """Empty username field should not crash — returns 401 or 422."""
        r = client.post(
            "/api/v1/auth/customer/login",
            data={"username": "", "password": "Pass1234!"},
        )
        assert r.status_code in (401, 422)

    def test_login_wrong_password_returns_401(self, client, monkeypatch):
        email = f"wrongpw-{uuid4().hex[:8]}@test.com"
        monkeypatch.setenv("SKIP_EMAIL_VERIFICATION", "true")
        client.post("/api/v1/auth/customer/register", json={
            "full_name": "Wrong PW", "email": email, "password": "Correct1!",
        })
        _activate_customer(email)

        r = client.post(
            "/api/v1/auth/customer/login",
            data={"username": email, "password": "WrongPassword!"},
        )
        assert r.status_code == 401

    def test_login_nonexistent_email_returns_401(self, client):
        r = client.post(
            "/api/v1/auth/customer/login",
            data={"username": "nobody@nowhere.com", "password": "Pass1234!"},
        )
        assert r.status_code == 401

    def test_login_returns_access_and_refresh_tokens(self, client, monkeypatch):
        email = f"tokens-{uuid4().hex[:8]}@test.com"
        monkeypatch.setenv("SKIP_EMAIL_VERIFICATION", "true")
        client.post("/api/v1/auth/customer/register", json={
            "full_name": "Token Test", "email": email, "password": "Pass1234!",
        })
        _activate_customer(email)

        r = client.post(
            "/api/v1/auth/customer/login",
            data={"username": email, "password": "Pass1234!"},
        )
        assert r.status_code == 200
        body = r.json()
        # accept either casing convention
        has_access  = "accessToken"  in body or "access_token"  in body
        has_refresh = "refreshToken" in body or "refresh_token" in body
        assert has_access,  f"accessToken missing from response: {body}"
        assert has_refresh, f"refreshToken missing from response: {body}"

    def test_login_response_includes_user_email(self, client, monkeypatch):
        email = f"useremail-{uuid4().hex[:8]}@test.com"
        monkeypatch.setenv("SKIP_EMAIL_VERIFICATION", "true")
        client.post("/api/v1/auth/customer/register", json={
            "full_name": "Email Check", "email": email, "password": "Pass1234!",
        })
        _activate_customer(email)

        r = client.post(
            "/api/v1/auth/customer/login",
            data={"username": email, "password": "Pass1234!"},
        )
        assert r.status_code == 200
        body = r.json()
        user_block = body.get("user") or {}
        assert user_block.get("email") == email


class TestVendorLoginEmailNormalisation:

    def test_vendor_login_with_email_in_username_field_succeeds(self, client, monkeypatch):
        email = f"vendor-norm-{uuid4().hex[:8]}@test.com"
        monkeypatch.setenv("SKIP_EMAIL_VERIFICATION", "true")
        client.post("/api/v1/auth/vendor/register", json={
            "business_name": f"Biz {uuid4().hex[:6]}",
            "email": email,
            "password": "Pass1234!",
        })
        _activate_vendor(email)

        r = client.post(
            "/api/v1/auth/vendor/login",
            data={"username": email, "password": "Pass1234!"},
        )
        assert r.status_code == 200
        body = r.json()
        assert "access_token" in body or "accessToken" in body

    def test_vendor_login_wrong_password_returns_401(self, client, monkeypatch):
        email = f"vendor-wrongpw-{uuid4().hex[:8]}@test.com"
        monkeypatch.setenv("SKIP_EMAIL_VERIFICATION", "true")
        client.post("/api/v1/auth/vendor/register", json={
            "business_name": f"Biz {uuid4().hex[:6]}",
            "email": email,
            "password": "CorrectPass1!",
        })
        _activate_vendor(email)

        r = client.post(
            "/api/v1/auth/vendor/login",
            data={"username": email, "password": "WrongPass!"},
        )
        assert r.status_code == 401

    def test_vendor_login_empty_username_returns_error(self, client):
        r = client.post(
            "/api/v1/auth/vendor/login",
            data={"username": "", "password": "Pass1234!"},
        )
        assert r.status_code in (401, 422)
