# ruff: noqa: S101

from uuid import uuid4

from app.core.database import SessionLocal
from app.core.security import create_refresh_token
from app.models.customer import Customer


def _get_customer(email: str) -> Customer | None:
    db = SessionLocal()
    try:
        return db.query(Customer).filter(Customer.email == email).first()
    finally:
        db.close()


def _set_customer_state(email: str, *, email_verified: bool, status: str) -> None:
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.email == email).first()
        assert customer is not None
        customer.email_verified = email_verified
        customer.status = status
        db.commit()
    finally:
        db.close()


def test_whenCustomerRegistersAndVerifies_loginAndRefresh_success(client):
    email = f"jit-customer-{uuid4().hex[:8]}@test.com"

    register_response = client.post(
        "/api/v1/auth/customer/register",
        json={
            "full_name": "JIT Customer",
            "email": email,
            "password": "Pass123!",
            "phone": "+94770000000",
        },
    )

    assert register_response.status_code == 201

    customer = _get_customer(email)
    assert customer is not None
    assert customer.verification_token is not None
    assert customer.status == "PENDING"

    verify_response = client.get(
        "/api/v1/auth/customer/verify-email",
        params={"token": customer.verification_token},
        headers={"Accept": "application/json"},
    )

    assert verify_response.status_code == 200

    verified_customer = _get_customer(email)
    assert verified_customer is not None
    assert verified_customer.email_verified is True
    assert verified_customer.status == "ACTIVE"

    login_response = client.post(
        "/api/v1/auth/customer/login",
        json={"email": email, "password": "Pass123!"},
    )

    assert login_response.status_code == 200
    login_body = login_response.json()
    assert "accessToken" in login_body
    assert "refreshToken" in login_body
    assert login_body["user"]["email"] == email
    assert login_body["user"]["status"] == "ACTIVE"
    assert login_body["user"]["role"] == "CUSTOMER"

    refresh_response = client.post(
        "/api/v1/auth/customer/token/refresh",
        json={"refreshToken": login_body["refreshToken"]},
    )

    assert refresh_response.status_code == 200
    refresh_body = refresh_response.json()
    assert "accessToken" in refresh_body
    assert "refreshToken" in refresh_body
    assert refresh_body["user"]["email"] == email


def test_whenCustomerIsSuspended_login_failsWithException(client):
    email = f"jit-inactive-{uuid4().hex[:8]}@test.com"

    register_response = client.post(
        "/api/v1/auth/customer/register",
        json={
            "full_name": "Inactive Customer",
            "email": email,
            "password": "Pass123!",
        },
    )

    assert register_response.status_code == 201

    _set_customer_state(email, email_verified=True, status="SUSPENDED")

    login_response = client.post(
        "/api/v1/auth/customer/login",
        json={"email": email, "password": "Pass123!"},
    )

    assert login_response.status_code == 403
    assert login_response.json()["detail"] == "Customer account is not active."


def test_whenCustomerIsDisabled_refreshToken_failsWithException(client):
    email = f"jit-refresh-{uuid4().hex[:8]}@test.com"

    register_response = client.post(
        "/api/v1/auth/customer/register",
        json={
            "full_name": "Refresh Customer",
            "email": email,
            "password": "Pass123!",
        },
    )

    assert register_response.status_code == 201

    customer = _get_customer(email)
    assert customer is not None

    verify_response = client.get(
        "/api/v1/auth/customer/verify-email",
        params={"token": customer.verification_token},
        headers={"Accept": "application/json"},
    )

    assert verify_response.status_code == 200

    _set_customer_state(email, email_verified=True, status="DISABLED")
    refresh_token = create_refresh_token({"sub": email, "role": "CUSTOMER"})

    refresh_response = client.post(
        "/api/v1/auth/customer/token/refresh",
        json={"refreshToken": refresh_token},
    )

    assert refresh_response.status_code == 401
