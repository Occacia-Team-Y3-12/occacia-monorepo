from uuid import uuid4

import jwt
import pytest

from app.core.database import SessionLocal, engine
from app.core.security import ALGORITHM, SECRET_KEY
from app.models.marketplace import Customer, Vendor


@pytest.fixture(autouse=True)
def prepare_customer_table():
    Customer.__table__.create(bind=engine, checkfirst=True)
    Vendor.__table__.create(bind=engine, checkfirst=True)
    db = SessionLocal()
    db.query(Customer).delete()
    db.query(Vendor).delete()
    db.commit()
    db.close()

    yield

    db = SessionLocal()
    db.query(Customer).delete()
    db.query(Vendor).delete()
    db.commit()
    db.close()


def test_customer_registration_and_email_verification_success(client):
    email = f"user-{uuid4().hex}@example.com"
    payload = {
        "full_name": "Jane Doe",
        "email": email,
        "password": "StrongPass123!",
        "phone": "+1-555-0100",
        "address": "123 Main St",
    }

    register_response = client.post("/api/v1/auth/register", json=payload)

    assert register_response.status_code == 201
    assert register_response.json()["message"] == "Verification email sent"
    assert register_response.json()["email"] == email

    db = SessionLocal()
    customer = db.query(Customer).filter(Customer.email == email).first()
    assert customer is not None
    assert customer.email_verified is False
    assert customer.status == "PENDING_VERIFICATION"
    assert customer.verification_token is not None
    token = customer.verification_token
    db.close()

    verify_response = client.get("/api/v1/auth/customers/verify-email", params={"token": token})

    assert verify_response.status_code == 200
    assert verify_response.json()["message"] == "Email verified successfully"

    db = SessionLocal()
    verified_customer = db.query(Customer).filter(Customer.email == email).first()
    assert verified_customer is not None
    assert verified_customer.email_verified is True
    assert verified_customer.status == "ACTIVE"
    assert verified_customer.verification_token is None
    db.close()


def test_customer_registration_rejects_duplicate_email(client):
    email = f"user-{uuid4().hex}@example.com"
    payload = {
        "full_name": "Jane Doe",
        "email": email,
        "password": "StrongPass123!",
    }

    first_response = client.post("/api/v1/auth/register", json=payload)
    second_response = client.post("/api/v1/auth/register", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 400
    assert second_response.json()["detail"] == "This email is already registered."


def test_customer_email_verification_rejects_invalid_token(client):
    response = client.get("/api/v1/auth/customers/verify-email", params={"token": "invalid-token"})

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid verification token."


def test_vendor_email_verification_success(client):
    email = f"vendor-{uuid4().hex}@example.com"
    payload = {
        "business_name": f"Vendor {uuid4().hex[:6]}",
        "email": email,
        "password": "StrongPass123!",
        "location_base": "Colombo",
        "phone": "+1-555-0200",
    }
    register_response = client.post("/api/v1/auth/vendors/register", json=payload)
    assert register_response.status_code == 201

    token = jwt.encode(
        {"sub": email, "type": "verify_vendor_email"},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    verify_response = client.get("/api/v1/auth/vendors/verify-email", params={"token": token})
    assert verify_response.status_code == 200
    assert verify_response.json()["message"] == "Email verified successfully"

    db = SessionLocal()
    vendor = db.query(Vendor).filter(Vendor.email == email).first()
    assert vendor is not None
    assert vendor.is_verified is True
    db.close()
