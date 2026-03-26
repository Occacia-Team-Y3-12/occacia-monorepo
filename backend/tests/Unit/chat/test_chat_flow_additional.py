from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

from app.core.database import SessionLocal
from app.core.security import create_access_token, get_password_hash
from app.models.customer import Customer
from app.models.event import Event


def _create_customer() -> Customer:
    db = SessionLocal()
    customer = Customer(
        customer_id=f"CUS-{uuid4().hex[:16]}",
        full_name="Chat Customer",
        email=f"chat-{uuid4().hex[:8]}@test.com",
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


def _create_event(customer_id: str) -> Event:
    db = SessionLocal()
    event = Event(
        customer_id=customer_id,
        event_type="BIRTHDAY",
        title="Chat Event",
        status="DRAFT",
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    db.close()
    return event


def test_chat_flow_returns_stubbed_response(client):
    customer = _create_customer()
    event = _create_event(customer.customer_id)
    token = create_access_token({"sub": customer.email, "role": "CUSTOMER"})
    with patch("app.services.event_chat_service.event_chat_service.send_message") as mock_send:
        mock_send.return_value = {"reply": "Hello!", "suggestedTasks": []}
        r = client.post(
            f"/api/v1/customers/events/{event.event_id}/chat",
            json={"content": "Hi"},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert r.status_code == 200
    body = r.json()
    assert body["reply"] == "Hello!"
