from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.core.database import SessionLocal
from app.core.security import create_access_token
from app.models.customer import Customer
from app.models.event import Event


def _create_customer_and_event():
    db = SessionLocal()
    customer = Customer(
        customer_id=f"CUS-{uuid4().hex[:16]}",
        full_name="Chat Customer",
        email=f"chat-customer-{uuid4().hex[:8]}@test.com",
        password_hash="hashed",
        email_verified=True,
        status="ACTIVE",
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)

    event = Event(
        event_id=f"EVT-{uuid4().hex[:16]}",
        customer_id=customer.customer_id,
        event_type="BIRTHDAY",
        title="Integration Chat Event",
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    email = customer.email
    event_id = event.event_id
    db.close()
    return email, event_id


def test_customer_event_chat_integration(client):
    email, event_id = _create_customer_and_event()
    access = create_access_token({"sub": email})
    client.headers.update({"Authorization": f"Bearer {access}"})

    ai_payload = {
        "reply": "Sounds great! Let us plan it.",
        "intent": "chat",
        "suggestedTasks": [],
        "missingInfo": [],
        "save_persona": False,
    }

    with patch(
        "app.services.groq_ai_service.groq_ai_service.plan_event_chat",
        new=AsyncMock(return_value=ai_payload),
    ):
        response = client.post(
            f"/api/v1/customers/events/{event_id}/chat",
            json={"content": "We are planning a birthday"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["reply"] == ai_payload["reply"]
