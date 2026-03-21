# ruff: noqa: S101

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.services.notification_service import (
    CUSTOMER_VERIFICATION_NOTIFICATION,
    NOTIFICATION_STATUS_PERMANENT_FAILURE,
    NOTIFICATION_STATUS_RETRY_PENDING,
    NOTIFICATION_STATUS_SENT,
    NotificationService,
    ProviderResult,
)


def test_enqueue_notification_skips_duplicate_within_window():
    service = NotificationService()
    db = MagicMock()
    service._resolve_recipient = MagicMock(return_value={"email": "customer@test.com", "name": "Jane"})
    service._has_recent_non_terminal = MagicMock(return_value=True)

    result = service.enqueue_notification(
        db,
        notification_type="TASK_CONFIRMED",
        recipient_id="CUS-001",
        context_data={"eventId": "EVT-001", "taskId": "TSK-001"},
        dedupe_window=timedelta(minutes=10),
    )

    assert result is None
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_render_template_injects_dynamic_values():
    service = NotificationService()

    rendered = service.render_template(
        notification_type=CUSTOMER_VERIFICATION_NOTIFICATION,
        recipient_name="Jane Doe",
        context_data={
            "verificationLink": "https://app.occacia.com/verify?token=abc",
        },
    )

    assert "Jane Doe" in rendered.subject or rendered.subject == "Verify your Occacia account"
    assert "Jane Doe" in rendered.text_body
    assert "https://app.occacia.com/verify?token=abc" in rendered.text_body
    assert "https://app.occacia.com/verify?token=abc" in rendered.html_body


def test_deliver_notification_marks_sent_on_provider_success(monkeypatch):
    service = NotificationService()
    db = MagicMock()
    timestamp = datetime(2026, 3, 21, 8, 5, tzinfo=timezone.utc)
    monkeypatch.setattr("app.services.notification_service.now_utc", MagicMock(return_value=timestamp))
    monkeypatch.setattr(
        service,
        "_send_email",
        MagicMock(return_value=ProviderResult(success=True, provider="SENDGRID", provider_message_id="msg-123")),
    )

    notification = SimpleNamespace(
        attempt_count=0,
        max_attempts=4,
        recipient_email="customer@test.com",
        subject="Subject",
        body_text="Body",
        body_html="<p>Body</p>",
        provider=None,
        provider_message_id=None,
        error_message=None,
        status="QUEUED",
        sent_at=None,
        next_attempt_at=timestamp,
        last_attempt_at=None,
    )

    result = service._deliver_notification(db, notification=notification)

    assert result.status == NOTIFICATION_STATUS_SENT
    assert result.sent_at == timestamp
    assert result.attempt_count == 1
    assert result.provider_message_id == "msg-123"
    assert result.next_attempt_at is None


def test_deliver_notification_retries_until_permanent_failure(monkeypatch):
    service = NotificationService()
    db = MagicMock()
    timestamp = datetime(2026, 3, 21, 9, 0, tzinfo=timezone.utc)
    monkeypatch.setattr("app.services.notification_service.now_utc", MagicMock(return_value=timestamp))
    monkeypatch.setattr(
        service,
        "_send_email",
        MagicMock(return_value=ProviderResult(success=False, provider="SENDGRID", error_message="provider down")),
    )

    retryable = SimpleNamespace(
        attempt_count=2,
        max_attempts=4,
        recipient_email="customer@test.com",
        subject="Subject",
        body_text="Body",
        body_html=None,
        provider=None,
        provider_message_id=None,
        error_message=None,
        status="QUEUED",
        sent_at=None,
        next_attempt_at=timestamp,
        last_attempt_at=None,
    )
    permanent = SimpleNamespace(
        attempt_count=3,
        max_attempts=4,
        recipient_email="customer@test.com",
        subject="Subject",
        body_text="Body",
        body_html=None,
        provider=None,
        provider_message_id=None,
        error_message=None,
        status="QUEUED",
        sent_at=None,
        next_attempt_at=timestamp,
        last_attempt_at=None,
    )

    retry_result = service._deliver_notification(db, notification=retryable)
    permanent_result = service._deliver_notification(db, notification=permanent)

    assert retry_result.status == NOTIFICATION_STATUS_RETRY_PENDING
    assert retry_result.attempt_count == 3
    assert retry_result.next_attempt_at == timestamp + timedelta(minutes=1)

    assert permanent_result.status == NOTIFICATION_STATUS_PERMANENT_FAILURE
    assert permanent_result.attempt_count == 4
    assert permanent_result.next_attempt_at is None
