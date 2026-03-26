from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch
from uuid import uuid4

from app.core.database import SessionLocal
from app.core.security import create_access_token, create_refresh_token, get_password_hash
from app.models.admin import Admin
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


def _uid(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12]}"


def _create_customer(password: str = "Pass12345!") -> Customer:
    db = SessionLocal()
    customer = Customer(
        customer_id=_uid("CUS"),
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


def _create_vendor(password: str = "VendPass123!") -> Vendor:
    db = SessionLocal()
    vendor = Vendor(
        vendor_id=_uid("VEN"),
        business_name="Test Vendor",
        display_name="Test Vendor",
        email=f"vendor-{uuid4().hex[:8]}@test.com",
        password_hash=get_password_hash(password),
        is_verified=True,
        approval_status="APPROVED",
        location_base="Colombo",
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    db.close()
    return vendor


def _create_admin() -> Admin:
    db = SessionLocal()
    admin = Admin(
        admin_id=_uid("ADM"),
        email=f"admin-{uuid4().hex[:8]}@test.com",
        password_hash=get_password_hash("AdminPass123!"),
        staff_role="staff",
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    db.close()
    return admin


def _customer_login(client, email: str, password: str):
    return client.post("/api/v1/auth/customer/login", json={"email": email, "password": password})


def _vendor_login(client, email: str, password: str):
    return client.post("/api/v1/auth/vendor/login", json={"email": email, "password": password})


def test_customer_can_change_password(client):
    customer = _create_customer("Pass12345!")
    fake_redis = _FakeRedis()
    with patch("app.services.auth_service._get_redis", return_value=fake_redis), patch(
        "app.core.security.is_token_blacklisted",
        side_effect=lambda t: bool(fake_redis.exists(f"blacklist:{t}")),
    ):
        login = _customer_login(client, customer.email, "Pass12345!")
        assert login.status_code == 200
        access = login.json()["accessToken"]

        change = client.post(
            "/api/v1/auth/customer/password/change",
            json={"currentPassword": "Pass12345!", "newPassword": "Pass54321!"},
            headers={"Authorization": f"Bearer {access}"},
        )
        assert change.status_code == 200

        reuse = client.post("/api/v1/auth/customer/logout", headers={"Authorization": f"Bearer {access}"})
        assert reuse.status_code == 401

        assert _customer_login(client, customer.email, "Pass12345!").status_code == 401
        assert _customer_login(client, customer.email, "Pass54321!").status_code == 200


def test_customer_wrong_current_password(client):
    customer = _create_customer("Pass12345!")
    login = _customer_login(client, customer.email, "Pass12345!")
    access = login.json()["accessToken"]
    r = client.post(
        "/api/v1/auth/customer/password/change",
        json={"currentPassword": "Wrong12345!", "newPassword": "Pass54321!"},
        headers={"Authorization": f"Bearer {access}"},
    )
    assert r.status_code == 400


def test_customer_same_password_rejected(client):
    customer = _create_customer("Pass12345!")
    login = _customer_login(client, customer.email, "Pass12345!")
    access = login.json()["accessToken"]
    r = client.post(
        "/api/v1/auth/customer/password/change",
        json={"currentPassword": "Pass12345!", "newPassword": "Pass12345!"},
        headers={"Authorization": f"Bearer {access}"},
    )
    assert r.status_code == 400


def test_customer_new_password_too_short(client):
    customer = _create_customer("Pass12345!")
    login = _customer_login(client, customer.email, "Pass12345!")
    access = login.json()["accessToken"]
    r = client.post(
        "/api/v1/auth/customer/password/change",
        json={"currentPassword": "Pass12345!", "newPassword": "1234"},
        headers={"Authorization": f"Bearer {access}"},
    )
    assert r.status_code == 422


def test_customer_password_change_requires_auth(client):
    r = client.post(
        "/api/v1/auth/customer/password/change",
        json={"currentPassword": "Pass12345!", "newPassword": "Pass54321!"},
    )
    assert r.status_code == 401


def test_vendor_can_change_password(client):
    vendor = _create_vendor("VendPass123!")
    fake_redis = _FakeRedis()
    with patch("app.services.auth_service._get_redis", return_value=fake_redis), patch(
        "app.core.security.is_token_blacklisted",
        side_effect=lambda t: bool(fake_redis.exists(f"blacklist:{t}")),
    ):
        login = _vendor_login(client, vendor.email, "VendPass123!")
        assert login.status_code == 200
        access = login.json()["accessToken"]
        change = client.post(
            "/api/v1/auth/vendor/password/change",
            json={"currentPassword": "VendPass123!", "newPassword": "VendPass321!"},
            headers={"Authorization": f"Bearer {access}"},
        )
        assert change.status_code == 200
        assert _vendor_login(client, vendor.email, "VendPass123!").status_code == 401
        assert _vendor_login(client, vendor.email, "VendPass321!").status_code == 200


def test_vendor_wrong_current_password(client):
    vendor = _create_vendor("VendPass123!")
    login = _vendor_login(client, vendor.email, "VendPass123!")
    access = login.json()["accessToken"]
    r = client.post(
        "/api/v1/auth/vendor/password/change",
        json={"currentPassword": "WrongPass123!", "newPassword": "VendPass321!"},
        headers={"Authorization": f"Bearer {access}"},
    )
    assert r.status_code == 400


def test_admin_can_get_own_profile(client):
    admin = _create_admin()
    token = create_access_token({"sub": admin.admin_id, "type": "admin", "role": admin.staff_role})
    r = client.get("/api/v1/admin/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()
    assert body["adminId"] == admin.admin_id
    assert body["email"] == admin.email
    assert "staffRole" in body


def test_admin_me_requires_auth(client):
    r = client.get("/api/v1/admin/me")
    assert r.status_code == 401


def test_admin_me_returns_correct_email(client):
    admin = _create_admin()
    token = create_access_token({"sub": admin.admin_id, "type": "admin", "role": admin.staff_role})
    r = client.get("/api/v1/admin/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == admin.email


def test_admin_can_logout(client):
    admin = _create_admin()
    access = create_access_token({"sub": admin.admin_id, "type": "admin", "role": admin.staff_role})
    fake_redis = _FakeRedis()
    with patch("app.services.admin_service._get_redis", return_value=fake_redis), patch(
        "app.core.security.is_token_blacklisted",
        side_effect=lambda t: bool(fake_redis.exists(f"blacklist:{t}")),
    ):
        first = client.post("/api/v1/auth/admin/logout", headers={"Authorization": f"Bearer {access}"})
        second = client.post("/api/v1/auth/admin/logout", headers={"Authorization": f"Bearer {access}"})
    assert first.status_code == 200
    assert second.status_code == 401


def test_admin_logout_requires_auth(client):
    r = client.post("/api/v1/auth/admin/logout")
    assert r.status_code == 401


def test_admin_can_refresh_token(client):
    admin = _create_admin()
    refresh = create_refresh_token({"sub": admin.admin_id, "role": "ADMIN"})
    r = client.post("/api/v1/auth/admin/token/refresh", json={"refreshToken": refresh})
    assert r.status_code == 200
    body = r.json()
    assert "accessToken" in body
    assert "refreshToken" in body
    assert body["user"]["userId"] == admin.admin_id


def test_admin_refresh_with_invalid_token(client):
    r = client.post("/api/v1/auth/admin/token/refresh", json={"refreshToken": "bad-token"})
    assert r.status_code == 401


def test_admin_refresh_with_customer_token(client):
    customer = _create_customer()
    refresh = create_refresh_token({"sub": customer.email, "role": "CUSTOMER"})
    r = client.post("/api/v1/auth/admin/token/refresh", json={"refreshToken": refresh})
    assert r.status_code == 401


def test_admin_refresh_with_expired_token(client):
    admin = _create_admin()
    refresh = create_refresh_token({"sub": admin.admin_id, "role": "ADMIN"}, expires_delta=timedelta(seconds=-1))
    r = client.post("/api/v1/auth/admin/token/refresh", json={"refreshToken": refresh})
    assert r.status_code == 401


def test_customer_can_delete_account(client):
    customer = _create_customer("Pass12345!")
    login = _customer_login(client, customer.email, "Pass12345!")
    assert login.status_code == 200
    access = login.json()["accessToken"]
    deleted = client.delete("/api/v1/auth/customer/delete", headers={"Authorization": f"Bearer {access}"})
    assert deleted.status_code == 200
    assert deleted.json()["message"] == "Customer account deleted successfully."
    assert _customer_login(client, customer.email, "Pass12345!").status_code == 401


def test_customer_delete_requires_auth(client):
    r = client.delete("/api/v1/auth/customer/delete")
    assert r.status_code == 401


def test_vendor_can_delete_account(client):
    vendor = _create_vendor("VendPass123!")
    login = _vendor_login(client, vendor.email, "VendPass123!")
    assert login.status_code == 200
    access = login.json()["accessToken"]
    deleted = client.delete("/api/v1/auth/vendor/delete", headers={"Authorization": f"Bearer {access}"})
    assert deleted.status_code == 200
    assert deleted.json()["message"] == "Vendor account deleted successfully."
    assert _vendor_login(client, vendor.email, "VendPass123!").status_code == 401


def test_vendor_delete_requires_auth(client):
    r = client.delete("/api/v1/auth/vendor/delete")
    assert r.status_code == 401


def test_admin_can_delete_account(client):
    admin = _create_admin()
    access = create_access_token({"sub": admin.admin_id, "type": "admin", "role": admin.staff_role})
    deleted = client.delete("/api/v1/auth/admin/delete", headers={"Authorization": f"Bearer {access}"})
    assert deleted.status_code == 200
    assert deleted.json()["message"] == "Admin account deleted successfully."
    reuse = client.get("/api/v1/admin/me", headers={"Authorization": f"Bearer {access}"})
    assert reuse.status_code == 401


def test_admin_delete_requires_auth(client):
    r = client.delete("/api/v1/auth/admin/delete")
    assert r.status_code == 401


def test_customer_register_duplicate_email_message(client):
    email = f"dup-customer-{uuid4().hex[:8]}@test.com"
    payload = {"fullName": "Dup Customer", "email": email, "password": "Pass12345!"}
    first = client.post("/api/v1/auth/customer/register", json=payload)
    assert first.status_code == 201
    second = client.post("/api/v1/auth/customer/register", json=payload)
    assert second.status_code == 400
    assert second.json()["detail"] == "Email already registered."


def test_vendor_register_duplicate_email_message(client):
    email = f"dup-vendor-{uuid4().hex[:8]}@test.com"
    payload = {"email": email, "password": "VendPass123!", "displayName": "Dup Vendor"}
    first = client.post("/api/v1/auth/vendor/register", json=payload)
    assert first.status_code == 201
    second = client.post("/api/v1/auth/vendor/register", json=payload)
    assert second.status_code == 400
    assert second.json()["detail"] == "Email already registered."


def test_admin_register_duplicate_email_message(client, monkeypatch):
    monkeypatch.setenv("DISABLE_ADMIN_REGISTER", "false")
    email = f"dup-admin-{uuid4().hex[:8]}@test.com"
    payload = {"email": email, "password": "AdminPass123!", "staff_role": "staff"}
    first = client.post("/api/v1/auth/admin/register", json=payload)
    if first.status_code == 403:
        return
    assert first.status_code == 201
    second = client.post("/api/v1/auth/admin/register", json=payload)
    assert second.status_code == 400
    assert second.json()["detail"] == "Email already registered."
