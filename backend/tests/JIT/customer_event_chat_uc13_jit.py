# ruff: noqa: S101

from app.core.database import SessionLocal
from app.models.customer import Customer
from app.models.event import Event
from app.models.task import Task


def test_whenCustomerCompletesEventChatFlow_chatScheduleRemindersAndConfirm_success(
    auth_client,
    active_customer,
    mock_google_calendar,
):
    create_response = auth_client.post(
        "/api/v1/customers/events",
        json={"eventType": "Birthday", "title": "Mom Birthday Dinner"},
    )

    assert create_response.status_code == 201
    event_id = create_response.json()["eventId"]

    chat_response = auth_client.post(
        f"/api/v1/customers/events/{event_id}/chat",
        json={"content": "It is on 2026-08-01 and I need reminders."},
    )

    assert chat_response.status_code == 200
    assert chat_response.json()["reply"]
    assert len(chat_response.json()["suggestedTasks"]) >= 1

    schedule_response = auth_client.put(
        f"/api/v1/customers/events/{event_id}/schedule",
        json={
            "startAt": "2026-08-01T18:00:00Z",
            "endAt": "2026-08-01T21:00:00Z",
            "timezone": "Asia/Colombo",
            "isAllDay": False,
            "recurrenceRule": "FREQ=YEARLY;INTERVAL=1;COUNT=2",
        },
    )

    assert schedule_response.status_code == 200
    assert schedule_response.json()["schedule"]["timezone"] == "Asia/Colombo"

    reminders_response = auth_client.put(
        f"/api/v1/customers/events/{event_id}/reminders",
        json={
            "enabled": True,
            "channels": ["PUSH", "IN_APP"],
            "offsets": ["P7D", "P1D"],
        },
    )

    assert reminders_response.status_code == 200
    assert reminders_response.json()["reminders"]["enabled"] is True

    connect_response = auth_client.post(
        "/api/v1/customers/calendar/connect",
        json={"provider": "GOOGLE", "redirectUri": "https://app.occacia.com/oauth/callback"},
    )

    assert connect_response.status_code == 200
    oauth_state = connect_response.json()["state"]

    exchange_response = auth_client.post(
        "/api/v1/customers/calendar/exchange-code",
        json={
            "provider": "GOOGLE",
            "code": "jit-mock-code",
            "state": oauth_state,
            "redirectUri": "https://app.occacia.com/oauth/callback",
        },
    )

    assert exchange_response.status_code == 200
    assert exchange_response.json()["connected"] is True

    task_response = auth_client.post(
        f"/api/v1/customers/events/{event_id}/tasks",
        json={"name": "Book venue", "description": "Reserve the restaurant", "quantity": 1},
    )

    assert task_response.status_code == 201
    task_id = task_response.json()["taskId"]

    sync_response = auth_client.put(
        f"/api/v1/customers/events/{event_id}/calendar-sync",
        json={"state": "ENABLED", "provider": "GOOGLE"},
    )

    assert sync_response.status_code == 200
    assert sync_response.json()["state"] == "ENABLED"

    confirm_response = auth_client.post(
        f"/api/v1/customers/events/{event_id}/tasks/confirm",
        json={"taskIds": [task_id]},
    )

    assert confirm_response.status_code == 200
    assert confirm_response.json()["event"]["status"] == "ACTIVE"
    assert confirm_response.json()["tasks"][0]["status"] == "PENDING"

    summary_response = auth_client.post(f"/api/v1/customers/events/{event_id}/summarize")

    assert summary_response.status_code == 200
    assert "Next occurrence" in summary_response.json()["summary"]

    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.customer_id == active_customer.customer_id).first()
        event = db.query(Event).filter(Event.event_id == event_id).first()
        task = db.query(Task).filter(Task.event_id == event_id).first()
    finally:
        db.close()

    assert customer is not None
    assert customer.calendar_provider == "GOOGLE"
    assert event is not None
    assert event.status == "ACTIVE"
    assert event.reminders_enabled is True
    assert event.calendar_sync_state == "ENABLED"
    assert event.external_calendar_event_id is not None
    assert task is not None
    assert task.status == "PENDING"
