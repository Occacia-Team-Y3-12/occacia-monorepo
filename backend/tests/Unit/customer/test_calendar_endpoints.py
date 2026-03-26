from __future__ import annotations

from uuid import uuid4

from app.core.database import SessionLocal
from app.core.security import create_access_token, get_password_hash
from app.models.customer import Customer


def _create_customer() -> Customer:
    db = SessionLocal()
    customer = Customer(
        customer_id=f"CUS-{uuid4().hex[:16]}",
        full_name="Calendar Customer",
        email=f"calendar-{uuid4().hex[:8]}@test.com",
        password_hash=get_password_hash("Pass12345!"),
        phone="+94770000000",
        email_verified=True,
        status="ACTIVE",
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    db.close()
    return customer


def test_calendar_connect_and_status(client):
    customer = _create_customer()
    token = create_access_token({"sub": customer.email, "role": "CUSTOMER"})

    connect = client.post(
        "/api/v1/customers/calendar/connect",
        json={"provider": "GOOGLE", "redirectUri": "https://app.occacia.com/oauth/callback"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert connect.status_code == 200
    assert "authorizationUrl" in connect.json()

    status = client.get(
        "/api/v1/customers/calendar/status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert status.status_code == 200
    assert "connected" in status.json()


def test_calendar_connect_requires_auth(client):
    r = client.post(
        "/api/v1/customers/calendar/connect",
        json={"provider": "GOOGLE", "redirectUri": "https://app.occacia.com/oauth/callback"},
    )
    assert r.status_code == 401
