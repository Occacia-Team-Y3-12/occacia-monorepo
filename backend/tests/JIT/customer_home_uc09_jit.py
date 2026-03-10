# ruff: noqa: S101

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.core.database import SessionLocal
from app.models.customer import Customer
from app.models.event import Event
from app.models.event_persona import EventPersona


def test_whenCustomerRequestsOwnProfile_getCustomersMe_success(auth_client, active_customer):
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


def test_whenCustomerUpdatesOwnProfile_putCustomersMe_success(auth_client, active_customer):
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
        refreshed_customer = (
            db.query(Customer)
            .filter(Customer.customer_id == active_customer.customer_id)
            .first()
        )
    finally:
        db.close()

    assert refreshed_customer is not None
    assert refreshed_customer.full_name == "Updated Customer"
    assert refreshed_customer.phone == "+94112223344"
    assert refreshed_customer.locale == "en-LK"


def test_whenCustomerRequestsEvents_getCustomersEvents_success(auth_client, active_customer):
    now = datetime.now(UTC)
    db = SessionLocal()
    try:
        newest_event = Event(
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
        older_event = Event(
            event_id=f"EVT-{uuid4().hex[:8]}",
            customer_id=active_customer.customer_id,
            event_type="Shopping",
            title="Shopping trip",
            status="DRAFT",
            created_at=now,
            updated_at=now,
        )
        db.add_all([newest_event, older_event])
        db.flush()
        db.add(EventPersona(event_id=newest_event.event_id, persona_id="PER-001"))
        db.commit()
        db.refresh(newest_event)
        db.refresh(older_event)
    finally:
        db.close()

    first_page_response = auth_client.get("/api/v1/customers/events", params={"limit": 1})

    assert first_page_response.status_code == 200
    first_page_body = first_page_response.json()
    assert first_page_body["nextCursor"] == newest_event.event_id
    assert len(first_page_body["items"]) == 1
    assert first_page_body["items"][0]["eventId"] == newest_event.event_id
    assert first_page_body["items"][0]["personaIds"] == ["PER-001"]

    second_page_response = auth_client.get(
        "/api/v1/customers/events",
        params={"limit": 1, "cursor": first_page_body["nextCursor"]},
    )

    assert second_page_response.status_code == 200
    assert second_page_response.json()["items"][0]["eventId"] == older_event.event_id
    assert second_page_response.json()["nextCursor"] is None


def test_whenCustomerRequestsQuickStartTemplates_getEventTemplates_success(auth_client):
    response = auth_client.get("/api/v1/event-templates")

    assert response.status_code == 200
    assert response.json() == {
        "items": ["Birthday", "Family Gathering", "Shopping"]
    }


def test_whenUnauthenticatedUserRequestsCustomerHome_getCustomersMe_failsWithException(client):
    response = client.get("/api/v1/customers/me")

    assert response.status_code == 401
