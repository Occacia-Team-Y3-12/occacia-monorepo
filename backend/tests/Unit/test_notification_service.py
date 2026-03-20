# ruff: noqa: S101

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.services.notification_service import NotificationService


def test_send_task_confirmed_notification_skips_duplicate_send_within_window(monkeypatch):
    service = NotificationService()
    db = MagicMock()
    customer = SimpleNamespace(customer_id="CUS-001", email="customer@test.com")
    event = SimpleNamespace(event_id="EVT-001", title="Birthday")
    task = SimpleNamespace(task_id="TSK-001", name="Cake", status="PENDING", confirmed_at=datetime(2026, 3, 21, 8, 0, tzinfo=timezone.utc))

    service._has_recent_success = MagicMock(return_value=True)
    send_email = MagicMock(return_value=True)
    monkeypatch.setattr("app.services.auth_service._send_email", send_email)

    result = service._send_task_confirmed_notification(
        db,
        customer=customer,
        event=event,
        task=task,
        window=timedelta(minutes=10),
    )

    assert result is None
    send_email.assert_not_called()
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_send_task_confirmed_notification_logs_failed_send(monkeypatch):
    service = NotificationService()
    db = MagicMock()
    customer = SimpleNamespace(customer_id="CUS-001", email="customer@test.com")
    event = SimpleNamespace(event_id="EVT-001", title="Birthday")
    task = SimpleNamespace(task_id="TSK-001", name="Cake", status="PENDING", confirmed_at=datetime(2026, 3, 21, 8, 0, tzinfo=timezone.utc))
    timestamp = datetime(2026, 3, 21, 8, 5, tzinfo=timezone.utc)

    service._has_recent_success = MagicMock(return_value=False)
    monkeypatch.setattr("app.services.notification_service.now_utc", MagicMock(return_value=timestamp))
    monkeypatch.setattr("app.services.auth_service._send_email", MagicMock(return_value=False))

    captured = {}

    def capture_add(notification):
        captured["notification"] = notification

    db.add.side_effect = capture_add

    result = service._send_task_confirmed_notification(
        db,
        customer=customer,
        event=event,
        task=task,
        window=timedelta(minutes=10),
    )

    assert result is captured["notification"]
    assert result.user_id == "CUS-001"
    assert result.event_id == "EVT-001"
    assert result.task_id == "TSK-001"
    assert result.type == "TASK_CONFIRMED"
    assert result.status == "FAILED"
    assert result.sent_at is None
    assert result.error_message == "Email send returned False"
    assert result.payload["taskId"] == "TSK-001"
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(result)


def test_has_recent_success_uses_sent_status_and_cutoff(monkeypatch):
    service = NotificationService()
    db = MagicMock()
    timestamp = datetime(2026, 3, 21, 9, 0, tzinfo=timezone.utc)
    monkeypatch.setattr("app.services.notification_service.now_utc", MagicMock(return_value=timestamp))

    query = db.query.return_value
    filtered = query.filter.return_value
    filtered.first.return_value = object()

    result = service._has_recent_success(
        db,
        type="TASK_CONFIRMED",
        dedupe_key="TASK_CONFIRMED:CUS-001:EVT-001:TSK-001",
        window=timedelta(minutes=10),
    )

    assert result is True
    db.query.assert_called_once()
    query.filter.assert_called_once()
