from __future__ import annotations

import logging
from datetime import timedelta

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.common.utils import now_utc
from app.models.customer import Customer
from app.models.event import Event
from app.models.notification import Notification
from app.models.task import Task

logger = logging.getLogger(__name__)

TASK_CONFIRMED_NOTIFICATION = "TASK_CONFIRMED"
NOTIFICATION_CHANNEL_EMAIL = "EMAIL"
NOTIFICATION_STATUS_SENT = "SENT"
NOTIFICATION_STATUS_FAILED = "FAILED"
DEFAULT_IDEMPOTENCY_WINDOW = timedelta(minutes=10)


class NotificationService:
    def send_task_confirmed_notifications(
        self,
        db: Session,
        *,
        customer: Customer,
        event: Event,
        tasks: list[Task],
        window: timedelta = DEFAULT_IDEMPOTENCY_WINDOW,
    ) -> list[Notification]:
        notifications: list[Notification] = []
        for task in tasks:
            notification = self._send_task_confirmed_notification(
                db,
                customer=customer,
                event=event,
                task=task,
                window=window,
            )
            if notification is not None:
                notifications.append(notification)
        return notifications

    def list_notifications(
        self,
        db: Session,
        *,
        limit: int,
        cursor: str | None,
        user_id: str | None = None,
        event_id: str | None = None,
        task_id: str | None = None,
        status: str | None = None,
        type: str | None = None,
    ) -> tuple[list[Notification], str | None]:
        query = db.query(Notification)

        if user_id:
            query = query.filter(Notification.user_id == user_id)
        if event_id:
            query = query.filter(Notification.event_id == event_id)
        if task_id:
            query = query.filter(Notification.task_id == task_id)
        if status:
            query = query.filter(Notification.status == status.upper())
        if type:
            query = query.filter(Notification.type == type.upper())

        if cursor:
            cursor_row = (
                db.query(Notification)
                .filter(Notification.notification_id == cursor)
                .first()
            )
            if cursor_row:
                query = query.filter(
                    or_(
                        Notification.created_at < cursor_row.created_at,
                        and_(
                            Notification.created_at == cursor_row.created_at,
                            Notification.id > cursor_row.id,
                        ),
                    )
                )

        items = (
            query.order_by(Notification.created_at.desc(), Notification.id.asc())
            .limit(limit + 1)
            .all()
        )
        next_cursor = None
        if len(items) > limit:
            next_cursor = items[limit].notification_id
            items = items[:limit]
        return items, next_cursor

    def _send_task_confirmed_notification(
        self,
        db: Session,
        *,
        customer: Customer,
        event: Event,
        task: Task,
        window: timedelta,
    ) -> Notification | None:
        dedupe_key = self._build_task_confirmed_dedupe_key(
            user_id=customer.customer_id,
            event_id=event.event_id,
            task_id=task.task_id,
        )

        if self._has_recent_success(
            db,
            type=TASK_CONFIRMED_NOTIFICATION,
            dedupe_key=dedupe_key,
            window=window,
        ):
            logger.info(
                "Skipping duplicate task confirmation notification for customer=%s task=%s",
                customer.customer_id,
                task.task_id,
            )
            return None

        payload = self._build_task_confirmed_payload(customer=customer, event=event, task=task)
        subject, body = self._build_task_confirmed_email(event=event, task=task)

        from app.services.auth_service import _send_email

        sent = _send_email(customer.email, subject, body)
        notification = Notification(
            user_id=customer.customer_id,
            event_id=event.event_id,
            task_id=task.task_id,
            channel=NOTIFICATION_CHANNEL_EMAIL,
            type=TASK_CONFIRMED_NOTIFICATION,
            status=NOTIFICATION_STATUS_SENT if sent else NOTIFICATION_STATUS_FAILED,
            dedupe_key=dedupe_key,
            payload=payload,
            error_message=None if sent else "Email send returned False",
            sent_at=now_utc() if sent else None,
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification

    def _has_recent_success(
        self,
        db: Session,
        *,
        type: str,
        dedupe_key: str,
        window: timedelta,
    ) -> bool:
        cutoff = now_utc() - window
        return (
            db.query(Notification)
            .filter(
                Notification.type == type,
                Notification.dedupe_key == dedupe_key,
                Notification.status == NOTIFICATION_STATUS_SENT,
                Notification.sent_at.is_not(None),
                Notification.sent_at >= cutoff,
            )
            .first()
            is not None
        )

    def _build_task_confirmed_dedupe_key(self, *, user_id: str, event_id: str, task_id: str) -> str:
        return f"{TASK_CONFIRMED_NOTIFICATION}:{user_id}:{event_id}:{task_id}"

    def _build_task_confirmed_payload(
        self,
        *,
        customer: Customer,
        event: Event,
        task: Task,
    ) -> dict[str, object]:
        return {
            "userId": customer.customer_id,
            "userEmail": customer.email,
            "eventId": event.event_id,
            "eventTitle": event.title,
            "taskId": task.task_id,
            "taskName": task.name,
            "taskStatus": task.status,
            "confirmedAt": task.confirmed_at.isoformat() if task.confirmed_at else None,
            "channel": NOTIFICATION_CHANNEL_EMAIL,
            "notificationType": TASK_CONFIRMED_NOTIFICATION,
        }

    def _build_task_confirmed_email(self, *, event: Event, task: Task) -> tuple[str, str]:
        subject = f"Task confirmed for {event.title}"
        body = (
            "Your task is confirmed in Occacia.\n\n"
            f"Event: {event.title}\n"
            f"Task: {task.name}\n"
            f"Task ID: {task.task_id}\n\n"
            "We will keep you updated as planning progresses."
        )
        return subject, body


notification_service = NotificationService()
