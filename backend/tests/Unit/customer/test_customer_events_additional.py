from __future__ import annotations

from uuid import uuid4

from app.core.database import SessionLocal
from app.core.security import create_access_token, get_password_hash
from app.models.customer import Customer
from app.models.event import Event


def _create_customer() -> Customer:
    db = SessionLocal()
    customer = Customer(
        customer_id=f"CUS-{uuid4().hex[:16]}",
        full_name="Events Customer",
        email=f"events-{uuid4().hex[:8]}@test.com",
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


def test_create_event_requires_auth(client):
    r = client.post("/api/v1/customers/events", json={"eventType": "WEDDING", "title": "Test"})
    assert r.status_code == 401


def test_create_and_delete_draft_event(client):
    customer = _create_customer()
    token = create_access_token({"sub": customer.email, "role": "CUSTOMER"})
    created = client.post(
        "/api/v1/customers/events",
        json={"eventType": "WEDDING", "title": "Test Event"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert created.status_code == 201
    event_id = created.json()["eventId"]
    deleted = client.delete(
        f"/api/v1/customers/events/{event_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert deleted.status_code == 204


def test_delete_non_draft_event_returns_409(client):
    customer = _create_customer()
    token = create_access_token({"sub": customer.email, "role": "CUSTOMER"})
    db = SessionLocal()
    event = Event(
        customer_id=customer.customer_id,
        event_type="BIRTHDAY",
        title="Active Event",
        status="ACTIVE",
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    db.close()

    r = client.delete(
        f"/api/v1/customers/events/{event.event_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 409
