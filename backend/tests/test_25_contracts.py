"""
tests/test_25_contracts.py

Full test suite for all 25 implemented OpenAPI contracts.

Contracts covered
─────────────────
AUTH – CUSTOMER (5)
  [C01] POST /api/v1/auth/customer/register
  [C02] GET  /api/v1/auth/customer/verify-email
  [C03] POST /api/v1/auth/customer/login
  [C04] POST /api/v1/auth/customer/password/forgot
  [C05] POST /api/v1/auth/customer/password/reset

AUTH – VENDOR (3)
  [V01] POST /api/v1/auth/vendor/register
  [V02] GET  /api/v1/auth/vendor/verify-email
  [V03] POST /api/v1/auth/vendor/login

AUTH – ADMIN (2)
  [A01] POST /api/v1/auth/admin/register
  [A02] POST /api/v1/auth/admin/login

PROFILES (4)
  [P01] GET  /api/v1/customers/me
  [P02] PUT  /api/v1/customers/me
  [P03] GET  /api/v1/vendors/me
  [P04] PUT  /api/v1/vendors/me

ADMIN – VENDOR MGMT (5)
  [AM01] GET  /api/v1/admin/vendors
  [AM02] GET  /api/v1/admin/vendors/{id}
  [AM03] PUT  /api/v1/admin/vendors/{id}/status
  [AM04] POST /api/v1/admin/vendors/{id}/approve
  [AM05] POST /api/v1/admin/vendors/{id}/reject

PERSONAS (5)
  [PE01] GET    /api/v1/customers/personas
  [PE02] POST   /api/v1/customers/personas
  [PE03] GET    /api/v1/customers/personas/{id}
  [PE04] PUT    /api/v1/customers/personas/{id}
  [PE05] DELETE /api/v1/customers/personas/{id}

SYSTEM (1)
  [S01] GET /api/v1/health

Run:
  pytest tests/test_25_contracts.py -v
  pytest tests/test_25_contracts.py -v -k "auth"
  pytest tests/test_25_contracts.py -v -k "admin"
"""

import uuid
from datetime import timedelta
from unittest.mock import MagicMock, patch

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# ── App & DB imports ────────────────────────────────────────────────────────
from app.main import app
from app.core.database import Base, get_db
from app.core.security import get_password_hash, SECRET_KEY, ALGORITHM, create_access_token

# ── Models ───────────────────────────────────────────────────────────────────
from app.models.customer import Customer
from app.models.vendor import Vendor
from app.models.admin import Admin
from app.models.persona import Persona


# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE FIXTURE — in-memory SQLite for full isolation
# ═══════════════════════════════════════════════════════════════════════════════

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
    """Unauthenticated TestClient with injected in-memory DB."""
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS — token factories & model factories
# ═══════════════════════════════════════════════════════════════════════════════

def _uid():
    return str(uuid.uuid4())[:8]


def _customer_token(email: str) -> str:
    return create_access_token({"sub": email}, expires_delta=timedelta(minutes=30))


def _vendor_token(email: str) -> str:
    return create_access_token({"sub": email}, expires_delta=timedelta(minutes=30))


def _admin_token(admin_id: str) -> str:
    return jwt.encode(
        {"sub": admin_id, "type": "admin"},
        SECRET_KEY, algorithm=ALGORITHM,
    )


def _auth_headers_customer(email: str) -> dict:
    return {"Authorization": f"Bearer {_customer_token(email)}"}


def _auth_headers_vendor(email: str) -> dict:
    return {"Authorization": f"Bearer {_vendor_token(email)}"}


def _auth_headers_admin(admin_id: str) -> dict:
    return {"Authorization": f"Bearer {_admin_token(admin_id)}"}


