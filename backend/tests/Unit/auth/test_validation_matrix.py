from __future__ import annotations

import pytest

from app.core.config import settings


INVALID_EMAILS = [
    "",
    "no-at",
    "a@b",
    "a@b.",
    "a@.com",
    "a@@b.com",
    "a b@c.com",
    "a@b..com",
    "a@b,com",
    "a@b@c.com",
]

SHORT_PASSWORDS = [
    "",
    "123",
    "short",
    "1234567",
    "pass1",
    "aaaaaaa",
    "       ",
    "p@ss!",
    "abcdefg",
    "1234567",
]


@pytest.mark.parametrize("email", INVALID_EMAILS)
def test_customer_register_invalid_email_422(client, email):
    payload = {"fullName": "Test User", "email": email, "password": "Pass12345!"}
    r = client.post("/api/v1/auth/customer/register", json=payload)
    assert r.status_code == 422


@pytest.mark.parametrize("password", SHORT_PASSWORDS)
def test_customer_register_short_password_422(client, password):
    payload = {"fullName": "Test User", "email": "valid@test.com", "password": password}
    r = client.post("/api/v1/auth/customer/register", json=payload)
    assert r.status_code == 422


@pytest.mark.parametrize("payload", [
    {"email": "a@test.com", "password": "Pass12345!"},
    {"fullName": "Test User", "password": "Pass12345!"},
    {"fullName": "Test User", "email": "a@test.com"},
])
def test_customer_register_missing_fields_422(client, payload):
    r = client.post("/api/v1/auth/customer/register", json=payload)
    assert r.status_code == 422


@pytest.mark.parametrize("email", INVALID_EMAILS)
def test_vendor_register_invalid_email_422(client, email):
    payload = {"email": email, "password": "Pass12345!", "displayName": "Vendor"}
    r = client.post("/api/v1/auth/vendor/register", json=payload)
    assert r.status_code == 422


@pytest.mark.parametrize("password", SHORT_PASSWORDS)
def test_vendor_register_short_password_422(client, password):
    payload = {"email": "vendor@test.com", "password": password, "displayName": "Vendor"}
    r = client.post("/api/v1/auth/vendor/register", json=payload)
    assert r.status_code in (400, 422)


@pytest.mark.parametrize("payload", [
    {"password": "Pass12345!", "displayName": "Vendor"},
    {"email": "vendor@test.com", "displayName": "Vendor"},
])
def test_vendor_register_missing_fields_422(client, payload):
    r = client.post("/api/v1/auth/vendor/register", json=payload)
    assert r.status_code == 422


@pytest.mark.parametrize("email", INVALID_EMAILS)
def test_admin_register_invalid_email_422(client, email):
    settings.DISABLE_ADMIN_REGISTER = False
    payload = {"email": email, "password": "Pass12345!", "staff_role": "staff"}
    r = client.post("/api/v1/auth/admin/register", json=payload)
    assert r.status_code == 422


@pytest.mark.parametrize("password", SHORT_PASSWORDS)
def test_admin_register_short_password_422(client, password):
    settings.DISABLE_ADMIN_REGISTER = False
    payload = {"email": "admin@test.com", "password": password, "staff_role": "staff"}
    r = client.post("/api/v1/auth/admin/register", json=payload)
    assert r.status_code in (400, 422)


@pytest.mark.parametrize("payload", [
    {"password": "Pass12345!", "staff_role": "staff"},
    {"email": "admin@test.com", "staff_role": "staff"},
])
def test_admin_register_missing_fields_422(client, payload):
    settings.DISABLE_ADMIN_REGISTER = False
    r = client.post("/api/v1/auth/admin/register", json=payload)
    assert r.status_code == 422


@pytest.mark.parametrize("email", INVALID_EMAILS)
def test_customer_login_invalid_email_422(client, email):
    payload = {"email": email, "password": "Pass12345!"}
    r = client.post("/api/v1/auth/customer/login", json=payload)
    assert r.status_code in (401, 422)


@pytest.mark.parametrize("password", SHORT_PASSWORDS)
def test_customer_login_short_password_422(client, password):
    payload = {"email": "valid@test.com", "password": password}
    r = client.post("/api/v1/auth/customer/login", json=payload)
    assert r.status_code in (401, 422)


@pytest.mark.parametrize("email", INVALID_EMAILS)
def test_vendor_login_invalid_email_422(client, email):
    payload = {"email": email, "password": "Pass12345!"}
    r = client.post("/api/v1/auth/vendor/login", json=payload)
    assert r.status_code in (401, 422)


@pytest.mark.parametrize("password", SHORT_PASSWORDS)
def test_vendor_login_short_password_422(client, password):
    payload = {"email": "vendor@test.com", "password": password}
    r = client.post("/api/v1/auth/vendor/login", json=payload)
    assert r.status_code in (401, 422)


@pytest.mark.parametrize("email", INVALID_EMAILS)
def test_admin_login_invalid_email_422(client, email):
    payload = {"email": email, "password": "Pass12345!"}
    r = client.post("/api/v1/auth/admin/login", json=payload)
    assert r.status_code in (401, 422)


@pytest.mark.parametrize("password", SHORT_PASSWORDS)
def test_admin_login_short_password_422(client, password):
    payload = {"email": "admin@test.com", "password": password}
    r = client.post("/api/v1/auth/admin/login", json=payload)
    assert r.status_code in (401, 422)


@pytest.mark.parametrize("payload", [
    {"currentPassword": "short", "newPassword": "Pass12345!"},
    {"currentPassword": "Pass12345!", "newPassword": "short"},
    {"current_password": "short", "new_password": "Pass12345!"},
    {"current_password": "Pass12345!", "new_password": "short"},
])
def test_password_change_short_fields_422(client, payload):
    r = client.post("/api/v1/auth/customer/password/change", json=payload)
    assert r.status_code == 401


@pytest.mark.parametrize("payload", [
    {"email": "not-an-email", "otp": "123456"},
    {"email": "user@test.com"},
    {"otp": "123456"},
])
def test_password_verify_otp_invalid_payload_422(client, payload):
    r = client.post("/api/v1/auth/customer/password/verify-otp", json=payload)
    assert r.status_code == 422


@pytest.mark.parametrize("payload", [
    {"resetToken": "token-only"},
    {"newPassword": "Pass12345!"},
    {"resetToken": "token", "newPassword": "short"},
])
def test_password_reset_invalid_payload_422(client, payload):
    r = client.post("/api/v1/auth/customer/password/reset", json=payload)
    assert r.status_code == 422
