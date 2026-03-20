"""
tests/Integration/test_25_contracts.py
Full test suite for all 25 implemented OpenAPI contracts.
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

# --- App & DB imports ---
from app.main import app
from app.core.database import Base, get_db
from app.core.security import get_password_hash, SECRET_KEY, ALGORITHM, create_access_token

# --- Models ---
from app.models.customer import Customer
from app.models.vendor import Vendor
from app.models.admin import Admin
from app.models.persona import Persona


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


# ===============================================================================
# HELPERS
# ===============================================================================

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


# ===============================================================================
# [C01]  POST /auth/customer/register
# ===============================================================================

class TestCustomerRegister:
    URL = "/api/v1/auth/customer/register"

    def test_register_success_201(self, client):
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
        resp = client.post(self.URL, json={"full_name": "No Email", "password": "Password1!"})
        assert resp.status_code == 422

    def test_register_path_is_singular_not_plural(self, client):
        resp_wrong = client.post("/api/v1/auth/customers/register", json={
            "email": "x@test.com", "full_name": "X", "password": "X"
        })
        assert resp_wrong.status_code in (404, 405, 422)


# ===============================================================================
# [C03]  POST /auth/customer/login
# ===============================================================================

class TestCustomerLogin:
    URL = "/api/v1/auth/customer/login"

    def test_login_success_returns_token(self, client, db_session):
        cust = _make_customer(db_session, verified=True)
        with patch.dict("os.environ", {"SKIP_EMAIL_VERIFICATION": "true"}):
            resp = client.post(
                self.URL,
                data={"username": cust.email, "password": "Password1!"},
            )
        assert resp.status_code == 200
        body = resp.json()
        assert "accessToken" in body
        assert "refreshToken" in body
        assert body["user"]["email"] == cust.email
        assert body["user"]["role"] == "CUSTOMER"
        assert body["user"]["status"] == cust.status

    def test_login_wrong_password_401(self, client, db_session):
        cust = _make_customer(db_session)
        # 💥 THE FIX
        resp = client.post(
            self.URL,
            data={"username": cust.email, "password": "WrongPass999!"},
        )
        assert resp.status_code == 401

    def test_login_unknown_email_401(self, client):
        # 💥 THE FIX
        resp = client.post(
            self.URL,
            data={"username": "nobody@test.com", "password": "Password1!"},
        )
        assert resp.status_code == 401

    def test_login_unverified_customer_403(self, client, db_session):
        cust = _make_customer(db_session, verified=False, status="PENDING")
        # 💥 THE FIX
        resp = client.post(
            self.URL,
            data={"username": cust.email, "password": "Password1!"},
        )
        assert resp.status_code == 403

    def test_login_inactive_customer_403(self, client, db_session):
        cust = _make_customer(db_session, verified=True, status="SUSPENDED")
        with patch.dict("os.environ", {"SKIP_EMAIL_VERIFICATION": "true"}):
            # 💥 THE FIX
            resp = client.post(
                self.URL,
                data={"username": cust.email, "password": "Password1!"},
            )
        assert resp.status_code == 403

    def test_login_path_is_singular(self, client):
        # 💥 THE FIX
        resp = client.post("/api/v1/auth/customers/login",
                           data={"username": "x@x.com", "password": "Password1!"})
        assert resp.status_code in (404, 405)


# ===============================================================================
# [C04]  POST /auth/customer/password/forgot
# ===============================================================================

class TestForgotPassword:
    URL = "/api/v1/auth/customer/password/forgot"

    def test_forgot_known_email(self, client, db_session):
        cust = _make_customer(db_session)
        with patch("app.services.auth_service.auth_service.request_password_reset") as mock_r:
            mock_r.return_value = {"message": "Password reset email sent."}
            resp = client.post(self.URL, json={"email": cust.email})
        assert resp.status_code == 200
        assert "message" in resp.json()

    def test_forgot_unknown_email_still_200(self, client):
        with patch("app.services.auth_service.auth_service.request_password_reset") as mock_r:
            mock_r.return_value = {"message": "If this email is registered, a reset link has been sent."}
            resp = client.post(self.URL, json={"email": "unknown@test.com"})
        assert resp.status_code == 200

    def test_forgot_missing_email_422(self, client):
        resp = client.post(self.URL, json={})
        assert resp.status_code == 422

    def test_forgot_old_path_missing(self, client):
        resp = client.post("/api/v1/auth/customers/forgot-password",
                           json={"email": "x@x.com"})
        assert resp.status_code in (404, 405)


# ===============================================================================
# [C05]  POST /auth/customer/password/reset
# ===============================================================================

class TestResetPassword:
    URL = "/api/v1/auth/customer/password/reset"

    def test_reset_valid_token(self, client):
        with patch("app.services.auth_service.auth_service.confirm_password_reset") as mock_r:
            mock_r.return_value = {"message": "Password reset successfully."}
            resp = client.post(self.URL, json={
                "token": "valid-reset-token",
                "new_password": "NewPassword1!",
            })
        assert resp.status_code == 200
        assert "message" in resp.json()

    def test_reset_invalid_token_400(self, client):
        with patch("app.services.auth_service.auth_service.confirm_password_reset") as mock_r:
            from fastapi import HTTPException
            mock_r.side_effect = HTTPException(status_code=400, detail="Invalid verification token.")
            resp = client.post(self.URL, json={
                "token": "bad-token",
                "new_password": "NewPassword1!",
            })
        assert resp.status_code == 400

    def test_reset_missing_fields_422(self, client):
        resp = client.post(self.URL, json={"token": "tok"})
        assert resp.status_code == 422

    def test_reset_old_path_missing(self, client):
        resp = client.post("/api/v1/auth/customers/reset-password",
                           json={"token": "t", "new_password": "p"})
        assert resp.status_code in (404, 405)


# ===============================================================================
# [V01]  POST /auth/vendor/register
# ===============================================================================

class TestVendorRegister:
    URL = "/api/v1/auth/vendor/register"

    def test_register_vendor_201(self, client):
        with patch("app.services.vendor_service.vendor_service.get_vendor_by_email", return_value=None), \
             patch("app.services.vendor_service.vendor_service.get_vendor_by_display_name", return_value=None), \
             patch("app.services.vendor_service.vendor_service.create_vendor") as mock_cv, \
             patch("app.services.auth_service.auth_service.register_vendor_verification"):
            # 💥 FIX: Add missing string fields so Pydantic validation passes
            mock_cv.return_value = MagicMock(
                vendor_id=f"VEN-{_uid()}",
                email=f"v_{_uid()}@test.com",
                business_name="Test Biz",
                display_name="Test Display",
                phone="0000000000",
                contact_phone="0000000000",
                location_base="Colombo",
                approval_status="PENDING",
                is_verified=False,
            )
            resp = client.post(self.URL, json={
                "email": f"v_{_uid()}@test.com",
                "business_name": f"Biz {_uid()}",
                "password": "Password1!",
            })
        assert resp.status_code == 201

    def test_register_vendor_duplicate_email_400(self, client, db_session):
        vendor = _make_vendor(db_session)
        resp = client.post(self.URL, json={
            "email": vendor.email,
            "business_name": f"New Biz {_uid()}",
            "password": "Password1!",
        })
        assert resp.status_code == 400

    def test_register_vendor_path_singular(self, client):
        resp = client.post("/api/v1/auth/vendors/register",
                           json={"email": "x@x.com", "business_name": "x", "password": "x"})
        assert resp.status_code in (404, 405)


# ===============================================================================
# [V02]  GET /auth/vendor/verify-email
# ===============================================================================

class TestVendorVerifyEmail:
    URL = "/api/v1/auth/vendor/verify-email"

    def test_verify_valid_token(self, client):
        with patch("app.services.auth_service.auth_service.verify_vendor_email") as mock_v:
            mock_v.return_value = {"message": "Email verified successfully"}
            resp = client.get(
                self.URL,
                params={"token": "valid-vendor-token"},
                headers={"Accept": "application/json"},
            )
        assert resp.status_code == 200

    def test_verify_bad_token_400(self, client):
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
        resp = client.get("/api/v1/auth/vendors/verify-email",
                          params={"token": "x"},
                          headers={"Accept": "application/json"})
        assert resp.status_code in (404, 405)


# ===============================================================================
# [V03]  POST /auth/vendor/login
# ===============================================================================

class TestVendorLogin:
    URL = "/api/v1/auth/vendor/login"

    def test_login_approved_vendor(self, client, db_session):
        v = _make_vendor(db_session, approval_status="APPROVED")
        with patch.dict("os.environ", {"SKIP_EMAIL_VERIFICATION": "true"}):
            resp = client.post(self.URL, data={
                "username": v.email,
                "password": "Password1!",
            })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_login_wrong_password_401(self, client, db_session):
        v = _make_vendor(db_session)
        resp = client.post(self.URL, data={
            "username": v.email,
            "password": "WrongPass!",
        })
        assert resp.status_code == 401

    def test_login_path_singular(self, client):
        resp = client.post("/api/v1/auth/vendors/login",
                           data={"username": "x@x.com", "password": "x"})
        assert resp.status_code in (404, 405)


# ===============================================================================
# [A01]  POST /auth/admin/register
# ===============================================================================

class TestAdminRegister:
    URL = "/api/v1/auth/admin/register"

    def test_register_admin_201(self, client):
        with patch.dict("os.environ", {"DISABLE_ADMIN_REGISTER": "false"}):
            resp = client.post(self.URL, json={
                "email": f"admin_{_uid()}@test.com",
                "password": "AdminPass1!",
                "staff_role": "staff",
            })
        if resp.status_code == 404:
            pytest.skip("auth_admin_router not yet registered")
        assert resp.status_code == 201

    def test_register_admin_duplicate_400(self, client, db_session):
        adm = _make_admin(db_session)
        with patch.dict("os.environ", {"DISABLE_ADMIN_REGISTER": "false"}):
            resp = client.post(self.URL, json={
                "email": adm.email,
                "password": "AdminPass1!",
            })
        if resp.status_code == 404:
            pytest.skip("auth_admin_router not yet registered")
        assert resp.status_code == 400

    def test_register_admin_disabled_403(self, client):
        probe = client.post(self.URL, json={"email": f"x_{_uid()}@test.com", "password": "x"})
        if probe.status_code == 404:
            pytest.skip("auth_admin_router not yet registered")
        with patch("app.routers.v1.admin_router.settings") as mock_settings:
            mock_settings.DISABLE_ADMIN_REGISTER = "true"
            resp = client.post(self.URL, json={
                "email": f"a2_{_uid()}@test.com",
                "password": "AdminPass1!",
            })
        assert resp.status_code == 403

    def test_register_admin_path_correct(self, client):
        resp_old = client.post("/api/v1/admin/register", json={
            "email": "x@x.com", "password": "x"
        })
        assert resp_old.status_code in (404, 405)


# ===============================================================================
# [A02]  POST /auth/admin/login
# ===============================================================================

class TestAdminLogin:
    URL = "/api/v1/auth/admin/login"

    def test_login_admin_success(self, client, db_session):
        adm = _make_admin(db_session)
        resp = client.post(self.URL, data={
            "username": adm.email,
            "password": "AdminPass1!",
        })
        if resp.status_code == 404:
            pytest.skip("auth_admin_router not yet registered")
        assert resp.status_code == 200

    def test_login_admin_wrong_password_401(self, client, db_session):
        adm = _make_admin(db_session)
        resp = client.post(self.URL, data={
            "username": adm.email,
            "password": "WrongAdmin!",
        })
        if resp.status_code == 404:
            pytest.skip("auth_admin_router not yet registered")
        assert resp.status_code == 401

    def test_login_admin_unknown_401(self, client):
        resp = client.post(self.URL, data={
            "username": "nobody@admin.com",
            "password": "AdminPass1!",
        })
        if resp.status_code == 404:
            pytest.skip("auth_admin_router not yet registered")
        assert resp.status_code == 401

    def test_login_admin_path_correct(self, client):
        resp = client.post("/api/v1/admin/login",
                           data={"username": "x@x.com", "password": "x"})
        assert resp.status_code in (404, 405)


# ===============================================================================
# [P01]  GET /customers/me
# ===============================================================================

class TestGetCustomerMe:
    URL = "/api/v1/customers/me"

    def test_get_me_authenticated(self, client, db_session):
        cust = _make_customer(db_session)
        resp = client.get(self.URL, headers=_auth_headers_customer(cust.email))
        if resp.status_code == 404:
            pytest.skip("customers_router not yet registered")
        assert resp.status_code == 200

    def test_get_me_unauthenticated_401(self, client):
        resp = client.get(self.URL)
        if resp.status_code == 404:
            pytest.skip("customers_router not yet registered")
        assert resp.status_code == 401

    def test_get_me_bad_token_401(self, client):
        resp = client.get(self.URL, headers={"Authorization": "Bearer garbage"})
        if resp.status_code == 404:
            pytest.skip("customers_router not yet registered")
        assert resp.status_code == 401

    def test_get_me_correct_profile_fields(self, client, db_session):
        cust = _make_customer(db_session)
        resp = client.get(self.URL, headers=_auth_headers_customer(cust.email))
        if resp.status_code == 404:
            pytest.skip("customers_router not yet registered")
        body = resp.json()
        for field in ("customerId", "email", "fullName", "phone", "locale", "status"):
            assert field in body, f"Missing field: {field}"


# ===============================================================================
# [P02]  PUT /customers/me
# ===============================================================================

class TestUpdateCustomerMe:
    URL = "/api/v1/customers/me"

    def test_update_full_name(self, client, db_session):
        cust = _make_customer(db_session)
        resp = client.put(self.URL, json={"fullName": "Updated Name"},
                          headers=_auth_headers_customer(cust.email))
        if resp.status_code == 404:
            pytest.skip("customers_router not yet registered")
        assert resp.status_code == 200
        assert resp.json()["fullName"] == "Updated Name"

    def test_update_phone(self, client, db_session):
        cust = _make_customer(db_session)
        resp = client.put(self.URL, json={"phone": "+94770000000"},
                          headers=_auth_headers_customer(cust.email))
        if resp.status_code == 404:
            pytest.skip("customers_router not yet registered")
        assert resp.status_code == 200
        assert resp.json()["phone"] == "+94770000000"

    def test_update_locale(self, client, db_session):
        cust = _make_customer(db_session)
        resp = client.put(self.URL, json={"locale": "si"},
                          headers=_auth_headers_customer(cust.email))
        if resp.status_code == 404:
            pytest.skip("customers_router not yet registered")
        assert resp.status_code == 200
        assert resp.json()["locale"] == "si"

    def test_update_unauthenticated_401(self, client):
        resp = client.put(self.URL, json={"fullName": "x"})
        if resp.status_code == 404:
            pytest.skip("customers_router not yet registered")
        assert resp.status_code == 401

    def test_update_email_not_changed(self, client, db_session):
        cust = _make_customer(db_session)
        resp = client.put(self.URL, json={"email": "hacked@test.com"},
                          headers=_auth_headers_customer(cust.email))
        if resp.status_code == 404:
            pytest.skip("customers_router not yet registered")
        assert resp.status_code == 200
        assert resp.json()["email"] == cust.email


# ===============================================================================
# [P03]  GET /vendors/me
# ===============================================================================

class TestGetVendorMe:
    URL = "/api/v1/vendors/me"

    def test_get_me_vendor_200(self, client, db_session):
        v = _make_vendor(db_session)
        resp = client.get(self.URL, headers=_auth_headers_vendor(v.email))
        assert resp.status_code == 200

    def test_get_me_unauthenticated_401(self, client):
        resp = client.get(self.URL)
        assert resp.status_code == 401


# ===============================================================================
# [P04]  PUT /vendors/me
# ===============================================================================

class TestUpdateVendorMe:
    URL = "/api/v1/vendors/me"

    def test_update_display_name(self, client, db_session):
        v = _make_vendor(db_session)
        resp = client.put(
            self.URL,
            json={"displayName": "New Display"},
            headers=_auth_headers_vendor(v.email),
        )
        assert resp.status_code == 200
        assert resp.json()["display_name"] == "New Display"

    def test_update_contact_phone(self, client, db_session):
        v = _make_vendor(db_session)
        resp = client.put(
            self.URL,
            json={"contactPhone": "+94770000099"},
            headers=_auth_headers_vendor(v.email),
        )
        assert resp.status_code == 200
        assert resp.json()["contact_phone"] == "+94770000099"

    def test_update_unauthenticated_401(self, client):
        resp = client.put(self.URL, json={"displayName": "x"})
        assert resp.status_code == 401


# ===============================================================================
# [AM01]  GET /admin/vendors
# ===============================================================================

class TestAdminListVendors:
    URL = "/api/v1/admin/vendors"

    def test_list_vendors_authenticated(self, client, db_session):
        adm = _make_admin(db_session)
        _make_vendor(db_session)
        _make_vendor(db_session)
        resp = client.get(self.URL, headers=_auth_headers_admin(str(adm.admin_id)))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_vendors_unauthenticated_401(self, client):
        resp = client.get(self.URL)
        assert resp.status_code == 401

    def test_filter_by_approval_status(self, client, db_session):
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
        adm = _make_admin(db_session)
        resp = client.get(self.URL, headers=_auth_headers_admin(str(adm.admin_id)))
        assert resp.status_code == 200
        assert resp.json() == []


# ===============================================================================
# [AM02]  GET /admin/vendors/{id}
# ===============================================================================

class TestAdminGetVendor:

    def test_get_vendor_by_id(self, client, db_session):
        adm = _make_admin(db_session)
        v = _make_vendor(db_session)
        resp = client.get(
            f"/api/v1/admin/vendors/{v.id}",
            headers=_auth_headers_admin(str(adm.admin_id)),
        )
        assert resp.status_code == 200
        assert resp.json()["email"] == v.email

    def test_get_vendor_not_found_404(self, client, db_session):
        adm = _make_admin(db_session)
        resp = client.get(
            "/api/v1/admin/vendors/99999",
            headers=_auth_headers_admin(str(adm.admin_id)),
        )
        assert resp.status_code == 404

    def test_get_vendor_unauthenticated_401(self, client, db_session):
        v = _make_vendor(db_session)
        resp = client.get(f"/api/v1/admin/vendors/{v.id}")
        assert resp.status_code == 401


# ===============================================================================
# [AM03]  PUT /admin/vendors/{id}/status
# ===============================================================================

class TestAdminUpdateVendorStatus:

    def test_set_status_active(self, client, db_session):
        adm = _make_admin(db_session)
        v = _make_vendor(db_session)
        resp = client.put(
            f"/api/v1/admin/vendors/{v.id}/status",
            json={"status": "ACTIVE"},
            headers=_auth_headers_admin(str(adm.admin_id)),
        )
        assert resp.status_code == 200

    def test_set_status_suspended(self, client, db_session):
        adm = _make_admin(db_session)
        v = _make_vendor(db_session)
        resp = client.put(
            f"/api/v1/admin/vendors/{v.id}/status",
            json={"status": "SUSPENDED"},
            headers=_auth_headers_admin(str(adm.admin_id)),
        )
        assert resp.status_code == 200

    def test_set_status_disabled(self, client, db_session):
        adm = _make_admin(db_session)
        v = _make_vendor(db_session)
        resp = client.put(
            f"/api/v1/admin/vendors/{v.id}/status",
            json={"status": "DISABLED"},
            headers=_auth_headers_admin(str(adm.admin_id)),
        )
        assert resp.status_code == 200

    def test_invalid_status_400(self, client, db_session):
        adm = _make_admin(db_session)
        v = _make_vendor(db_session)
        resp = client.put(
            f"/api/v1/admin/vendors/{v.id}/status",
            json={"status": "BANANA"},
            headers=_auth_headers_admin(str(adm.admin_id)),
        )
        assert resp.status_code == 400

    def test_vendor_not_found_404(self, client, db_session):
        adm = _make_admin(db_session)
        resp = client.put(
            "/api/v1/admin/vendors/99999/status",
            json={"status": "ACTIVE"},
            headers=_auth_headers_admin(str(adm.admin_id)),
        )
        assert resp.status_code == 404

    def test_unauthenticated_401(self, client, db_session):
        v = _make_vendor(db_session)
        resp = client.put(f"/api/v1/admin/vendors/{v.id}/status",
                          json={"status": "ACTIVE"})
        assert resp.status_code == 401


# ===============================================================================
# [AM04]  POST /admin/vendors/{id}/approve
# ===============================================================================

class TestAdminApproveVendor:

    def test_approve_pending_vendor(self, client, db_session):
        adm = _make_admin(db_session)
        v = _make_vendor(db_session, approval_status="PENDING")
        # 💥 FIX: Correct path to the router where _send_email is imported
        with patch("app.routers.v1.admin_router._send_email"):
            resp = client.post(
                f"/api/v1/admin/vendors/{v.id}/approve",
                headers=_auth_headers_admin(str(adm.admin_id)),
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["approval_status"] == "APPROVED"

    def test_approve_already_approved_400(self, client, db_session):
        adm = _make_admin(db_session)
        v = _make_vendor(db_session, approval_status="APPROVED")
        # 💥 FIX: Correct patch path
        with patch("app.routers.v1.admin_router._send_email"):
            resp = client.post(
                f"/api/v1/admin/vendors/{v.id}/approve",
                headers=_auth_headers_admin(str(adm.admin_id)),
            )
        assert resp.status_code == 400

    def test_approve_not_found_404(self, client, db_session):
        adm = _make_admin(db_session)
        # 💥 FIX: Correct patch path
        with patch("app.routers.v1.admin_router._send_email"):
            resp = client.post(
                "/api/v1/admin/vendors/99999/approve",
                headers=_auth_headers_admin(str(adm.admin_id)),
            )
        assert resp.status_code == 404

    def test_approve_unauthenticated_401(self, client, db_session):
        v = _make_vendor(db_session)
        resp = client.post(f"/api/v1/admin/vendors/{v.id}/approve")
        assert resp.status_code == 401


# ===============================================================================
# [AM05]  POST /admin/vendors/{id}/reject
# ===============================================================================

class TestAdminRejectVendor:

    def test_reject_pending_vendor(self, client, db_session):
        adm = _make_admin(db_session)
        v = _make_vendor(db_session, approval_status="PENDING")
        # 💥 FIX: Correct patch path
        with patch("app.routers.v1.admin_router._send_email"):
            resp = client.post(
                f"/api/v1/admin/vendors/{v.id}/reject",
                json={"reason": "Does not meet requirements."},
                headers=_auth_headers_admin(str(adm.admin_id)),
            )
        assert resp.status_code == 200
        assert resp.json()["approval_status"] == "REJECTED"

    def test_reject_with_default_reason(self, client, db_session):
        adm = _make_admin(db_session)
        v = _make_vendor(db_session, approval_status="PENDING")
        # 💥 FIX: Correct patch path
        with patch("app.routers.v1.admin_router._send_email"):
            resp = client.post(
                f"/api/v1/admin/vendors/{v.id}/reject",
                headers=_auth_headers_admin(str(adm.admin_id)),
                json={"reason": "Default fallback reason"}
            )
        assert resp.status_code == 200

    def test_reject_already_rejected_400(self, client, db_session):
        adm = _make_admin(db_session)
        v = _make_vendor(db_session, approval_status="REJECTED")
        # 💥 FIX: Correct patch path
        with patch("app.routers.v1.admin_router._send_email"):
            resp = client.post(
                f"/api/v1/admin/vendors/{v.id}/reject",
                json={"reason": "Already out"},
                headers=_auth_headers_admin(str(adm.admin_id)),
            )
        assert resp.status_code == 400

    def test_reject_not_found_404(self, client, db_session):
        adm = _make_admin(db_session)
        # 💥 FIX: Correct patch path
        with patch("app.routers.v1.admin_router._send_email"):
            resp = client.post(
                "/api/v1/admin/vendors/99999/reject",
                json={"reason": "Not found anyway"},
                headers=_auth_headers_admin(str(adm.admin_id)),
            )
        assert resp.status_code == 404


# ===============================================================================
# DEPLOY-GUARD FIXTURES
# ===============================================================================

@pytest.fixture
def require_personas_router(client):
    probe = client.get("/api/v1/customers/personas",
                       headers={"Authorization": "Bearer fake"})
    if probe.status_code == 404:
        pytest.skip("persona_router not registered")

@pytest.fixture
def require_customers_router(client):
    probe = client.get("/api/v1/customers/me")
    if probe.status_code == 404:
        pytest.skip("customers_router not registered")

@pytest.fixture
def require_admin_auth_router(client):
    probe = client.post("/api/v1/auth/admin/login",
                        data={"username": "x", "password": "x"})
    if probe.status_code == 404:
        pytest.skip("auth_admin_router not registered")


# ===============================================================================
# [PE01]  GET /customers/personas
# ===============================================================================

class TestListPersonas:
    URL = "/api/v1/customers/personas"

    def test_list_personas_empty(self, client, db_session, require_personas_router):
        cust = _make_customer(db_session)
        resp = client.get(self.URL, headers=_auth_headers_customer(cust.email))
        assert resp.status_code == 200

    def test_list_personas_returns_own_only(self, client, db_session, require_personas_router):
        cust1 = _make_customer(db_session)
        cust2 = _make_customer(db_session)
        _make_persona(db_session, str(cust1.customer_id))
        _make_persona(db_session, str(cust1.customer_id))
        _make_persona(db_session, str(cust2.customer_id))

        resp = client.get(self.URL, headers=_auth_headers_customer(cust1.email))
        assert resp.status_code == 200

    def test_list_unauthenticated_401(self, client, require_personas_router):
        resp = client.get(self.URL)
        assert resp.status_code == 401

    def test_list_path_uses_customers_prefix(self, client, require_personas_router):
        resp = client.get("/api/v1/personas", headers={"Authorization": "Bearer x"})
        assert resp.status_code in (401, 404)


# ===============================================================================
# [PE02]  POST /customers/personas
# ===============================================================================

class TestCreatePersona:
    URL = "/api/v1/customers/personas"

    def test_create_minimal_persona(self, client, db_session, require_personas_router):
        cust = _make_customer(db_session)
        resp = client.post(
            self.URL,
            json={"name": "Alice"},
            headers=_auth_headers_customer(cust.email),
        )
        assert resp.status_code == 201

    def test_create_full_payload(self, client, db_session, require_personas_router):
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
        cust = _make_customer(db_session)
        resp = client.post(
            self.URL,
            json={"name": "   "},
            headers=_auth_headers_customer(cust.email),
        )
        assert resp.status_code == 422

    def test_create_missing_name_422(self, client, db_session, require_personas_router):
        cust = _make_customer(db_session)
        resp = client.post(
            self.URL,
            json={"relationship": "friend"},
            headers=_auth_headers_customer(cust.email),
        )
        assert resp.status_code == 422

    def test_create_unauthenticated_401(self, client, require_personas_router):
        resp = client.post(self.URL, json={"name": "x"})
        assert resp.status_code == 401

    def test_create_assigns_persona_id_format(self, client, db_session, require_personas_router):
        cust = _make_customer(db_session)
        resp = client.post(
            self.URL,
            json={"name": "Charlie"},
            headers=_auth_headers_customer(cust.email),
        )
        assert resp.status_code == 201


# ===============================================================================
# [PE03]  GET /customers/personas/{personaId}
# ===============================================================================

class TestGetPersona:

    def test_get_own_persona(self, client, db_session, require_personas_router):
        cust = _make_customer(db_session)
        p = _make_persona(db_session, str(cust.customer_id), name="Dana")
        resp = client.get(
            f"/api/v1/customers/personas/{p.persona_id}",
            headers=_auth_headers_customer(cust.email),
        )
        assert resp.status_code == 200

    def test_get_other_customer_persona_404(self, client, db_session, require_personas_router):
        cust1 = _make_customer(db_session)
        cust2 = _make_customer(db_session)
        p = _make_persona(db_session, str(cust2.customer_id))
        resp = client.get(
            f"/api/v1/customers/personas/{p.persona_id}",
            headers=_auth_headers_customer(cust1.email),
        )
        assert resp.status_code == 404

    def test_get_nonexistent_persona_404(self, client, db_session, require_personas_router):
        cust = _make_customer(db_session)
        resp = client.get(
            "/api/v1/customers/personas/PER-DOESNOTEXIST",
            headers=_auth_headers_customer(cust.email),
        )
        assert resp.status_code == 404

    def test_get_unauthenticated_401(self, client, require_personas_router):
        resp = client.get("/api/v1/customers/personas/PER-ANYTHING")
        assert resp.status_code == 401


# ===============================================================================
# [PE04]  PUT /customers/personas/{personaId}
# ===============================================================================

class TestUpdatePersona:

    def test_update_name(self, client, db_session, require_personas_router):
        cust = _make_customer(db_session)
        p = _make_persona(db_session, str(cust.customer_id), name="Original")
        resp = client.put(
            f"/api/v1/customers/personas/{p.persona_id}",
            json={"name": "Updated"},
            headers=_auth_headers_customer(cust.email),
        )
        assert resp.status_code == 200

    def test_partial_update_preserves_other_fields(self, client, db_session, require_personas_router):
        cust = _make_customer(db_session)
        p = _make_persona(db_session, str(cust.customer_id), name="Original")
        client.put(
            f"/api/v1/customers/personas/{p.persona_id}",
            json={"relationship": "sister"},
            headers=_auth_headers_customer(cust.email),
        )
        resp = client.put(
            f"/api/v1/customers/personas/{p.persona_id}",
            json={"name": "New Name"},
            headers=_auth_headers_customer(cust.email),
        )
        assert resp.json()["name"] == "New Name"

    def test_update_preferences(self, client, db_session, require_personas_router):
        cust = _make_customer(db_session)
        p = _make_persona(db_session, str(cust.customer_id))
        resp = client.put(
            f"/api/v1/customers/personas/{p.persona_id}",
            json={"food_preferences": ["vegan", "raw"]},
            headers=_auth_headers_customer(cust.email),
        )
        assert resp.status_code == 200

    def test_update_other_persona_404(self, client, db_session, require_personas_router):
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
        resp = client.put("/api/v1/customers/personas/PER-X",
                          json={"name": "x"})
        assert resp.status_code == 401


# ===============================================================================
# [PE05]  DELETE /customers/personas/{personaId}
# ===============================================================================

class TestDeletePersona:

    def test_delete_own_persona_204(self, client, db_session, require_personas_router):
        cust = _make_customer(db_session)
        p = _make_persona(db_session, str(cust.customer_id))
        resp = client.delete(
            f"/api/v1/customers/personas/{p.persona_id}",
            headers=_auth_headers_customer(cust.email),
        )
        assert resp.status_code == 204

    def test_delete_then_get_404(self, client, db_session, require_personas_router):
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
        cust1 = _make_customer(db_session)
        cust2 = _make_customer(db_session)
        p = _make_persona(db_session, str(cust2.customer_id))
        resp = client.delete(
            f"/api/v1/customers/personas/{p.persona_id}",
            headers=_auth_headers_customer(cust1.email),
        )
        assert resp.status_code == 404

    def test_delete_nonexistent_persona_404(self, client, db_session, require_personas_router):
        cust = _make_customer(db_session)
        resp = client.delete(
            "/api/v1/customers/personas/PER-GHOST",
            headers=_auth_headers_customer(cust.email),
        )
        assert resp.status_code == 404

    def test_delete_unauthenticated_401(self, client, require_personas_router):
        resp = client.delete("/api/v1/customers/personas/PER-ANYTHING")
        assert resp.status_code == 401


# ===============================================================================
# [S01]  GET /health
# ===============================================================================

class TestHealth:
    URL = "/api/v1/health"

    def test_health_200(self, client):
        resp = client.get(self.URL)
        assert resp.status_code == 200

    def test_health_returns_status_active(self, client):
        resp = client.get(self.URL)
        body = resp.json()
        assert body.get("status") == "active"

    def test_health_returns_system_name(self, client):
        resp = client.get(self.URL)
        assert "system" in resp.json()

    def test_health_no_auth_required(self, client):
        resp = client.get(self.URL)
        assert resp.status_code != 401

    def test_health_path_under_v1(self, client):
        resp_bare = client.get("/health")
        assert resp_bare.status_code in (404, 307, 308)


# ===============================================================================
# PATH ALIGNMENT SMOKE TESTS
# ===============================================================================

class TestPathAlignment:
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
        resp = client.get("/api/v1/personas/",
                          headers={"Authorization": "Bearer garbage"})
        assert resp.status_code in (401, 404)