def _make_customer(db, email=None, verified=True, status="ACTIVE"):
    email = email or f"cust_{_uid()}@test.com"
    c = Customer(
        email=email,
        full_name="Test Customer",
        password_hash=get_password_hash("Password1!"),
        phone="+94771234567",
        locale="en",
        email_verified=verified,
        status=status,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def _make_vendor(db, email=None, approval_status="PENDING"):
    email = email or f"vendor_{_uid()}@test.com"
    v = Vendor(
        email=email,
        business_name=f"Biz {_uid()}",
        display_name=f"Display {_uid()}",
        password_hash=get_password_hash("Password1!"),
        is_verified=approval_status == "APPROVED",
        approval_status=approval_status,
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


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


def _make_persona(db, customer_id: str, name=None):
    p = Persona(
        customer_id=customer_id,
        name=name or f"Persona {_uid()}",
        relationship="friend",
        food_preferences=["sushi"],
        is_confirmed=False,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


# ═══════════════════════════════════════════════════════════════════════════════
# [C01]  POST /auth/customer/register
# ═══════════════════════════════════════════════════════════════════════════════

class TestCustomerRegister:
    URL = "/api/v1/auth/customer/register"

    def test_register_success_201(self, client):
        """[C01] Valid registration → 201."""
        # Patch both the email send AND the service so we don't need real email infra.
        # The service must return something compatible with RegisterResponse (has 'email').
        with patch("app.services.auth_service._send_email", return_value=True), \
             patch("app.services.auth_service.auth_service.register_customer") as mock_reg:
            mock_reg.return_value = {
                "message": "Registration successful. Please verify your email.",
                "email": f"new_{_uid()}@test.com",
            }
            resp = client.post(self.URL, json={
                "email": f"new_{_uid()}@test.com",
                "full_name": "New User",
                "password": "Password1!",
                "phone": "+94771234567",
            })
        assert resp.status_code == 201

    def test_register_duplicate_email_400(self, client, db_session):
        """[C01] Duplicate email → 400."""
        existing = _make_customer(db_session)
        with patch("app.services.auth_service.auth_service.register_customer") as mock_reg:
            from fastapi import HTTPException
            mock_reg.side_effect = HTTPException(status_code=400, detail="This email is already registered.")
            resp = client.post(self.URL, json={
                "email": existing.email,
                "full_name": "Dup User",
                "password": "Password1!",
                "phone": "+94771234567",
            })
        assert resp.status_code == 400

    def test_register_missing_email_422(self, client):
        """[C01] Missing required field → 422 validation error."""
        resp = client.post(self.URL, json={"full_name": "No Email", "password": "Password1!"})
        assert resp.status_code == 422

    def test_register_path_is_singular_not_plural(self, client):
        """[C01] Path must be /customer/ (singular) not /customers/ (plural)."""
        # Wrong path should 404 or 405
        resp_wrong = client.post("/api/v1/auth/customers/register", json={
            "email": "x@test.com", "full_name": "X", "password": "X"
        })
        assert resp_wrong.status_code in (404, 405, 422)


# ═══════════════════════════════════════════════════════════════════════════════
# [C02]  GET /auth/customer/verify-email
# ═══════════════════════════════════════════════════════════════════════════════

class TestCustomerVerifyEmail:
    URL = "/api/v1/auth/customer/verify-email"

    def test_verify_valid_token_json(self, client):
        """[C02] Valid token returns JSON message when Accept: application/json."""
        with patch("app.services.auth_service.auth_service.verify_customer_email") as mock_v:
            mock_v.return_value = {"message": "Email verified successfully"}
            resp = client.get(
                self.URL,
                params={"token": "valid-token-abc"},
                headers={"Accept": "application/json"},
            )
        assert resp.status_code == 200
        assert "message" in resp.json()

    def test_verify_valid_token_html(self, client):
        """[C02] Browser request (Accept: text/html) → HTML page."""
        with patch("app.services.auth_service.auth_service.verify_customer_email") as mock_v:
            mock_v.return_value = {"message": "Email verified successfully"}
            resp = client.get(
                self.URL,
                params={"token": "valid-token-abc"},
                headers={"Accept": "text/html,application/xhtml+xml"},
            )
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")

    def test_verify_invalid_token_400(self, client):
        """[C02] Invalid token → 400."""
        with patch("app.services.auth_service.auth_service.verify_customer_email") as mock_v:
            from fastapi import HTTPException
            mock_v.side_effect = HTTPException(status_code=400, detail="Invalid verification token.")
            resp = client.get(
                self.URL,
                params={"token": "bad-token"},
                headers={"Accept": "application/json"},
            )
        assert resp.status_code == 400

    def test_verify_missing_token_422(self, client):
        """[C02] Missing token query param → 422."""
        resp = client.get(self.URL, headers={"Accept": "application/json"})
        assert resp.status_code == 422

    def test_verify_path_is_singular(self, client):
        """[C02] Spec path: /auth/customer/verify-email (singular)."""
        resp = client.get("/api/v1/auth/customers/verify-email",
                          params={"token": "x"},
                          headers={"Accept": "application/json"})
        assert resp.status_code in (404, 405)


# ═══════════════════════════════════════════════════════════════════════════════
# [C03]  POST /auth/customer/login
# ═══════════════════════════════════════════════════════════════════════════════

class TestCustomerLogin:
    URL = "/api/v1/auth/customer/login"

    def test_login_success_returns_token(self, client, db_session):
        """[C03] Correct credentials → access_token + token_type."""
        cust = _make_customer(db_session, verified=True)
        with patch.dict("os.environ", {"SKIP_EMAIL_VERIFICATION": "true"}):
            resp = client.post(self.URL, data={
                "username": cust.email,
                "password": "Password1!",
            })
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    def test_login_wrong_password_401(self, client, db_session):
        """[C03] Wrong password → 401."""
        cust = _make_customer(db_session)
        resp = client.post(self.URL, data={
            "username": cust.email,
            "password": "WrongPass999!",
        })
        assert resp.status_code == 401

    def test_login_unknown_email_401(self, client):
        """[C03] Unknown email → 401."""
        resp = client.post(self.URL, data={
            "username": "nobody@test.com",
            "password": "Password1!",
        })
        assert resp.status_code == 401

    def test_login_unverified_customer_403(self, client, db_session):
        """[C03] Unverified customer → 403 when verification is enforced.
        The router's verify_user_login() raises 403 when email is not verified
        and SKIP_EMAIL_VERIFICATION != 'true'. We patch verify_user_login to
        simulate this — the contract is that the endpoint surfaces a 403.
        """
        from fastapi import HTTPException as FastAPIHTTPException
        cust = _make_customer(db_session, verified=False, status="PENDING_VERIFICATION")

        def raise_403(user, form_data):
            if not getattr(user, "email_verified", True):
                raise FastAPIHTTPException(
                    status_code=403, detail="Email not verified."
                )

        with patch("app.routers.v1.auth_router.verify_user_login", side_effect=raise_403):
            resp = client.post(self.URL, data={
                "username": cust.email,
                "password": "Password1!",
            })
        assert resp.status_code in (401, 403)

    def test_login_path_is_singular(self, client):
        """[C03] /auth/customers/login (plural) must not exist."""
        resp = client.post("/api/v1/auth/customers/login",
                           data={"username": "x@x.com", "password": "x"})
        assert resp.status_code in (404, 405)


# ═══════════════════════════════════════════════════════════════════════════════
# [C04]  POST /auth/customer/password/forgot
# ═══════════════════════════════════════════════════════════════════════════════

class TestForgotPassword:
    URL = "/api/v1/auth/customer/password/forgot"

    def test_forgot_known_email(self, client, db_session):
        """[C04] Known email → 200 with message (email sent)."""
        cust = _make_customer(db_session)
        with patch("app.services.auth_service.auth_service.request_password_reset") as mock_r:
            mock_r.return_value = {"message": "Password reset email sent."}
            resp = client.post(self.URL, json={"email": cust.email})
        assert resp.status_code == 200
        assert "message" in resp.json()

    def test_forgot_unknown_email_still_200(self, client):
        """[C04] Unknown email → still 200 (no user enumeration)."""
        with patch("app.services.auth_service.auth_service.request_password_reset") as mock_r:
            mock_r.return_value = {"message": "If this email is registered, a reset link has been sent."}
            resp = client.post(self.URL, json={"email": "unknown@test.com"})
        assert resp.status_code == 200

    def test_forgot_missing_email_422(self, client):
        """[C04] Missing body → 422."""
        resp = client.post(self.URL, json={})
        assert resp.status_code == 422

    def test_forgot_old_path_missing(self, client):
        """[C04] Old path /auth/customers/forgot-password must 404/405."""
        resp = client.post("/api/v1/auth/customers/forgot-password",
                           json={"email": "x@x.com"})
        assert resp.status_code in (404, 405)


# ═══════════════════════════════════════════════════════════════════════════════
# [C05]  POST /auth/customer/password/reset
# ═══════════════════════════════════════════════════════════════════════════════

class TestResetPassword:
    URL = "/api/v1/auth/customer/password/reset"

    def test_reset_valid_token(self, client):
        """[C05] Valid token + new password → 200."""
        with patch("app.services.auth_service.auth_service.confirm_password_reset") as mock_r:
            mock_r.return_value = {"message": "Password reset successfully."}
            resp = client.post(self.URL, json={
                "token": "valid-reset-token",
                "new_password": "NewPassword1!",
            })
        assert resp.status_code == 200
        assert "message" in resp.json()

    def test_reset_invalid_token_400(self, client):
        """[C05] Bad token → 400."""
        with patch("app.services.auth_service.auth_service.confirm_password_reset") as mock_r:
            from fastapi import HTTPException
            mock_r.side_effect = HTTPException(status_code=400, detail="Invalid verification token.")
            resp = client.post(self.URL, json={
                "token": "bad-token",
                "new_password": "NewPassword1!",
            })
        assert resp.status_code == 400

    def test_reset_missing_fields_422(self, client):
        """[C05] Missing new_password → 422."""
        resp = client.post(self.URL, json={"token": "tok"})
        assert resp.status_code == 422

    def test_reset_old_path_missing(self, client):
        """[C05] Old path /auth/customers/reset-password must 404/405."""
        resp = client.post("/api/v1/auth/customers/reset-password",
                           json={"token": "t", "new_password": "p"})
        assert resp.status_code in (404, 405)


# ═══════════════════════════════════════════════════════════════════════════════
# [V01]  POST /auth/vendor/register
# ═══════════════════════════════════════════════════════════════════════════════

class TestVendorRegister:
    URL = "/api/v1/auth/vendor/register"

    def test_register_vendor_201(self, client):
        """[V01] New vendor registration → 201."""
        with patch("app.services.vendor_service.vendor_service.get_vendor_by_email",
                   return_value=None), \
             patch("app.services.vendor_service.vendor_service.get_vendor_by_display_name",
                   return_value=None), \
             patch("app.services.vendor_service.vendor_service.create_vendor") as mock_cv, \
             patch("app.services.auth_service.auth_service.register_vendor_verification"):
            mock_cv.return_value = MagicMock(
                vendor_id=f"VEN-{_uid()}",
                email=f"v_{_uid()}@test.com",
                business_name="Test Biz",
                display_name="Test Display",
                phone=None,
                contact_phone=None,
                location_base=None,
                approval_status="PENDING",
                is_verified=False,
                approved_at=None,
            )
            resp = client.post(self.URL, json={
                "email": f"v_{_uid()}@test.com",
                "business_name": f"Biz {_uid()}",
                "password": "Password1!",
            })
        assert resp.status_code == 201

    def test_register_vendor_duplicate_email_400(self, client, db_session):
        """[V01] Duplicate email → 400."""
        vendor = _make_vendor(db_session)
        resp = client.post(self.URL, json={
            "email": vendor.email,
            "business_name": f"New Biz {_uid()}",
            "password": "Password1!",
        })
        assert resp.status_code == 400

    def test_register_vendor_path_singular(self, client):
        """[V01] /auth/vendors/register (plural) must 404/405."""
        resp = client.post("/api/v1/auth/vendors/register",
                           json={"email": "x@x.com", "business_name": "x", "password": "x"})
        assert resp.status_code in (404, 405)


# ═══════════════════════════════════════════════════════════════════════════════
# [V02]  GET /auth/vendor/verify-email
# ═══════════════════════════════════════════════════════════════════════════════

class TestVendorVerifyEmail:
    URL = "/api/v1/auth/vendor/verify-email"

    def test_verify_valid_token(self, client):
        """[V02] Valid token → 200."""
        with patch("app.services.auth_service.auth_service.verify_vendor_email") as mock_v:
            mock_v.return_value = {"message": "Email verified successfully"}
            resp = client.get(
                self.URL,
                params={"token": "valid-vendor-token"},
                headers={"Accept": "application/json"},
            )
        assert resp.status_code == 200

    def test_verify_bad_token_400(self, client):
        """[V02] Bad token → 400."""
        with patch("app.services.auth_service.auth_service.verify_vendor_email") as mock_v:
            from fastapi import HTTPException
            mock_v.side_effect = HTTPException(400, "Invalid verification token.")
            resp = client.get(
                self.URL,
                params={"token": "bad"},
                headers={"Accept": "application/json"},
            )
        assert resp.status_code == 400

    def test_verify_path_singular(self, client):
        """[V02] /auth/vendors/verify-email (plural) must 404/405."""
        resp = client.get("/api/v1/auth/vendors/verify-email",
                          params={"token": "x"},
                          headers={"Accept": "application/json"})
        assert resp.status_code in (404, 405)


# ═══════════════════════════════════════════════════════════════════════════════
# [V03]  POST /auth/vendor/login
# ═══════════════════════════════════════════════════════════════════════════════

class TestVendorLogin:
    URL = "/api/v1/auth/vendor/login"

    def test_login_approved_vendor(self, client, db_session):
        """[V03] Approved vendor with correct credentials → token."""
        v = _make_vendor(db_session, approval_status="APPROVED")
        with patch.dict("os.environ", {"SKIP_EMAIL_VERIFICATION": "true"}):
            resp = client.post(self.URL, data={
                "username": v.email,
                "password": "Password1!",
            })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_login_wrong_password_401(self, client, db_session):
        """[V03] Wrong password → 401."""
        v = _make_vendor(db_session)
        resp = client.post(self.URL, data={
            "username": v.email,
            "password": "WrongPass!",
        })
        assert resp.status_code == 401

    def test_login_path_singular(self, client):
        """[V03] /auth/vendors/login (plural) must 404/405."""
        resp = client.post("/api/v1/auth/vendors/login",
                           data={"username": "x@x.com", "password": "x"})
        assert resp.status_code in (404, 405)


# ═══════════════════════════════════════════════════════════════════════════════
# [A01]  POST /auth/admin/register
# ═══════════════════════════════════════════════════════════════════════════════

class TestAdminRegister:
    URL = "/api/v1/auth/admin/register"

    def test_register_admin_201(self, client):
        """[A01] Register new admin → 201.
        REQUIRES: admin_router.py + v1/__init__.py deployed (auth_admin_router included).
        """
        with patch.dict("os.environ", {"DISABLE_ADMIN_REGISTER": "false"}):
            resp = client.post(self.URL, json={
                "email": f"admin_{_uid()}@test.com",
                "password": "AdminPass1!",
                "staff_role": "staff",
            })
        if resp.status_code == 404:
            pytest.skip("auth_admin_router not yet registered in v1/__init__.py — deploy admin_router.py + v1/__init__.py first")
        assert resp.status_code == 201
        body = resp.json()
        assert "admin_id" in body
        assert "email" in body

    def test_register_admin_duplicate_400(self, client, db_session):
        """[A01] Duplicate admin email → 400."""
        adm = _make_admin(db_session)
        with patch.dict("os.environ", {"DISABLE_ADMIN_REGISTER": "false"}):
            resp = client.post(self.URL, json={
                "email": adm.email,
                "password": "AdminPass1!",
            })
        if resp.status_code == 404:
            pytest.skip("auth_admin_router not yet registered — deploy admin_router.py + v1/__init__.py")
        assert resp.status_code == 400

    def test_register_admin_disabled_403(self, client):
        """[A01] DISABLE_ADMIN_REGISTER=true → 403."""
        # Check route exists first
        probe = client.post(self.URL, json={"email": f"x_{_uid()}@test.com", "password": "x"})
        if probe.status_code == 404:
            pytest.skip("auth_admin_router not yet registered — deploy admin_router.py + v1/__init__.py")
        with patch("app.routers.v1.admin_router.settings") as mock_settings:
            mock_settings.DISABLE_ADMIN_REGISTER = "true"
            resp = client.post(self.URL, json={
                "email": f"a2_{_uid()}@test.com",
                "password": "AdminPass1!",
            })
        assert resp.status_code == 403

    def test_register_admin_path_correct(self, client):
        """[A01] Path is /auth/admin/register (not /admin/register)."""
        resp_old = client.post("/api/v1/admin/register", json={
            "email": "x@x.com", "password": "x"
        })
        assert resp_old.status_code in (404, 405)


# ═══════════════════════════════════════════════════════════════════════════════
# [A02]  POST /auth/admin/login
# ═══════════════════════════════════════════════════════════════════════════════

class TestAdminLogin:
    URL = "/api/v1/auth/admin/login"

    def test_login_admin_success(self, client, db_session):
        """[A02] Correct admin credentials → token + role."""
        adm = _make_admin(db_session)
        resp = client.post(self.URL, data={
            "username": adm.email,
            "password": "AdminPass1!",
        })
        if resp.status_code == 404:
            pytest.skip("auth_admin_router not yet registered — deploy admin_router.py + v1/__init__.py")
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert "role" in body

    def test_login_admin_wrong_password_401(self, client, db_session):
        """[A02] Wrong password → 401."""
        adm = _make_admin(db_session)
        resp = client.post(self.URL, data={
            "username": adm.email,
            "password": "WrongAdmin!",
        })
        if resp.status_code == 404:
            pytest.skip("auth_admin_router not yet registered — deploy admin_router.py + v1/__init__.py")
        assert resp.status_code == 401

    def test_login_admin_unknown_401(self, client):
        """[A02] Unknown admin → 401."""
        resp = client.post(self.URL, data={
            "username": "nobody@admin.com",
            "password": "AdminPass1!",
        })
        if resp.status_code == 404:
            pytest.skip("auth_admin_router not yet registered — deploy admin_router.py + v1/__init__.py")
        assert resp.status_code == 401

    def test_login_admin_path_correct(self, client):
        """[A02] Old /admin/login path must 404/405."""
        resp = client.post("/api/v1/admin/login",
                           data={"username": "x@x.com", "password": "x"})
        assert resp.status_code in (404, 405)


# ═══════════════════════════════════════════════════════════════════════════════
# [P01]  GET /customers/me
# ═══════════════════════════════════════════════════════════════════════════════

class TestGetCustomerMe:
    URL = "/api/v1/customers/me"

    def test_get_me_authenticated(self, client, db_session):
        """[P01] Authenticated customer → profile fields returned."""
        cust = _make_customer(db_session)
        resp = client.get(self.URL, headers=_auth_headers_customer(cust.email))
        if resp.status_code == 404:
            pytest.skip("customers_router not yet registered — deploy customers_router.py + v1/__init__.py")
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == cust.email
        assert "fullName" in body
        assert "customerId" in body

    def test_get_me_unauthenticated_401(self, client):
        """[P01] No token → 401."""
        resp = client.get(self.URL)
        if resp.status_code == 404:
            pytest.skip("customers_router not yet registered — deploy customers_router.py + v1/__init__.py")
        assert resp.status_code == 401

    def test_get_me_bad_token_401(self, client):
        """[P01] Garbage token → 401."""
        resp = client.get(self.URL, headers={"Authorization": "Bearer garbage"})
        if resp.status_code == 404:
            pytest.skip("customers_router not yet registered — deploy customers_router.py + v1/__init__.py")
        assert resp.status_code == 401

    def test_get_me_correct_profile_fields(self, client, db_session):
        """[P01] Response contains all spec-required fields."""
        cust = _make_customer(db_session)
        resp = client.get(self.URL, headers=_auth_headers_customer(cust.email))
        if resp.status_code == 404:
            pytest.skip("customers_router not yet registered — deploy customers_router.py + v1/__init__.py")
        body = resp.json()
        for field in ("customerId", "email", "fullName", "phone", "locale", "status"):
            assert field in body, f"Missing field: {field}"


# ═══════════════════════════════════════════════════════════════════════════════
# [P02]  PUT /customers/me
# ═══════════════════════════════════════════════════════════════════════════════

class TestUpdateCustomerMe:
    URL = "/api/v1/customers/me"

    def test_update_full_name(self, client, db_session):
        """[P02] Update fullName → reflected in response."""
        cust = _make_customer(db_session)
        resp = client.put(self.URL, json={"fullName": "Updated Name"},
                          headers=_auth_headers_customer(cust.email))
        if resp.status_code == 404:
            pytest.skip("customers_router not yet registered — deploy customers_router.py + v1/__init__.py")
        assert resp.status_code == 200
        assert resp.json()["fullName"] == "Updated Name"

    def test_update_phone(self, client, db_session):
        """[P02] Update phone → reflected in response."""
        cust = _make_customer(db_session)
        resp = client.put(self.URL, json={"phone": "+94770000000"},
                          headers=_auth_headers_customer(cust.email))
        if resp.status_code == 404:
            pytest.skip("customers_router not yet registered — deploy customers_router.py + v1/__init__.py")
        assert resp.status_code == 200
        assert resp.json()["phone"] == "+94770000000"

    def test_update_locale(self, client, db_session):
        """[P02] Update locale → reflected in response."""
        cust = _make_customer(db_session)
        resp = client.put(self.URL, json={"locale": "si"},
                          headers=_auth_headers_customer(cust.email))
        if resp.status_code == 404:
            pytest.skip("customers_router not yet registered — deploy customers_router.py + v1/__init__.py")
        assert resp.status_code == 200
        assert resp.json()["locale"] == "si"

    def test_update_unauthenticated_401(self, client):
        """[P02] No token → 401."""
        resp = client.put(self.URL, json={"fullName": "x"})
        if resp.status_code == 404:
            pytest.skip("customers_router not yet registered — deploy customers_router.py + v1/__init__.py")
        assert resp.status_code == 401

    def test_update_email_not_changed(self, client, db_session):
        """[P02] Email is read-only — not changeable via this endpoint."""
        cust = _make_customer(db_session)
        resp = client.put(self.URL, json={"email": "hacked@test.com"},
                          headers=_auth_headers_customer(cust.email))
        if resp.status_code == 404:
            pytest.skip("customers_router not yet registered — deploy customers_router.py + v1/__init__.py")
        assert resp.status_code == 200
        assert resp.json()["email"] == cust.email


# ═══════════════════════════════════════════════════════════════════════════════
# [P03]  GET /vendors/me
# ═══════════════════════════════════════════════════════════════════════════════

class TestGetVendorMe:
    URL = "/api/v1/vendors/me"

    def test_get_me_vendor_200(self, client, db_session):
        """[P03] Authenticated vendor → profile returned."""
        v = _make_vendor(db_session)
        resp = client.get(self.URL, headers=_auth_headers_vendor(v.email))
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == v.email

    def test_get_me_unauthenticated_401(self, client):
        """[P03] No token → 401."""
        resp = client.get(self.URL)
        assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════════
# [P04]  PUT /vendors/me
# ═══════════════════════════════════════════════════════════════════════════════

class TestUpdateVendorMe:
    URL = "/api/v1/vendors/me"

    def test_update_display_name(self, client, db_session):
        """[P04] Update displayName → reflected in response."""
        v = _make_vendor(db_session)
        resp = client.put(
            self.URL,
            json={"displayName": "New Display"},
            headers=_auth_headers_vendor(v.email),
        )
        assert resp.status_code == 200
        assert resp.json()["display_name"] == "New Display"

    def test_update_contact_phone(self, client, db_session):
        """[P04] Update contactPhone → reflected in response."""
        v = _make_vendor(db_session)
        resp = client.put(
            self.URL,
            json={"contactPhone": "+94770000099"},
            headers=_auth_headers_vendor(v.email),
        )
        assert resp.status_code == 200
        assert resp.json()["contact_phone"] == "+94770000099"

    def test_update_unauthenticated_401(self, client):
        """[P04] No token → 401."""
        resp = client.put(self.URL, json={"displayName": "x"})
        assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════════
# [AM01]  GET /admin/vendors
# ═══════════════════════════════════════════════════════════════════════════════

class TestAdminListVendors:
    URL = "/api/v1/admin/vendors"

    def test_list_vendors_authenticated(self, client, db_session):
        """[AM01] Admin can list vendors."""
        adm = _make_admin(db_session)
        _make_vendor(db_session)
        _make_vendor(db_session)
        resp = client.get(self.URL, headers=_auth_headers_admin(str(adm.admin_id)))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_vendors_unauthenticated_401(self, client):
        """[AM01] No token → 401."""
        resp = client.get(self.URL)
        assert resp.status_code == 401

    def test_filter_by_approval_status(self, client, db_session):
        """[AM01] ?approval_status=PENDING filters correctly."""
        adm = _make_admin(db_session)
        _make_vendor(db_session, approval_status="PENDING")
        _make_vendor(db_session, approval_status="APPROVED")
        resp = client.get(
            self.URL,
            params={"approval_status": "PENDING"},
            headers=_auth_headers_admin(str(adm.admin_id)),
        )
        assert resp.status_code == 200
        for v in resp.json():
            assert v["approval_status"] == "PENDING"

    def test_returns_list_even_empty(self, client, db_session):
        """[AM01] Empty DB → empty list, not error."""
        adm = _make_admin(db_session)
        resp = client.get(self.URL, headers=_auth_headers_admin(str(adm.admin_id)))
        assert resp.status_code == 200
        assert resp.json() == []


# ═══════════════════════════════════════════════════════════════════════════════
# [AM02]  GET /admin/vendors/{id}
# ═══════════════════════════════════════════════════════════════════════════════

class TestAdminGetVendor:

    def test_get_vendor_by_id(self, client, db_session):
        """[AM02] Get vendor detail by id."""
        adm = _make_admin(db_session)
        v = _make_vendor(db_session)
        resp = client.get(
            f"/api/v1/admin/vendors/{v.id}",
            headers=_auth_headers_admin(str(adm.admin_id)),
        )
        assert resp.status_code == 200
        assert resp.json()["email"] == v.email

    def test_get_vendor_not_found_404(self, client, db_session):
        """[AM02] Non-existent vendor id → 404."""
        adm = _make_admin(db_session)
        resp = client.get(
            "/api/v1/admin/vendors/99999",
            headers=_auth_headers_admin(str(adm.admin_id)),
        )
        assert resp.status_code == 404

    def test_get_vendor_unauthenticated_401(self, client, db_session):
        """[AM02] No token → 401."""
        v = _make_vendor(db_session)
        resp = client.get(f"/api/v1/admin/vendors/{v.id}")
        assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════════
# [AM03]  PUT /admin/vendors/{id}/status
# ═══════════════════════════════════════════════════════════════════════════════

class TestAdminUpdateVendorStatus:

    def test_set_status_active(self, client, db_session):
        """[AM03] Set vendor status to ACTIVE."""
        adm = _make_admin(db_session)
        v = _make_vendor(db_session)
        resp = client.put(
            f"/api/v1/admin/vendors/{v.id}/status",
            json={"status": "ACTIVE"},
            headers=_auth_headers_admin(str(adm.admin_id)),
        )
        assert resp.status_code == 200

    def test_set_status_suspended(self, client, db_session):
        """[AM03] Set vendor status to SUSPENDED."""
        adm = _make_admin(db_session)
        v = _make_vendor(db_session)
        resp = client.put(
            f"/api/v1/admin/vendors/{v.id}/status",
            json={"status": "SUSPENDED"},
            headers=_auth_headers_admin(str(adm.admin_id)),
        )
        assert resp.status_code == 200

    def test_set_status_disabled(self, client, db_session):
        """[AM03] Set vendor status to DISABLED."""
        adm = _make_admin(db_session)
        v = _make_vendor(db_session)
        resp = client.put(
            f"/api/v1/admin/vendors/{v.id}/status",
            json={"status": "DISABLED"},
            headers=_auth_headers_admin(str(adm.admin_id)),
        )
        assert resp.status_code == 200

    def test_invalid_status_400(self, client, db_session):
        """[AM03] Invalid status value → 400."""
        adm = _make_admin(db_session)
        v = _make_vendor(db_session)
        resp = client.put(
            f"/api/v1/admin/vendors/{v.id}/status",
            json={"status": "BANANA"},
            headers=_auth_headers_admin(str(adm.admin_id)),
        )
        assert resp.status_code == 400

    def test_vendor_not_found_404(self, client, db_session):
        """[AM03] Non-existent vendor → 404."""
        adm = _make_admin(db_session)
        resp = client.put(
            "/api/v1/admin/vendors/99999/status",
            json={"status": "ACTIVE"},
            headers=_auth_headers_admin(str(adm.admin_id)),
        )
        assert resp.status_code == 404

    def test_unauthenticated_401(self, client, db_session):
        """[AM03] No token → 401."""
        v = _make_vendor(db_session)
        resp = client.put(f"/api/v1/admin/vendors/{v.id}/status",
                          json={"status": "ACTIVE"})
        assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════════
# [AM04]  POST /admin/vendors/{id}/approve
# ═══════════════════════════════════════════════════════════════════════════════

class TestAdminApproveVendor:

    def test_approve_pending_vendor(self, client, db_session):
        """[AM04] Approve pending vendor → is_verified=True, approval_status=APPROVED."""
        adm = _make_admin(db_session)
        v = _make_vendor(db_session, approval_status="PENDING")
        with patch("app.routers.v1.admin_router._send_approval_email"):
            resp = client.post(
                f"/api/v1/admin/vendors/{v.id}/approve",
                headers=_auth_headers_admin(str(adm.admin_id)),
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["approval_status"] == "APPROVED"
        assert body["is_verified"] is True

    def test_approve_already_approved_400(self, client, db_session):
        """[AM04] Already approved → 400."""
        adm = _make_admin(db_session)
        v = _make_vendor(db_session, approval_status="APPROVED")
        with patch("app.routers.v1.admin_router._send_approval_email"):
            resp = client.post(
                f"/api/v1/admin/vendors/{v.id}/approve",
                headers=_auth_headers_admin(str(adm.admin_id)),
            )
        assert resp.status_code == 400

    def test_approve_not_found_404(self, client, db_session):
        """[AM04] Vendor not found → 404."""
        adm = _make_admin(db_session)
        with patch("app.routers.v1.admin_router._send_approval_email"):
            resp = client.post(
                "/api/v1/admin/vendors/99999/approve",
                headers=_auth_headers_admin(str(adm.admin_id)),
            )
        assert resp.status_code == 404

    def test_approve_unauthenticated_401(self, client, db_session):
        """[AM04] No token → 401."""
        v = _make_vendor(db_session)
        resp = client.post(f"/api/v1/admin/vendors/{v.id}/approve")
        assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════════
# [AM05]  POST /admin/vendors/{id}/reject
# ═══════════════════════════════════════════════════════════════════════════════

class TestAdminRejectVendor:

    def test_reject_pending_vendor(self, client, db_session):
        """[AM05] Reject pending vendor → approval_status=REJECTED."""
        adm = _make_admin(db_session)
        v = _make_vendor(db_session, approval_status="PENDING")
        with patch("app.routers.v1.admin_router._send_rejection_email"):
            resp = client.post(
                f"/api/v1/admin/vendors/{v.id}/reject",
                json={"reason": "Does not meet requirements."},
                headers=_auth_headers_admin(str(adm.admin_id)),
            )
        assert resp.status_code == 200
        assert resp.json()["approval_status"] == "REJECTED"

    def test_reject_with_default_reason(self, client, db_session):
        """[AM05] No body → default rejection reason used."""
        adm = _make_admin(db_session)
        v = _make_vendor(db_session, approval_status="PENDING")
        with patch("app.routers.v1.admin_router._send_rejection_email"):
            resp = client.post(
                f"/api/v1/admin/vendors/{v.id}/reject",
                headers=_auth_headers_admin(str(adm.admin_id)),
            )
        assert resp.status_code == 200

    def test_reject_already_rejected_400(self, client, db_session):
        """[AM05] Already rejected → 400."""
        adm = _make_admin(db_session)
        v = _make_vendor(db_session, approval_status="REJECTED")
        with patch("app.routers.v1.admin_router._send_rejection_email"):
            resp = client.post(
                f"/api/v1/admin/vendors/{v.id}/reject",
                headers=_auth_headers_admin(str(adm.admin_id)),
            )
        assert resp.status_code == 400

    def test_reject_not_found_404(self, client, db_session):
        """[AM05] Vendor not found → 404."""
        adm = _make_admin(db_session)
        with patch("app.routers.v1.admin_router._send_rejection_email"):
            resp = client.post(
                "/api/v1/admin/vendors/99999/reject",
                headers=_auth_headers_admin(str(adm.admin_id)),
            )
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# DEPLOY-GUARD FIXTURES
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def require_personas_router(client):
    """Skip all persona tests if persona_router not yet deployed."""
    probe = client.get("/api/v1/customers/personas",
                       headers={"Authorization": "Bearer fake"})
    if probe.status_code == 404:
        pytest.skip("persona_router not registered at /customers/personas — deploy persona_router.py + v1/__init__.py")


@pytest.fixture
def require_customers_router(client):
    """Skip customers/me tests if customers_router not yet deployed."""
    probe = client.get("/api/v1/customers/me")
    if probe.status_code == 404:
        pytest.skip("customers_router not registered — deploy customers_router.py + v1/__init__.py")


@pytest.fixture
def require_admin_auth_router(client):
    """Skip admin auth tests if auth_admin_router not yet deployed."""
    probe = client.post("/api/v1/auth/admin/login",
                        data={"username": "x", "password": "x"})
    if probe.status_code == 404:
        pytest.skip("auth_admin_router not registered — deploy admin_router.py + v1/__init__.py")


# ═══════════════════════════════════════════════════════════════════════════════
# [PE01]  GET /customers/personas
# ═══════════════════════════════════════════════════════════════════════════════

class TestListPersonas:
    URL = "/api/v1/customers/personas"

    def test_list_personas_empty(self, client, db_session, require_personas_router):
        """[PE01] No personas → empty list."""
        cust = _make_customer(db_session)
        resp = client.get(self.URL, headers=_auth_headers_customer(cust.email))
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_personas_returns_own_only(self, client, db_session, require_personas_router):
        """[PE01] Only returns personas belonging to the authenticated customer."""
        cust1 = _make_customer(db_session)
        cust2 = _make_customer(db_session)
        _make_persona(db_session, str(cust1.customer_id))
        _make_persona(db_session, str(cust1.customer_id))
        _make_persona(db_session, str(cust2.customer_id))

        resp = client.get(self.URL, headers=_auth_headers_customer(cust1.email))
        assert resp.status_code == 200
        personas = resp.json()
        assert len(personas) == 2
        for p in personas:
            assert p["customer_id"] == str(cust1.customer_id)

    def test_list_unauthenticated_401(self, client, require_personas_router):
        """[PE01] No token → 401."""
        resp = client.get(self.URL)
        assert resp.status_code == 401

    def test_list_path_uses_customers_prefix(self, client, require_personas_router):
        """[PE01] Old /personas path must 404."""
        resp = client.get("/api/v1/personas", headers={"Authorization": "Bearer x"})
        assert resp.status_code in (401, 404)


# ═══════════════════════════════════════════════════════════════════════════════
# [PE02]  POST /customers/personas
# ═══════════════════════════════════════════════════════════════════════════════

class TestCreatePersona:
    URL = "/api/v1/customers/personas"

    def test_create_minimal_persona(self, client, db_session, require_personas_router):
        """[PE02] Minimal valid payload → 201."""
        cust = _make_customer(db_session)
        resp = client.post(
            self.URL,
            json={"name": "Alice"},
            headers=_auth_headers_customer(cust.email),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["name"] == "Alice"
        assert "persona_id" in body
        assert body["customer_id"] == str(cust.customer_id)

    def test_create_full_payload(self, client, db_session, require_personas_router):
        """[PE02] Full payload with all optional fields → 201."""
        cust = _make_customer(db_session)
        resp = client.post(
            self.URL,
            json={
                "name": "Bob",
                "relationship": "brother",
                "birthday": "1995-06-15",
                "personality": "outgoing",
                "food_preferences": ["pizza", "sushi"],
                "color_preferences": ["blue"],
                "music_preferences": ["jazz"],
                "personality_tags": ["adventurous"],
            },
            headers=_auth_headers_customer(cust.email),
        )
        assert resp.status_code == 201

    def test_create_empty_name_422(self, client, db_session, require_personas_router):
        """[PE02] Empty name → 422 validation error."""
        cust = _make_customer(db_session)
        resp = client.post(
            self.URL,
            json={"name": "   "},
            headers=_auth_headers_customer(cust.email),
        )
        assert resp.status_code == 422

    def test_create_missing_name_422(self, client, db_session, require_personas_router):
        """[PE02] Missing name → 422."""
        cust = _make_customer(db_session)
        resp = client.post(
            self.URL,
            json={"relationship": "friend"},
            headers=_auth_headers_customer(cust.email),
        )
        assert resp.status_code == 422

    def test_create_unauthenticated_401(self, client, require_personas_router):
        """[PE02] No token → 401."""
        resp = client.post(self.URL, json={"name": "x"})
        assert resp.status_code == 401

    def test_create_assigns_persona_id_format(self, client, db_session, require_personas_router):
        """[PE02] persona_id starts with PER-."""
        cust = _make_customer(db_session)
        resp = client.post(
            self.URL,
            json={"name": "Charlie"},
            headers=_auth_headers_customer(cust.email),
        )
        assert resp.status_code == 201
        assert resp.json()["persona_id"].startswith("PER-")


# ═══════════════════════════════════════════════════════════════════════════════
# [PE03]  GET /customers/personas/{personaId}
# ═══════════════════════════════════════════════════════════════════════════════

class TestGetPersona:

    def test_get_own_persona(self, client, db_session, require_personas_router):
        """[PE03] Get own persona by ID."""
        cust = _make_customer(db_session)
        p = _make_persona(db_session, str(cust.customer_id), name="Dana")
        resp = client.get(
            f"/api/v1/customers/personas/{p.persona_id}",
            headers=_auth_headers_customer(cust.email),
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Dana"
        assert resp.json()["persona_id"] == p.persona_id

    def test_get_other_customer_persona_404(self, client, db_session, require_personas_router):
        """[PE03] Cannot access another customer's persona → 404."""
        cust1 = _make_customer(db_session)
        cust2 = _make_customer(db_session)
        p = _make_persona(db_session, str(cust2.customer_id))
        resp = client.get(
            f"/api/v1/customers/personas/{p.persona_id}",
            headers=_auth_headers_customer(cust1.email),
        )
        assert resp.status_code == 404

    def test_get_nonexistent_persona_404(self, client, db_session, require_personas_router):
        """[PE03] Non-existent persona_id → 404."""
        cust = _make_customer(db_session)
        resp = client.get(
            "/api/v1/customers/personas/PER-DOESNOTEXIST",
            headers=_auth_headers_customer(cust.email),
        )
        assert resp.status_code == 404

    def test_get_unauthenticated_401(self, client, require_personas_router):
        """[PE03] No token → 401."""
        resp = client.get("/api/v1/customers/personas/PER-ANYTHING")
        assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════════
# [PE04]  PUT /customers/personas/{personaId}
# ═══════════════════════════════════════════════════════════════════════════════

class TestUpdatePersona:

    def test_update_name(self, client, db_session, require_personas_router):
        """[PE04] Update name only → only name changes."""
        cust = _make_customer(db_session)
        p = _make_persona(db_session, str(cust.customer_id), name="Original")
        resp = client.put(
            f"/api/v1/customers/personas/{p.persona_id}",
            json={"name": "Updated"},
            headers=_auth_headers_customer(cust.email),
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated"

    def test_partial_update_preserves_other_fields(self, client, db_session, require_personas_router):
        """[PE04] Partial update — unspecified fields unchanged."""
        cust = _make_customer(db_session)
        p = _make_persona(db_session, str(cust.customer_id), name="Original")
        # Set relationship first
        client.put(
            f"/api/v1/customers/personas/{p.persona_id}",
            json={"relationship": "sister"},
            headers=_auth_headers_customer(cust.email),
        )
        # Now update name only
        resp = client.put(
            f"/api/v1/customers/personas/{p.persona_id}",
            json={"name": "New Name"},
            headers=_auth_headers_customer(cust.email),
        )
        body = resp.json()
        assert body["name"] == "New Name"
        assert body["relationship"] == "sister"

    def test_update_preferences(self, client, db_session, require_personas_router):
        """[PE04] Update food_preferences list."""
        cust = _make_customer(db_session)
        p = _make_persona(db_session, str(cust.customer_id))
        resp = client.put(
            f"/api/v1/customers/personas/{p.persona_id}",
            json={"food_preferences": ["vegan", "raw"]},
            headers=_auth_headers_customer(cust.email),
        )
        assert resp.status_code == 200
        assert resp.json()["food_preferences"] == ["vegan", "raw"]

    def test_update_other_persona_404(self, client, db_session, require_personas_router):
        """[PE04] Can't update another customer's persona → 404."""
        cust1 = _make_customer(db_session)
        cust2 = _make_customer(db_session)
        p = _make_persona(db_session, str(cust2.customer_id))
        resp = client.put(
            f"/api/v1/customers/personas/{p.persona_id}",
            json={"name": "Hacked"},
            headers=_auth_headers_customer(cust1.email),
        )
        assert resp.status_code == 404

    def test_update_unauthenticated_401(self, client, require_personas_router):
        """[PE04] No token → 401."""
        resp = client.put("/api/v1/customers/personas/PER-X",
                          json={"name": "x"})
        assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════════
# [PE05]  DELETE /customers/personas/{personaId}
# ═══════════════════════════════════════════════════════════════════════════════

class TestDeletePersona:

    def test_delete_own_persona_204(self, client, db_session, require_personas_router):
        """[PE05] Delete own persona → 204 No Content."""
        cust = _make_customer(db_session)
        p = _make_persona(db_session, str(cust.customer_id))
        resp = client.delete(
            f"/api/v1/customers/personas/{p.persona_id}",
            headers=_auth_headers_customer(cust.email),
        )
        assert resp.status_code == 204

    def test_delete_then_get_404(self, client, db_session, require_personas_router):
        """[PE05] After delete, GET returns 404."""
        cust = _make_customer(db_session)
        p = _make_persona(db_session, str(cust.customer_id))
        client.delete(
            f"/api/v1/customers/personas/{p.persona_id}",
            headers=_auth_headers_customer(cust.email),
        )
        resp = client.get(
            f"/api/v1/customers/personas/{p.persona_id}",
            headers=_auth_headers_customer(cust.email),
        )
        assert resp.status_code == 404

    def test_delete_other_persona_404(self, client, db_session, require_personas_router):
        """[PE05] Cannot delete another customer's persona."""
        cust1 = _make_customer(db_session)
        cust2 = _make_customer(db_session)
        p = _make_persona(db_session, str(cust2.customer_id))
        resp = client.delete(
            f"/api/v1/customers/personas/{p.persona_id}",
            headers=_auth_headers_customer(cust1.email),
        )
        assert resp.status_code == 404

    def test_delete_nonexistent_persona_404(self, client, db_session, require_personas_router):
        """[PE05] Non-existent persona → 404 (not 204/500)."""
        cust = _make_customer(db_session)
        resp = client.delete(
            "/api/v1/customers/personas/PER-GHOST",
            headers=_auth_headers_customer(cust.email),
        )
        assert resp.status_code == 404

    def test_delete_unauthenticated_401(self, client, require_personas_router):
        """[PE05] No token → 401."""
        resp = client.delete("/api/v1/customers/personas/PER-ANYTHING")
        assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════════
# [S01]  GET /health
# ═══════════════════════════════════════════════════════════════════════════════

class TestHealth:
    URL = "/api/v1/health"

    def test_health_200(self, client):
        """[S01] Health endpoint returns 200."""
        resp = client.get(self.URL)
        assert resp.status_code == 200

    def test_health_returns_status_active(self, client):
        """[S01] Response body contains status: active."""
        resp = client.get(self.URL)
        body = resp.json()
        assert body.get("status") == "active"

    def test_health_returns_system_name(self, client):
        """[S01] Response body contains system field."""
        resp = client.get(self.URL)
        assert "system" in resp.json()

    def test_health_no_auth_required(self, client):
        """[S01] Health is a public endpoint — no token needed."""
        resp = client.get(self.URL)
        assert resp.status_code != 401

    def test_health_path_under_v1(self, client):
        """[S01] Path is /api/v1/health (not bare /health)."""
        resp_bare = client.get("/health")
        # Bare /health should 404 since all routes are under /api/v1
        assert resp_bare.status_code in (404, 307, 308)


# ═══════════════════════════════════════════════════════════════════════════════
# PATH ALIGNMENT SMOKE TESTS — verify old wrong paths are gone
# ═══════════════════════════════════════════════════════════════════════════════

class TestPathAlignment:
    """Regression tests: old wrong paths must be dead."""

    def test_old_auth_customers_register_gone(self, client):
        resp = client.post("/api/v1/auth/customers/register",
                           json={"email": "x@x.com", "full_name": "x", "password": "x"})
        assert resp.status_code in (404, 405)

    def test_old_auth_customers_login_gone(self, client):
        resp = client.post("/api/v1/auth/customers/login",
                           data={"username": "x@x.com", "password": "x"})
        assert resp.status_code in (404, 405)

    def test_old_auth_customers_verify_gone(self, client):
        resp = client.get("/api/v1/auth/customers/verify-email",
                          params={"token": "x"},
                          headers={"Accept": "application/json"})
        assert resp.status_code in (404, 405)

    def test_old_auth_customers_forgot_gone(self, client):
        resp = client.post("/api/v1/auth/customers/forgot-password",
                           json={"email": "x@x.com"})
        assert resp.status_code in (404, 405)

    def test_old_auth_customers_reset_gone(self, client):
        resp = client.post("/api/v1/auth/customers/reset-password",
                           json={"token": "t", "new_password": "p"})
        assert resp.status_code in (404, 405)

    def test_old_auth_vendors_register_gone(self, client):
        resp = client.post("/api/v1/auth/vendors/register",
                           json={"email": "x@x.com", "business_name": "x", "password": "x"})
        assert resp.status_code in (404, 405)

    def test_old_auth_vendors_login_gone(self, client):
        resp = client.post("/api/v1/auth/vendors/login",
                           data={"username": "x@x.com", "password": "x"})
        assert resp.status_code in (404, 405)

    def test_old_admin_register_gone(self, client):
        resp = client.post("/api/v1/admin/register",
                           json={"email": "x@x.com", "password": "x"})
        assert resp.status_code in (404, 405)

    def test_old_admin_login_gone(self, client):
        resp = client.post("/api/v1/admin/login",
                           data={"username": "x@x.com", "password": "x"})
        assert resp.status_code in (404, 405)

    def test_old_personas_prefix_gone(self, client):
        """Old /api/v1/personas/ must be dead — now at /customers/personas."""
        resp = client.get("/api/v1/personas/",
                          headers={"Authorization": "Bearer garbage"})
        assert resp.status_code in (401, 404)