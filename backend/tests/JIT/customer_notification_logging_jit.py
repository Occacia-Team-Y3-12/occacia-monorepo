# ruff: noqa: S101

from app.core.database import SessionLocal
from app.models.notification import Notification


def test_whenCustomerConfirmsTaskTwice_notificationIsLoggedOnceAndQueryable(auth_client, active_customer, monkeypatch):
    send_calls: list[tuple[str, str, str]] = []

    def fake_send_email(to: str, subject: str, body: str) -> bool:
        send_calls.append((to, subject, body))
        return True

    monkeypatch.setattr("app.services.auth_service._send_email", fake_send_email)

    create_response = auth_client.post(
        "/api/v1/customers/events",
        json={"eventType": "Birthday", "title": "Birthday Notification Test"},
    )
    assert create_response.status_code == 201
    event_id = create_response.json()["eventId"]

    task_response = auth_client.post(
        f"/api/v1/customers/events/{event_id}/tasks",
        json={"name": "Cake", "description": "Order a cake", "quantity": 1},
    )
    assert task_response.status_code == 201
    task_id = task_response.json()["taskId"]

    first_confirm = auth_client.post(
        f"/api/v1/customers/events/{event_id}/tasks/confirm",
        json={"taskIds": [task_id]},
    )
    assert first_confirm.status_code == 200
    assert first_confirm.json()["event"]["status"] == "ACTIVE"

    second_confirm = auth_client.post(
        f"/api/v1/customers/events/{event_id}/tasks/confirm",
        json={"taskIds": [task_id]},
    )
    assert second_confirm.status_code == 200

    db = SessionLocal()
    try:
        notifications = (
            db.query(Notification)
            .filter(
                Notification.user_id == active_customer.customer_id,
                Notification.event_id == event_id,
                Notification.task_id == task_id,
                Notification.type == "TASK_CONFIRMED",
            )
            .all()
        )
    finally:
        db.close()

    assert len(send_calls) == 1
    assert len(notifications) == 1
    assert notifications[0].status == "SENT"
    assert notifications[0].payload["eventId"] == event_id
    assert notifications[0].payload["taskId"] == task_id
