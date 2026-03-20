from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.security import ALGORITHM, SECRET_KEY, get_password_hash
from app.main import app
from app.models.admin import Admin
from app.models.customer import Customer
from app.models.event import Event
from app.models.notification import Notification
from app.models.task import Task


def _create_event_with_task(customer: Customer) -> tuple[str, str]:
    db = SessionLocal()
    try:
        event = Event(
            customer_id=customer.customer_id,
            event_type="birthday",
            title="Birthday Plan",
            status="DRAFT",
        )
        db.add(event)
        db.flush()

        task = Task(
            event_id=event.event_id,
            name="Cake",
            description="Book the cake",
            currency="LKR",
            status="DRAFT",
        )
        db.add(task)
        db.commit()
        db.refresh(event)
        db.refresh(task)
        return event.event_id, task.task_id
    finally:
        db.close()


def _admin_headers() -> dict[str, str]:
    db = SessionLocal()
    try:
        admin = Admin(
            email="admin-notify@test.com",
            password_hash=get_password_hash("Admin123!"),
            staff_role="staff",
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        token = jwt.encode(
            {
                "sub": admin.admin_id,
                "type": "admin",
                "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            },
            SECRET_KEY,
            algorithm=ALGORITHM,
        )
        return {"Authorization": f"Bearer {token}"}
    finally:
        db.close()


def test_task_confirmed_notifications_are_logged_once_within_dedupe_window(auth_client, active_customer, monkeypatch):
    event_id, task_id = _create_event_with_task(active_customer)
    send_calls: list[tuple[str, str, str]] = []

    def fake_send_email(to: str, subject: str, body: str) -> bool:
        send_calls.append((to, subject, body))
        return True

    monkeypatch.setattr("app.services.auth_service._send_email", fake_send_email)

    first_response = auth_client.post(f"/api/v1/customers/events/{event_id}/tasks/confirm")
    second_response = auth_client.post(f"/api/v1/customers/events/{event_id}/tasks/confirm")

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert len(send_calls) == 1

    db = SessionLocal()
    try:
        notifications = db.query(Notification).all()
        assert len(notifications) == 1
        notification = notifications[0]
        assert notification.user_id == active_customer.customer_id
        assert notification.event_id == event_id
        assert notification.task_id == task_id
        assert notification.type == "TASK_CONFIRMED"
        assert notification.status == "SENT"
        assert notification.sent_at is not None
        assert notification.payload["taskId"] == task_id
        assert notification.payload["eventId"] == event_id
    finally:
        db.close()


def test_admin_can_query_notification_history(auth_client, active_customer, monkeypatch):
    event_id, task_id = _create_event_with_task(active_customer)
    monkeypatch.setattr("app.services.auth_service._send_email", lambda *_args, **_kwargs: True)

    response = auth_client.post(f"/api/v1/customers/events/{event_id}/tasks/confirm")

    assert response.status_code == 200

    db = SessionLocal()
    try:
        notifications = (
            db.query(Notification)
            .filter(Notification.event_id == event_id, Notification.task_id == task_id)
            .all()
        )
        assert len(notifications) == 1
    finally:
        db.close()

    with TestClient(app) as admin_client:
        admin_response = admin_client.get(
            f"/api/v1/admin/notifications?event_id={event_id}&task_id={task_id}&type=task_confirmed",
            headers=_admin_headers(),
        )

    assert admin_response.status_code == 200
    body = admin_response.json()
    assert body["next_cursor"] is None
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["event_id"] == event_id
    assert item["task_id"] == task_id
    assert item["type"] == "TASK_CONFIRMED"
    assert item["status"] == "SENT"
