# ruff: noqa: S101

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.core.database import SessionLocal
from app.models.customer import Customer
from app.models.event import Event
from app.models.event_persona import EventPersona


def test_get_customer_profile(auth_client, active_customer):
    response = auth_client.get("/api/v1/customers/me")

    assert response.status_code == 200
    assert response.json() == {
        "customerId": active_customer.customer_id,
        "email": active_customer.email,
        "fullName": active_customer.full_name,
        "phone": active_customer.phone,
        "locale": active_customer.locale,
        "status": active_customer.status,
    }


def test_update_customer_profile(auth_client, active_customer):
    response = auth_client.put(
        "/api/v1/customers/me",
        json={
            "fullName": "Updated Customer",
            "phone": "+94112223344",
            "locale": "en-LK",
        },
    )

    assert response.status_code == 200
    assert response.json()["fullName"] == "Updated Customer"
    assert response.json()["phone"] == "+94112223344"
    assert response.json()["locale"] == "en-LK"

    db = SessionLocal()
    try:
        refreshed = (
            db.query(Customer)
            .filter(Customer.customer_id == active_customer.customer_id)
            .first()
        )
    finally:
        db.close()

    assert refreshed is not None
    assert refreshed.full_name == "Updated Customer"
    assert refreshed.phone == "+94112223344"
    assert refreshed.locale == "en-LK"


def test_list_customer_events_returns_paginated_events(auth_client, active_customer):
    now = datetime.now(UTC)
    db = SessionLocal()
    try:
        later_event = Event(
            event_id=f"EVT-{uuid4().hex[:8]}",
            customer_id=active_customer.customer_id,
            event_type="Birthday",
            title="Birthday dinner",
            description="Family dinner",
            location_text="Colombo",
            start_at=now + timedelta(days=10),
            end_at=now + timedelta(days=10, hours=4),
            status="ACTIVE",
            created_at=now + timedelta(minutes=5),
            updated_at=now + timedelta(minutes=5),
        )
        earlier_event = Event(
            event_id=f"EVT-{uuid4().hex[:8]}",
            customer_id=active_customer.customer_id,
            event_type="Shopping",
            title="Shopping trip",
            status="DRAFT",
            created_at=now,
            updated_at=now,
        )
        db.add_all([later_event, earlier_event])
        db.flush()
        db.add(EventPersona(event_id=later_event.event_id, persona_id="PER-001"))
        db.commit()
        db.refresh(later_event)
        db.refresh(earlier_event)
    finally:
        db.close()

    response = auth_client.get("/api/v1/customers/events", params={"limit": 1})

    assert response.status_code == 200
    payload = response.json()
    assert payload["nextCursor"] == later_event.event_id
    assert len(payload["items"]) == 1
    assert payload["items"][0]["eventId"] == later_event.event_id
    assert payload["items"][0]["personaIds"] == ["PER-001"]

    next_page = auth_client.get(
        "/api/v1/customers/events",
        params={"limit": 1, "cursor": payload["nextCursor"]},
    )

    assert next_page.status_code == 200
    assert next_page.json()["items"][0]["eventId"] == earlier_event.event_id
    assert next_page.json()["nextCursor"] is None


def test_list_customer_events_filters_by_status(auth_client, active_customer):
    now = datetime.now(UTC)
    db = SessionLocal()
    try:
        db.add_all(
            [
                Event(
                    event_id=f"EVT-{uuid4().hex[:8]}",
                    customer_id=active_customer.customer_id,
                    event_type="Birthday",
                    title="Active event",
                    status="ACTIVE",
                    created_at=now + timedelta(minutes=1),
                    updated_at=now + timedelta(minutes=1),
                ),
                Event(
                    event_id=f"EVT-{uuid4().hex[:8]}",
                    customer_id=active_customer.customer_id,
                    event_type="Shopping",
                    title="Draft event",
                    status="DRAFT",
                    created_at=now,
                    updated_at=now,
                ),
            ]
        )
        db.commit()
    finally:
        db.close()

    response = auth_client.get("/api/v1/customers/events", params={"status": "ACTIVE"})

    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["status"] == "ACTIVE"


def test_list_event_templates(auth_client):
    response = auth_client.get("/api/v1/event-templates")

    assert response.status_code == 200
    assert response.json() == {
        "items": ["Birthday", "Family Gathering", "Shopping"]
    }
