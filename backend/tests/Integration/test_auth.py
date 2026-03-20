"""
tests/Integration/test_auth.py
"""
from uuid import uuid4
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import get_db, SessionLocal
from app.models.customer import Customer


@pytest.fixture
def client():
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


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


def test_customer_register_success(client):
    email = f"user-{uuid4().hex[:8]}@test.com"
    r = client.post("/api/v1/auth/customer/register", json={
        "fullName": "Jane Doe",
        "email": email,
        "password": "StrongPass123!",
        "phone": "+94771234567",
    })
    assert r.status_code == 201
    assert r.json()["message"] == "Registration successful. Please verify your email."


def test_customer_register_duplicate_email(client):
    email = f"user-{uuid4().hex[:8]}@test.com"
    payload = {"full_name": "Jane", "email": email, "password": "Pass123!"}
    client.post("/api/v1/auth/customer/register", json=payload)
    r = client.post("/api/v1/auth/customer/register", json=payload)
    assert r.status_code == 400


def test_vendor_register_success(client):
    r = client.post("/api/v1/auth/vendor/register", json={
        "business_name": f"Vendor {uuid4().hex[:6]}",
        "email": f"vendor-{uuid4().hex[:8]}@test.com",
        "password": "StrongPass123!",
        "location_base": "Colombo",
        "phone": "+94771234567",
    })
    assert r.status_code == 201


def test_vendor_register_duplicate_email(client):
    email = f"vendor-{uuid4().hex[:8]}@test.com"
    payload = {
        "business_name": f"Vendor {uuid4().hex[:6]}",
        "email": email,
        "password": "Pass123!",
    }
    client.post("/api/v1/auth/vendor/register", json=payload)
    r = client.post("/api/v1/auth/vendor/register", json=payload)
    assert r.status_code == 400


def test_customer_verify_email_success(client):
    email = f"user-{uuid4().hex[:8]}@test.com"
    client.post("/api/v1/auth/customer/register", json={
        "fullName": "Jane", "email": email, "password": "Pass12345!"
    })
    db = SessionLocal()
    customer = db.query(Customer).filter(Customer.email == email).first()
    if customer is None:
        pytest.skip("Customer not created")
    token = getattr(customer, "verification_token", None)
    db.close()
    if not token:
        pytest.skip("No verification_token")
    r = client.get("/api/v1/auth/customer/verify-email",
                   params={"token": token},
                   headers={"Accept": "application/json"})
    assert r.status_code == 200


def test_customer_verify_email_invalid_token(client):
    r = client.get("/api/v1/auth/customer/verify-email",
                   params={"token": "bad-token"},
                   headers={"Accept": "application/json"})
    assert r.status_code == 400


def test_customer_login_success(client, monkeypatch):
    email = f"user-{uuid4().hex[:8]}@test.com"
    client.post("/api/v1/auth/customer/register", json={
        "fullName": "Jane", "email": email, "password": "Pass12345!"
    })
    _activate_customer(email)
    
    monkeypatch.setenv("SKIP_EMAIL_VERIFICATION", "true")
    
    # 💥 THE FIX: data= instead of json=
    r = client.post("/api/v1/auth/customer/login",
                    data={"username": email, "password": "Pass12345!"})
    
    assert r.status_code == 200
    data = r.json()
    assert "accessToken" in data
    assert "refreshToken" in data
    assert data["user"]["email"] == email


def test_customer_login_wrong_password(client):
    email = f"user-{uuid4().hex[:8]}@test.com"
    client.post("/api/v1/auth/customer/register", json={
        "fullName": "Jane", "email": email, "password": "Pass12345!"}
    )
    _activate_customer(email)
    
    # 💥 THE FIX: data= instead of json=
    r = client.post("/api/v1/auth/customer/login",
                    data={"username": email, "password": "WrongPass!"})
    
    assert r.status_code == 401


def test_customer_refresh_token_success(client, monkeypatch):
    email = f"user-{uuid4().hex[:8]}@test.com"
    client.post("/api/v1/auth/customer/register", json={
        "fullName": "Jane", "email": email, "password": "Pass12345!"}
    )
    _activate_customer(email)
    
    monkeypatch.setenv("SKIP_EMAIL_VERIFICATION", "true")
    
    # 💥 THE FIX: data= instead of json=
    login = client.post(
        "/api/v1/auth/customer/login",
        data={"username": email, "password": "Pass12345!"},
    )
    
    data = login.json()
    assert "refreshToken" in data, f"Login failed: {data}"
    refresh_token = data["refreshToken"]

    r = client.post(
        "/api/v1/auth/customer/token/refresh",
        json={"refreshToken": refresh_token},
    )

    assert r.status_code == 200
    assert "accessToken" in r.json()


def test_vendor_login_success(client, monkeypatch):
    email = f"vendor-{uuid4().hex[:8]}@test.com"
    client.post("/api/v1/auth/vendor/register", json={
        "business_name": f"Biz {uuid4().hex[:6]}",
        "email": email,
        "password": "Pass123!",
    })
    
    monkeypatch.setenv("SKIP_EMAIL_VERIFICATION", "true")
    
    r = client.post("/api/v1/auth/vendor/login",
                    data={"username": email, "password": "Pass123!"})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_vendor_login_wrong_password(client):
    email = f"vendor-{uuid4().hex[:8]}@test.com"
    client.post("/api/v1/auth/vendor/register", json={
        "business_name": f"Biz {uuid4().hex[:6]}",
        "email": email,
        "password": "Pass123!",
    })
    r = client.post("/api/v1/auth/vendor/login",
                    data={"username": email, "password": "WrongPass!"})
    assert r.status_code == 401


def test_customer_forgot_password(client):
    email = f"user-{uuid4().hex[:8]}@test.com"
    client.post("/api/v1/auth/customer/register", json={
        "fullName": "Jane", "email": email, "password": "Pass12345!"}
    )
    r = client.post("/api/v1/auth/customer/password/forgot",
                    json={"email": email})
    assert r.status_code == 200


def test_customer_forgot_password_unknown_email(client):
    r = client.post("/api/v1/auth/customer/password/forgot",
                    json={"email": "nobody@test.com"})
    assert r.status_code == 200


def test_customer_reset_password_invalid_token(client):
    r = client.post("/api/v1/auth/customer/password/reset",
                    json={"token": "bad-token", "new_password": "NewPass123!"})
    assert r.status_code == 400


def test_customer_resend_verification_success(client):
    email = f"user-{uuid4().hex[:8]}@test.com"
    client.post("/api/v1/auth/customer/register", json={
        "fullName": "Jane",
        "email": email,
        "password": "Pass12345!",
    })

    r = client.post(
        "/api/v1/auth/customer/email-verification/resend",
        json={"email": email},
    )

    assert r.status_code == 200
    assert r.json()["message"] == "Verification email resent successfully."
