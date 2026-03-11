from __future__ import annotations

from app.core.database import SessionLocal
from app.models.customer import Customer
from app.models.event import Event


def _create_event(auth_client, title: str = "Birthday Dinner") -> str:
    response = auth_client.post(
        "/api/v1/customers/events",
        json={"eventType": "Birthday", "title": title},
    )
    assert response.status_code == 201, response.text
    return response.json()["eventId"]


def test_whenCustomerSendsEventChatMessage_postEventChat_success(auth_client):
    event_id = _create_event(auth_client)

    response = auth_client.post(
        f"/api/v1/customers/events/{event_id}/chat",
        json={"content": "I want to plan this with reminders."},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["reply"]
    assert len(body["suggestedTasks"]) >= 1

    messages = auth_client.get(f"/api/v1/customers/events/{event_id}/messages")
    assert messages.status_code == 200
    assert [item["sender"] for item in messages.json()["items"]] == ["CUSTOMER", "AI"]


def test_whenCustomerUpdatesRecurringSchedule_getOccurrences_success(auth_client):
    event_id = _create_event(auth_client, title="Annual Birthday")

    response = auth_client.put(
        f"/api/v1/customers/events/{event_id}/schedule",
        json={
            "startAt": "2026-06-10T12:00:00Z",
            "endAt": "2026-06-10T15:00:00Z",
            "timezone": "Asia/Colombo",
            "isAllDay": False,
            "recurrenceRule": "FREQ=YEARLY;INTERVAL=1;COUNT=3",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["schedule"]["timezone"] == "Asia/Colombo"
    assert body["nextOccurrence"]["startAt"].startswith("2026-06-10T12:00:00")

    occurrences = auth_client.get(
        f"/api/v1/customers/events/{event_id}/occurrences",
        params={"from": "2026-01-01T00:00:00Z", "limit": 2},
    )
    assert occurrences.status_code == 200, occurrences.text
    occurrence_items = occurrences.json()["items"]
    assert len(occurrence_items) == 2
    assert occurrence_items[0]["startAt"].startswith("2026-06-10T12:00:00")
    assert occurrence_items[1]["startAt"].startswith("2027-06-10T12:00:00")


def test_whenCustomerUpdatesReminders_putEventReminders_success(auth_client):
    event_id = _create_event(auth_client)

    schedule = auth_client.put(
        f"/api/v1/customers/events/{event_id}/schedule",
        json={
            "startAt": "2026-07-12T09:00:00Z",
            "timezone": "Asia/Colombo",
            "isAllDay": False,
        },
    )
    assert schedule.status_code == 200

    response = auth_client.put(
        f"/api/v1/customers/events/{event_id}/reminders",
        json={
            "enabled": True,
            "channels": ["PUSH", "EMAIL"],
            "offsets": ["P7D", "P1D", "PT0M"],
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["reminders"]["enabled"] is True
    assert body["reminders"]["channels"] == ["PUSH", "EMAIL"]


def test_whenCustomerConfirmsWithoutTasks_postConfirmTasks_failsWithException(auth_client):
    event_id = _create_event(auth_client)

    response = auth_client.post(f"/api/v1/customers/events/{event_id}/tasks/confirm")

    assert response.status_code == 400
    assert response.json()["detail"] == "Add at least 1 task"


def test_whenCustomerConfirmsTasks_postConfirmTasks_activatesEvent(auth_client):
    event_id = _create_event(auth_client)

    created_task = auth_client.post(
        f"/api/v1/customers/events/{event_id}/tasks",
        json={"name": "Book venue", "quantity": 1},
    )
    assert created_task.status_code == 201, created_task.text

    response = auth_client.post(f"/api/v1/customers/events/{event_id}/tasks/confirm")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["event"]["status"] == "ACTIVE"
    assert body["tasks"][0]["status"] == "PENDING"


def test_whenCustomerConnectsCalendarAndEnablesSync_putEventCalendarSync_success(auth_client, active_customer):
    event_id = _create_event(auth_client)

    connect = auth_client.post(
        "/api/v1/customers/calendar/connect",
        json={"provider": "GOOGLE", "redirectUri": "https://app.occacia.com/oauth/callback"},
    )
    assert connect.status_code == 200, connect.text
    state = connect.json()["state"]

    exchange = auth_client.post(
        "/api/v1/customers/calendar/exchange-code",
        json={
            "provider": "GOOGLE",
            "code": "mock-code",
            "state": state,
            "redirectUri": "https://app.occacia.com/oauth/callback",
        },
    )
    assert exchange.status_code == 200, exchange.text
    assert exchange.json()["connected"] is True
    assert exchange.json()["provider"] == "GOOGLE"

    schedule = auth_client.put(
        f"/api/v1/customers/events/{event_id}/schedule",
        json={
            "startAt": "2026-08-01T18:00:00Z",
            "timezone": "Asia/Colombo",
            "isAllDay": False,
        },
    )
    assert schedule.status_code == 200

    sync = auth_client.put(
        f"/api/v1/customers/events/{event_id}/calendar-sync",
        json={"state": "ENABLED", "provider": "GOOGLE"},
    )
    assert sync.status_code == 200, sync.text
    sync_body = sync.json()
    assert sync_body["state"] == "ENABLED"
    assert sync_body["provider"] == "GOOGLE"
    assert sync_body["externalEventId"]

    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.customer_id == active_customer.customer_id).first()
        event = db.query(Event).filter(Event.event_id == event_id).first()
        assert customer is not None and customer.calendar_provider == "GOOGLE"
        assert event is not None and event.calendar_sync_state == "ENABLED"
    finally:
        db.close()


def test_whenCustomerProvidesInvalidRecurrence_putEventSchedule_failsWithException(auth_client):
    event_id = _create_event(auth_client, title="Recurring Event")

    response = auth_client.put(
        f"/api/v1/customers/events/{event_id}/schedule",
        json={
            "startAt": "2026-06-10T12:00:00Z",
            "timezone": "Asia/Colombo",
            "isAllDay": False,
            "recurrenceRule": "FREQ=INVALID;INTERVAL=1",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported recurrence frequency"
