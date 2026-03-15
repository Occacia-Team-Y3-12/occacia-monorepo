# ruff: noqa: S101

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.core.database import SessionLocal
from app.models.customer import Customer
from app.models.event import Event
from app.models.event_persona import EventPersona
from app.models.persona import Persona


def test_get_customer_profile_returns_authenticated_customer(auth_client, active_customer):
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


def test_update_customer_profile_persists_changes(auth_client, active_customer):
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


def test_list_customer_events_returns_paginated_customer_events(auth_client, active_customer):
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


def test_list_event_templates_returns_quick_start_options(auth_client):
    response = auth_client.get("/api/v1/event-templates")

    assert response.status_code == 200
    assert response.json() == {
        "items": ["Birthday", "Family Gathering", "Shopping"]
    }


def test_list_event_types_returns_uc12_event_types(auth_client):
    response = auth_client.get("/api/v1/event-types")

    assert response.status_code == 200
    assert response.json() == {
        "items": ["Individual", "Group", "Others"]
    }


def test_create_customer_event_creates_draft_and_links_personas(auth_client, active_customer):
    db = SessionLocal()
    try:
        persona = Persona(
            persona_id=f"PER-{uuid4().hex[:8]}",
            customer_id=active_customer.customer_id,
            name="Mom",
        )
        db.add(persona)
        db.commit()
        db.refresh(persona)
    finally:
        db.close()

    response = auth_client.post(
        "/api/v1/customers/events",
        json={
            "eventType": "Individual",
            "title": "Visiting to see sick mom",
            "personaIds": [persona.persona_id],
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "DRAFT"
    assert body["eventId"].startswith("EVT-")

    db = SessionLocal()
    try:
        saved_event = db.query(Event).filter(Event.event_id == body["eventId"]).first()
        saved_links = (
            db.query(EventPersona)
            .filter(EventPersona.event_id == body["eventId"])
            .all()
        )
    finally:
        db.close()

    assert saved_event is not None
    assert saved_event.customer_id == active_customer.customer_id
    assert saved_event.event_type == "Individual"
    assert saved_event.title == "Visiting to see sick mom"
    assert saved_event.status == "DRAFT"
    assert [link.persona_id for link in saved_links] == [persona.persona_id]


def test_create_customer_event_rejects_short_title(auth_client):
    response = auth_client.post(
        "/api/v1/customers/events",
        json={
            "eventType": "Individual",
            "title": "Hi",
        },
    )

    assert response.status_code == 422


def test_set_event_personas_replaces_existing_links(auth_client, active_customer):
    db = SessionLocal()
    try:
        event = Event(
            event_id=f"EVT-{uuid4().hex[:8]}",
            customer_id=active_customer.customer_id,
            event_type="Group",
            title="Family dinner planning",
            status="DRAFT",
        )
        old_persona = Persona(
            persona_id=f"PER-{uuid4().hex[:8]}",
            customer_id=active_customer.customer_id,
            name="Old Persona",
        )
        new_persona = Persona(
            persona_id=f"PER-{uuid4().hex[:8]}",
            customer_id=active_customer.customer_id,
            name="New Persona",
        )
        db.add_all([event, old_persona, new_persona])
        db.flush()
        db.add(EventPersona(event_id=event.event_id, persona_id=old_persona.persona_id))
        db.commit()
        db.refresh(event)
        db.refresh(new_persona)
    finally:
        db.close()

    response = auth_client.put(
        f"/api/v1/customers/events/{event.event_id}/personas",
        json={"personaIds": [new_persona.persona_id]},
    )

    assert response.status_code == 200
    assert response.json()["personaIds"] == [new_persona.persona_id]

    db = SessionLocal()
    try:
        saved_links = (
            db.query(EventPersona)
            .filter(EventPersona.event_id == event.event_id)
            .all()
        )
    finally:
        db.close()

    assert [link.persona_id for link in saved_links] == [new_persona.persona_id]


def test_delete_customer_event_removes_draft_event_and_links(auth_client, active_customer):
    db = SessionLocal()
    try:
        event = Event(
            event_id=f"EVT-{uuid4().hex[:8]}",
            customer_id=active_customer.customer_id,
            event_type="Others",
            title="Doctor appointment",
            status="DRAFT",
        )
        persona = Persona(
            persona_id=f"PER-{uuid4().hex[:8]}",
            customer_id=active_customer.customer_id,
            name="Dad",
        )
        db.add_all([event, persona])
        db.flush()
        db.add(EventPersona(event_id=event.event_id, persona_id=persona.persona_id))
        db.commit()
        db.refresh(event)
    finally:
        db.close()

    response = auth_client.delete(f"/api/v1/customers/events/{event.event_id}")

    assert response.status_code == 204

    db = SessionLocal()
    try:
        saved_event = db.query(Event).filter(Event.event_id == event.event_id).first()
        saved_links = (
            db.query(EventPersona)
            .filter(EventPersona.event_id == event.event_id)
            .all()
        )
    finally:
        db.close()

    assert saved_event is None
    assert saved_links == []
