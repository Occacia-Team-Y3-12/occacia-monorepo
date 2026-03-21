from __future__ import annotations

from uuid import uuid4

from app.core.database import SessionLocal
from app.models.customer import Customer
from app.models.notification import Notification
from app.services.notification_service import (
    CUSTOMER_VERIFICATION_NOTIFICATION,
    NOTIFICATION_STATUS_PERMANENT_FAILURE,
    NOTIFICATION_STATUS_QUEUED,
    NOTIFICATION_STATUS_RETRY_PENDING,
    NOTIFICATION_STATUS_SENT,
    ProviderResult,
    notification_service,
)


def test_customer_registration_queues_and_sends_verification_email(client, monkeypatch):
    email = f"user-{uuid4().hex[:8]}@test.com"
    sent_payloads: list[tuple[str, str]] = []

    def fake_send_email(*, to: str, subject: str, text_body: str, html_body: str | None):
        sent_payloads.append((to, subject))
        return ProviderResult(success=True, provider="SENDGRID", provider_message_id="reg-msg")

    monkeypatch.setattr(notification_service, "_send_email", fake_send_email)

    response = client.post(
        "/api/v1/auth/customer/register",
        json={
            "fullName": "Jane Doe",
            "email": email,
            "password": "StrongPass123!",
            "phone": "+94771234567",
        },
    )

    assert response.status_code == 201

    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.email == email).first()
        assert customer is not None

        notification = (
            db.query(Notification)
            .filter(
                Notification.user_id == customer.customer_id,
                Notification.type == CUSTOMER_VERIFICATION_NOTIFICATION,
            )
            .first()
        )
        assert notification is not None
        assert notification.status == NOTIFICATION_STATUS_QUEUED
        assert notification.recipient_email == email

        processed = notification_service.process_pending_notifications(db, batch_size=10)
        assert processed == 1
        db.refresh(notification)
        assert notification.status == NOTIFICATION_STATUS_SENT
        assert notification.attempt_count == 1
    finally:
        db.close()

    assert sent_payloads == [(email, "Verify your Occacia account")]


def test_notification_worker_marks_permanent_failure_after_three_retries(client, monkeypatch):
    email = f"user-{uuid4().hex[:8]}@test.com"
    monkeypatch.setattr(
        notification_service,
        "_send_email",
        lambda **_kwargs: ProviderResult(success=False, provider="SENDGRID", error_message="temporary outage"),
    )

    response = client.post(
        "/api/v1/auth/customer/register",
        json={
            "fullName": "Jane Retry",
            "email": email,
            "password": "StrongPass123!",
            "phone": "+94771234567",
        },
    )

    assert response.status_code == 201

    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.email == email).first()
        assert customer is not None
        notification = (
            db.query(Notification)
            .filter(
                Notification.user_id == customer.customer_id,
                Notification.type == CUSTOMER_VERIFICATION_NOTIFICATION,
            )
            .first()
        )
        assert notification is not None

        for _ in range(3):
            notification_service.process_pending_notifications(db, batch_size=10)
            db.refresh(notification)
            assert notification.status == NOTIFICATION_STATUS_RETRY_PENDING

            notification.next_attempt_at = notification.created_at
            db.add(notification)
            db.commit()
            db.refresh(notification)

        notification_service.process_pending_notifications(db, batch_size=10)
        db.refresh(notification)

        assert notification.status == NOTIFICATION_STATUS_PERMANENT_FAILURE
        assert notification.attempt_count == 4
        assert notification.error_message == "temporary outage"
        assert notification.next_attempt_at is None
    finally:
        db.close()
