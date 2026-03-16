from __future__ import annotations

import calendar
import re
from urllib.parse import quote
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.common.utils import generate_prefixed_id, now_utc
from app.core.encryption import decrypt_value, encrypt_value
from app.models.customer import Customer
from app.models.event import Event
from app.models.event_chat_message import EventChatMessage
from app.models.event_persona import EventPersona
from app.models.persona import Persona
from app.models.task import Task
from app.services.google_calendar_service import google_calendar_service

_RRULE_PART_RE = re.compile(r"^(?P<key>[A-Z]+)=(?P<value>.+)$")
_DURATION_RE = re.compile(r"^P(?:(?P<days>\d+)D)?(?:T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?)?$")
_SUPPORTED_FREQ = {"DAILY", "WEEKLY", "MONTHLY", "YEARLY"}
_REMINDER_CHANNELS = {"PUSH", "EMAIL", "IN_APP"}
_CALENDAR_PROVIDERS = {"GOOGLE"}
_TIMEZONE_ALIASES = {
    "utc": "UTC",
    "gmt": "UTC",
    "slst": "Asia/Colombo",
    "ist": "Asia/Kolkata",
}

_TASK_TEMPLATES = {
    "birthday": [
        {"name": "Cake", "description": "Order or prepare the birthday cake."},
        {"name": "Decorations", "description": "Plan balloons, table setup, and decor."},
        {"name": "Guest invitations", "description": "Confirm the guest list and invitations."},
    ],
    "wedding": [
        {"name": "Venue", "description": "Finalize venue requirements and booking."},
        {"name": "Catering", "description": "Choose menu and serving style."},
        {"name": "Photography", "description": "Shortlist photo and video coverage."},
    ],
    "meeting": [
        {"name": "Agenda", "description": "Prepare agenda and key discussion points."},
        {"name": "Attendees", "description": "Confirm required attendees and invites."},
        {"name": "Materials", "description": "Prepare documents, slides, or notes."},
    ],
    "default": [
        {"name": "Venue", "description": "Confirm where the event will happen."},
        {"name": "Budget", "description": "Set the target spend and constraints."},
        {"name": "Essentials", "description": "List the must-have items or services."},
    ],
}


class EventPlanningService:
    def get_event_for_customer(self, db: Session, *, customer_id: str, event_id: str) -> Event:
        event = (
            db.query(Event)
            .filter(Event.event_id == event_id, Event.customer_id == customer_id)
            .first()
        )
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        return event

    def list_messages(
        self,
        db: Session,
        *,
        customer_id: str,
        event_id: str,
        limit: int,
        cursor: str | None,
    ) -> tuple[list[EventChatMessage], str | None]:
        self.get_event_for_customer(db, customer_id=customer_id, event_id=event_id)
        query = db.query(EventChatMessage).filter(EventChatMessage.event_id == event_id)
        if cursor:
            cursor_message = (
                db.query(EventChatMessage)
                .filter(
                    EventChatMessage.event_id == event_id,
                    EventChatMessage.message_id == cursor,
                )
                .first()
            )
            if cursor_message:
                query = query.filter(
                    or_(
                        EventChatMessage.sent_at > cursor_message.sent_at,
                        and_(
                            EventChatMessage.sent_at == cursor_message.sent_at,
                            EventChatMessage.id > cursor_message.id,
                        ),
                    )
                )
        items = query.order_by(EventChatMessage.sent_at.asc(), EventChatMessage.id.asc()).limit(limit + 1).all()
        next_cursor = None
        if len(items) > limit:
            next_cursor = items[limit].message_id
            items = items[:limit]
        return items, next_cursor

    def send_chat_message(
        self,
        db: Session,
        *,
        customer_id: str,
        event_id: str,
        content: str,
    ) -> tuple[str, list[dict[str, object]]]:
        event = self.get_event_for_customer(db, customer_id=customer_id, event_id=event_id)
        self._save_event_message(db, event_id=event.event_id, sender="CUSTOMER", content=content)
        self._apply_chat_updates(event, content)
        suggested_tasks = self._build_suggested_tasks(event)
        reply = self._build_chat_reply(db, event, content, suggested_tasks)
        self._save_event_message(db, event_id=event.event_id, sender="AI", content=reply)
        db.add(event)
        db.commit()
        db.refresh(event)
        return reply, suggested_tasks

    def summarize_event_context(self, db: Session, *, customer_id: str, event_id: str) -> str:
        event = self.get_event_for_customer(db, customer_id=customer_id, event_id=event_id)
        tasks = self.list_tasks(db, customer_id=customer_id, event_id=event_id)
        personas = (
            db.query(Persona.name)
            .join(EventPersona, EventPersona.persona_id == Persona.persona_id)
            .filter(EventPersona.event_id == event_id)
            .all()
        )
        next_occurrence = self._next_occurrence(event)
        parts = [f"{event.title} ({event.event_type}) is currently {event.status.lower()}."]
        if personas:
            parts.append("Personas: " + ", ".join(name for (name,) in personas) + ".")
        if event.location_text:
            parts.append(f"Location: {event.location_text}.")
        if event.start_at and event.timezone:
            schedule_text = f"Scheduled for {event.start_at.isoformat()} ({event.timezone})"
            if event.is_all_day:
                schedule_text += ", all-day"
            if event.recurrence_rule:
                schedule_text += f", recurring via {event.recurrence_rule}"
            parts.append(schedule_text + ".")
        else:
            parts.append("Schedule is still incomplete.")
        if next_occurrence:
            parts.append(f"Next occurrence: {next_occurrence['startAt'].isoformat()}.")
        if event.reminders_enabled:
            offsets = ", ".join(event.reminder_offsets or [])
            channels = ", ".join(event.reminder_channels or [])
            parts.append(f"Reminders enabled via {channels or 'no channels'} at {offsets or 'no offsets'}.")
            reminder_times = self._build_reminder_preview(event)
            if reminder_times:
                parts.append("Upcoming reminder times: " + ", ".join(reminder_times[:3]) + ".")
        else:
            parts.append("Reminders disabled.")
        if tasks:
            parts.append(f"{len(tasks)} tasks saved: " + ", ".join(task.name for task in tasks[:5]) + ".")
        else:
            parts.append("No tasks confirmed yet.")
        if event.calendar_sync_state == "ENABLED":
            target = event.calendar_sync_calendar_id or "default calendar"
            parts.append(f"Calendar sync enabled to {event.calendar_sync_provider or 'provider'} ({target}).")
            calendar_link = self.build_calendar_link(event)
            if calendar_link:
                parts.append(f"Calendar link: {calendar_link}.")
        return " ".join(parts)

    def list_tasks(self, db: Session, *, customer_id: str, event_id: str) -> list[Task]:
        self.get_event_for_customer(db, customer_id=customer_id, event_id=event_id)
        return (
            db.query(Task)
            .filter(Task.event_id == event_id)
            .order_by(Task.created_at.asc(), Task.id.asc())
            .all()
        )

    def create_task(
        self,
        db: Session,
        *,
        customer_id: str,
        event_id: str,
        payload: dict[str, object],
    ) -> Task:
        self.get_event_for_customer(db, customer_id=customer_id, event_id=event_id)
        task = Task(
            event_id=event_id,
            name=payload["name"],
            description=payload.get("description"),
            quantity=payload.get("quantity", 1),
            needs_vendor=self._normalize_vendor_category(
                payload.get("needs_vendor"),
                payload.get("vendor_category"),
            ),
            budget_min=payload.get("budget_min"),
            budget_max=payload.get("budget_max"),
            currency=payload.get("currency", "LKR"),
            status="DRAFT",
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    def update_task(
        self,
        db: Session,
        *,
        customer_id: str,
        event_id: str,
        task_id: str,
        payload: dict[str, object],
    ) -> Task:
        task = self._get_task(db, customer_id=customer_id, event_id=event_id, task_id=task_id)
        if task.status not in {"DRAFT", "PENDING"}:
            raise HTTPException(status_code=409, detail="Task is no longer editable")
        for field in ("name", "description", "quantity", "budget_min", "budget_max", "currency"):
            if field in payload and payload[field] is not None:
                setattr(task, field, payload[field])
        if "needs_vendor" in payload or "vendor_category" in payload:
            task.needs_vendor = self._normalize_vendor_category(
                payload.get("needs_vendor"),
                payload.get("vendor_category"),
                current_value=task.needs_vendor,
            )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    def delete_task(self, db: Session, *, customer_id: str, event_id: str, task_id: str) -> None:
        task = self._get_task(db, customer_id=customer_id, event_id=event_id, task_id=task_id)
        if task.status != "DRAFT":
            raise HTTPException(status_code=409, detail="Only draft tasks can be deleted")
        db.delete(task)
        db.commit()

    def confirm_tasks(
        self,
        db: Session,
        *,
        customer_id: str,
        event_id: str,
        task_ids: list[str] | None,
    ) -> tuple[Event, list[Task]]:
        event = self.get_event_for_customer(db, customer_id=customer_id, event_id=event_id)
        tasks = self.list_tasks(db, customer_id=customer_id, event_id=event_id)
        if not tasks:
            raise HTTPException(status_code=400, detail="Add at least 1 task")
        selected_ids = task_ids or [task.task_id for task in tasks]
        if not selected_ids:
            raise HTTPException(status_code=400, detail="Add at least 1 task")
        selected_set = set(selected_ids)
        confirmed_tasks = [task for task in tasks if task.task_id in selected_set]
        if len(confirmed_tasks) != len(selected_set):
            raise HTTPException(status_code=404, detail="Task not found")
        if not confirmed_tasks:
            raise HTTPException(status_code=400, detail="Add at least 1 task")

        confirmed_at = now_utc()
        for task in confirmed_tasks:
            task.status = "PENDING"
            task.confirmed_at = confirmed_at
            task.status_updated_at = confirmed_at
            db.add(task)

        if event.status == "DRAFT":
            event.status = "ACTIVE"
        event.confirmed_at = confirmed_at
        if event.reminders_enabled:
            event.reminder_schedule_status = "SCHEDULED" if event.start_at else "PENDING_DATE"
        if event.calendar_sync_state == "ENABLED":
            if not event.calendar_sync_provider:
                event.calendar_sync_state = "DISABLED"
                event.calendar_last_sync_status = "FAILED"
            else:
                self._sync_event_if_needed(
                    db,
                    customer_id=customer_id,
                    event=event,
                )
        db.add(event)
        db.commit()
        db.refresh(event)
        for task in confirmed_tasks:
            db.refresh(task)
        return event, confirmed_tasks

    def get_schedule(self, db: Session, *, customer_id: str, event_id: str) -> Event:
        event = self.get_event_for_customer(db, customer_id=customer_id, event_id=event_id)
        if not event.start_at or not event.timezone:
            raise HTTPException(status_code=404, detail="Schedule not found")
        return event

    def upsert_schedule(
        self,
        db: Session,
        *,
        customer_id: str,
        event_id: str,
        payload: dict[str, object],
    ) -> Event:
        event = self.get_event_for_customer(db, customer_id=customer_id, event_id=event_id)
        self._validate_timezone(payload["timezone"])
        start_at = self._ensure_aware_datetime(payload["start_at"])
        end_at = self._ensure_aware_datetime(payload.get("end_at"))
        if end_at and end_at < start_at:
            raise HTTPException(status_code=400, detail="endAt must be after startAt")
        recurrence_rule = payload.get("recurrence_rule")
        recurrence_until = self._ensure_aware_datetime(payload.get("recurrence_until"))
        recurrence_count = payload.get("recurrence_count")
        parsed_rrule = self._parse_rrule(recurrence_rule) if recurrence_rule else None
        if recurrence_count is not None and recurrence_count < 1:
            raise HTTPException(status_code=400, detail="recurrenceCount must be at least 1")
        if recurrence_until and recurrence_until < start_at:
            raise HTTPException(status_code=400, detail="recurrenceUntil must be on or after startAt")
        if parsed_rrule:
            if parsed_rrule.get("UNTIL") and recurrence_until and parsed_rrule["UNTIL"] != recurrence_until:
                raise HTTPException(status_code=400, detail="recurrenceUntil conflicts with recurrenceRule")
            if parsed_rrule.get("COUNT") and recurrence_count and parsed_rrule["COUNT"] != recurrence_count:
                raise HTTPException(status_code=400, detail="recurrenceCount conflicts with recurrenceRule")

        event.start_at = start_at
        event.end_at = end_at
        event.timezone = payload["timezone"]
        event.is_all_day = payload["is_all_day"]
        event.recurrence_rule = recurrence_rule
        event.recurrence_until = recurrence_until or (parsed_rrule.get("UNTIL") if parsed_rrule else None)
        event.recurrence_count = recurrence_count or (parsed_rrule.get("COUNT") if parsed_rrule else None)
        if event.calendar_sync_state == "ENABLED":
            self._sync_event_if_needed(
                db,
                customer_id=customer_id,
                event=event,
            )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    def get_reminders(self, db: Session, *, customer_id: str, event_id: str) -> Event:
        event = self.get_event_for_customer(db, customer_id=customer_id, event_id=event_id)
        if event.reminder_channels is None or event.reminder_offsets is None:
            raise HTTPException(status_code=404, detail="Reminders not found")
        return event

    def upsert_reminders(
        self,
        db: Session,
        *,
        customer_id: str,
        event_id: str,
        payload: dict[str, object],
    ) -> Event:
        event = self.get_event_for_customer(db, customer_id=customer_id, event_id=event_id)
        channels = list(dict.fromkeys(payload.get("channels", [])))
        offsets = list(dict.fromkeys(payload.get("offsets", [])))
        for channel in channels:
            if channel not in _REMINDER_CHANNELS:
                raise HTTPException(status_code=400, detail=f"Unsupported reminder channel: {channel}")
        for offset in offsets:
            self._parse_duration(offset)
        if payload["enabled"] and not channels:
            raise HTTPException(status_code=400, detail="At least one reminder channel is required")
        if payload["enabled"] and not offsets:
            raise HTTPException(status_code=400, detail="At least one reminder offset is required")
        event.reminders_enabled = payload["enabled"]
        event.reminder_channels = channels
        event.reminder_offsets = offsets
        event.reminder_schedule_status = (
            "SCHEDULED" if payload["enabled"] and event.start_at else "PENDING_DATE"
        ) if payload["enabled"] else "DISABLED"
        if event.calendar_sync_state == "ENABLED":
            self._sync_event_if_needed(
                db,
                customer_id=customer_id,
                event=event,
            )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    def list_occurrences(
        self,
        db: Session,
        *,
        customer_id: str,
        event_id: str,
        from_dt: datetime | None,
        limit: int,
        cursor: str | None,
    ) -> tuple[list[dict[str, datetime | str | None]], str | None]:
        event = self.get_schedule(db, customer_id=customer_id, event_id=event_id)
        if cursor:
            try:
                from_dt = self._ensure_aware_datetime(datetime.fromisoformat(cursor))
            except ValueError as exc:
                raise HTTPException(status_code=400, detail="Invalid cursor") from exc
        from_dt = self._ensure_aware_datetime(from_dt) or now_utc()
        occurrences = self._generate_occurrences(event, from_dt=from_dt, count=limit + 1)
        next_cursor = None
        if len(occurrences) > limit:
            next_cursor = occurrences[limit]["startAt"].isoformat()
            occurrences = occurrences[:limit]
        return occurrences, next_cursor

    def get_calendar_sync_status(self, db: Session, *, customer_id: str, event_id: str) -> Event:
        return self.get_event_for_customer(db, customer_id=customer_id, event_id=event_id)

    def upsert_calendar_sync(
        self,
        db: Session,
        *,
        customer_id: str,
        event_id: str,
        payload: dict[str, object],
    ) -> Event:
        event = self.get_event_for_customer(db, customer_id=customer_id, event_id=event_id)
        customer = self._get_customer(db, customer_id)
        state = payload["state"]
        if state not in {"DISABLED", "ENABLED"}:
            raise HTTPException(status_code=400, detail="Invalid calendar sync state")
        if state == "DISABLED":
            deleted = self._delete_synced_event(db, customer_id=customer_id, event=event)
            event.calendar_sync_state = "DISABLED"
            event.calendar_sync_provider = None
            event.calendar_sync_calendar_id = None
            if deleted:
                event.external_calendar_event_id = None
                event.calendar_last_sync_status = None
                event.calendar_last_sync_at = None
        else:
            provider = payload.get("provider") or customer.calendar_provider
            if provider not in _CALENDAR_PROVIDERS:
                raise HTTPException(status_code=400, detail="Calendar provider is not connected")
            if customer.calendar_provider != provider:
                raise HTTPException(status_code=400, detail="Calendar provider is not connected")
            event.calendar_sync_state = "ENABLED"
            event.calendar_sync_provider = provider
            event.calendar_sync_calendar_id = payload.get("calendar_id") or customer.calendar_default_id
            event.calendar_last_sync_status = "PENDING"
            if event.start_at:
                self._sync_event_if_needed(
                    db,
                    customer_id=customer_id,
                    event=event,
                )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    def list_calendar_providers(self) -> list[dict[str, object]]:
        return [
            {
                "type": "GOOGLE",
                "displayName": "Google Calendar",
                "capabilities": {"recurrence": True, "reminders": True, "directLinkSync": True},
            },
        ]

    def start_calendar_connect(
        self,
        db: Session,
        *,
        customer_id: str,
        provider: str,
        redirect_uri: str,
    ) -> dict[str, str]:
        if provider not in _CALENDAR_PROVIDERS:
            raise HTTPException(status_code=400, detail="Unsupported calendar provider")
        customer = self._get_customer(db, customer_id)
        state = generate_prefixed_id("STATE")
        customer.calendar_oauth_state = state
        db.add(customer)
        db.commit()
        return {
            "provider": provider,
            "authorizationUrl": google_calendar_service.build_google_auth_url(
                state=state,
                redirect_uri=redirect_uri,
            ),
            "state": state,
        }

    def exchange_calendar_code(
        self,
        db: Session,
        *,
        customer_id: str,
        provider: str,
        code: str,
        state: str | None,
        redirect_uri: str | None = None,
    ) -> Customer:
        if provider not in _CALENDAR_PROVIDERS:
            raise HTTPException(status_code=400, detail="Unsupported calendar provider")
        if not code.strip():
            raise HTTPException(status_code=400, detail="code must not be empty")
        customer = self._get_customer(db, customer_id)
        if customer.calendar_oauth_state and customer.calendar_oauth_state != state:
            raise HTTPException(status_code=400, detail="Invalid OAuth state")

        token_payload = google_calendar_service.exchange_google_code(
            code=code,
            redirect_uri=redirect_uri,
        )
        access_token = token_payload.get("access_token")
        if not access_token:
            raise HTTPException(status_code=502, detail="Google OAuth response did not include an access token")
        profile = google_calendar_service.get_google_account_profile(access_token=access_token)
        connected_at = now_utc()
        customer.calendar_provider = provider
        customer.calendar_default_id = profile.get("calendar_id") or "primary"
        customer.calendar_connected_at = connected_at
        customer.calendar_last_sync_at = None
        customer.calendar_oauth_state = None
        customer.calendar_account_email = profile.get("email")
        customer.calendar_access_token_encrypted = encrypt_value(access_token)
        refresh_token = token_payload.get("refresh_token")
        if refresh_token:
            customer.calendar_refresh_token_encrypted = encrypt_value(refresh_token)
        customer.calendar_token_expires_at = google_calendar_service.parse_expiry(token_payload)
        customer.calendar_token_scope = token_payload.get("scope")
        customer.calendar_token_type = token_payload.get("token_type")
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return customer

    def get_calendar_status(self, db: Session, *, customer_id: str) -> Customer:
        return self._get_customer(db, customer_id)

    def disconnect_calendar(self, db: Session, *, customer_id: str) -> None:
        customer = self._get_customer(db, customer_id)
        customer.calendar_provider = None
        customer.calendar_default_id = None
        customer.calendar_connected_at = None
        customer.calendar_last_sync_at = None
        customer.calendar_oauth_state = None
        customer.calendar_account_email = None
        customer.calendar_access_token_encrypted = None
        customer.calendar_refresh_token_encrypted = None
        customer.calendar_token_expires_at = None
        customer.calendar_token_scope = None
        customer.calendar_token_type = None
        db.add(customer)
        db.commit()

    def _sync_event_if_needed(self, db: Session, *, customer_id: str, event: Event) -> None:
        if event.calendar_sync_state != "ENABLED":
            return
        if not event.start_at or not event.calendar_sync_provider:
            event.calendar_last_sync_status = "PENDING"
            event.calendar_last_sync_at = None
            return

        customer = self._get_customer(db, customer_id)
        try:
            access_token = self._get_google_access_token(db, customer)
            reminder_overrides = self._build_google_reminder_overrides(event)
            event_payload = google_calendar_service.build_event_payload(
                event=event,
                description=event.description or self.summarize_event_context_from_event(event),
                reminder_overrides=reminder_overrides,
            )
            calendar_id = event.calendar_sync_calendar_id or customer.calendar_default_id or "primary"
            if event.external_calendar_event_id:
                synced_event = google_calendar_service.update_google_event(
                    access_token=access_token,
                    calendar_id=calendar_id,
                    event_id=event.external_calendar_event_id,
                    payload=event_payload,
                )
            else:
                synced_event = google_calendar_service.create_google_event(
                    access_token=access_token,
                    calendar_id=calendar_id,
                    payload=event_payload,
                )
            event.calendar_sync_calendar_id = calendar_id
            event.external_calendar_event_id = synced_event.get("id") or event.external_calendar_event_id
            event.calendar_last_sync_status = "SUCCESS"
            event.calendar_last_sync_at = now_utc()
            customer.calendar_last_sync_at = event.calendar_last_sync_at
            db.add(customer)
        except HTTPException:
            event.calendar_last_sync_status = "FAILED"
            event.calendar_last_sync_at = now_utc()

    def _delete_synced_event(self, db: Session, *, customer_id: str, event: Event) -> bool:
        if not event.external_calendar_event_id or event.calendar_sync_provider != "GOOGLE":
            return True
        customer = self._get_customer(db, customer_id)
        try:
            access_token = self._get_google_access_token(db, customer)
            calendar_id = event.calendar_sync_calendar_id or customer.calendar_default_id or "primary"
            google_calendar_service.delete_google_event(
                access_token=access_token,
                calendar_id=calendar_id,
                event_id=event.external_calendar_event_id,
            )
            return True
        except HTTPException:
            event.calendar_last_sync_status = "FAILED"
            event.calendar_last_sync_at = now_utc()
            return False

    def _get_google_access_token(self, db: Session, customer: Customer) -> str:
        if customer.calendar_provider != "GOOGLE":
            raise HTTPException(status_code=400, detail="Google Calendar is not connected")

        access_token = decrypt_value(customer.calendar_access_token_encrypted)
        refresh_token = decrypt_value(customer.calendar_refresh_token_encrypted)
        expires_at = self._ensure_aware_datetime(customer.calendar_token_expires_at)
        if access_token and (not expires_at or expires_at > now_utc() + timedelta(minutes=1)):
            return access_token
        if not refresh_token:
            raise HTTPException(status_code=400, detail="Google Calendar needs to be reconnected")

        token_payload = google_calendar_service.refresh_google_access_token(refresh_token=refresh_token)
        next_access_token = token_payload.get("access_token")
        if not next_access_token:
            raise HTTPException(status_code=502, detail="Google refresh response did not include an access token")

        customer.calendar_access_token_encrypted = encrypt_value(next_access_token)
        if token_payload.get("refresh_token"):
            customer.calendar_refresh_token_encrypted = encrypt_value(token_payload["refresh_token"])
        customer.calendar_token_expires_at = google_calendar_service.parse_expiry(token_payload)
        customer.calendar_token_scope = token_payload.get("scope", customer.calendar_token_scope)
        customer.calendar_token_type = token_payload.get("token_type", customer.calendar_token_type)
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return next_access_token

    def _build_google_reminder_overrides(self, event: Event) -> list[dict[str, object]]:
        if not event.reminders_enabled:
            return []

        overrides = []
        for offset in event.reminder_offsets or []:
            minutes = self._duration_seconds(offset) // 60
            if minutes < 0:
                continue
            overrides.append({"method": "popup", "minutes": minutes})
        return overrides

    def build_calendar_link(self, event: Event) -> str | None:
        start_at = self._ensure_aware_datetime(event.start_at)
        if not start_at or event.calendar_sync_state != "ENABLED":
            return None

        end_at = self._ensure_aware_datetime(event.end_at) or (
            start_at + timedelta(days=1) if event.is_all_day else start_at + timedelta(hours=1)
        )
        title = quote(event.title)
        details = quote(event.description or self.summarize_event_context_from_event(event))
        location = quote(event.location_text or "")

        if event.calendar_sync_provider == "GOOGLE":
            dates = f"{self._calendar_timestamp(start_at)}/{self._calendar_timestamp(end_at)}"
            return (
                "https://calendar.google.com/calendar/render?action=TEMPLATE"
                f"&text={title}&dates={dates}&details={details}&location={location}"
            )

        if event.calendar_sync_provider == "MICROSOFT":
            return (
                "https://outlook.office.com/calendar/0/deeplink/compose?path=/calendar/action/compose"
                f"&rru=addevent&subject={title}"
                f"&startdt={quote(start_at.isoformat())}&enddt={quote(end_at.isoformat())}"
                f"&body={details}&location={location}"
            )

        if event.calendar_sync_provider == "APPLE":
            return "data:text/calendar;charset=utf-8," + quote(self._build_ics_payload(event, start_at, end_at))

        return None

    def summarize_event_context_from_event(self, event: Event) -> str:
        parts = [f"{event.title} ({event.event_type})"]
        if event.location_text:
            parts.append(f"at {event.location_text}")
        if event.start_at:
            parts.append(f"starting {event.start_at.isoformat()}")
        if event.recurrence_rule:
            parts.append(f"with recurrence {event.recurrence_rule}")
        return " ".join(parts)

    def _build_suggested_tasks(self, event: Event) -> list[dict[str, object]]:
        template_key = self._resolve_template_key(event)
        return _TASK_TEMPLATES[template_key]

    def _build_chat_reply(
        self,
        db: Session,
        event: Event,
        content: str,
        suggested_tasks: list[dict[str, object]],
    ) -> str:
        tasks = self.list_tasks(db, customer_id=event.customer_id, event_id=event.event_id)
        prompts = []
        if not tasks:
            prompts.append("I added a few starter tasks based on this event.")
        if not event.start_at:
            prompts.append("When should this happen?")
        elif event.recurrence_rule:
            prompts.append("I have the recurring schedule saved.")
        else:
            prompts.append("Is this a one-time event or recurring?")
        if not event.timezone:
            prompts.append("Which time zone should I use?")
        if not event.location_text:
            prompts.append("Where is it happening?")
        if event.calendar_sync_state != "ENABLED":
            prompts.append("Do you want local reminders only or calendar sync?")
        if not event.reminders_enabled:
            prompts.append("What reminder offsets do you want?")
        else:
            prompts.append("Your reminder preferences are already saved.")

        persona_names = (
            db.query(Persona.name)
            .join(EventPersona, EventPersona.persona_id == Persona.persona_id)
            .filter(EventPersona.event_id == event.event_id)
            .all()
        )
        persona_text = ""
        if persona_names:
            persona_text = " Using persona preferences from " + ", ".join(name for (name,) in persona_names) + "."

        task_hint = ""
        if suggested_tasks:
            task_hint = " Suggested tasks: " + ", ".join(task["name"] for task in suggested_tasks[:3]) + "."

        refined_bits = []
        if event.start_at and event.timezone:
            refined_bits.append(f"Saved schedule: {event.start_at.isoformat()} ({event.timezone})")
        if event.recurrence_rule:
            refined_bits.append(f"Recurrence: {event.recurrence_rule}")
        if event.reminders_enabled:
            refined_bits.append(
                "Reminders: "
                + ", ".join(event.reminder_offsets or [])
                + " via "
                + ", ".join(event.reminder_channels or [])
            )
        if event.calendar_sync_state == "ENABLED":
            refined_bits.append(f"Calendar sync: {event.calendar_sync_provider or 'connected'}")
        refinement_text = f" {' '.join(refined_bits)}." if refined_bits else ""

        return f"{prompts[0]} {' '.join(prompts[1:])}{persona_text}{task_hint}{refinement_text}".strip()

    def _apply_chat_updates(self, event: Event, content: str) -> None:
        normalized = content.strip()
        if not normalized:
            return

        lowered = normalized.lower()
        if not event.location_text:
            location_match = re.search(r"\b(?:at|in)\s+([A-Za-z][A-Za-z ,.-]{2,})", normalized)
            if location_match:
                event.location_text = location_match.group(1).strip().rstrip(".")

        timezone_name = self._extract_timezone(lowered)
        if timezone_name:
            event.timezone = timezone_name

        parsed_schedule = self._extract_schedule(normalized, event.timezone or "UTC")
        if parsed_schedule:
            event.start_at = parsed_schedule["start_at"]
            event.end_at = parsed_schedule.get("end_at")
            event.timezone = parsed_schedule["timezone"]
            event.is_all_day = parsed_schedule["is_all_day"]

        recurrence = self._extract_recurrence(lowered)
        if recurrence:
            event.recurrence_rule = recurrence
            event.recurrence_count = None
            event.recurrence_until = None

        reminder_channels, reminder_offsets = self._extract_reminders(lowered)
        if reminder_channels or reminder_offsets:
            event.reminders_enabled = True
            event.reminder_channels = reminder_channels or event.reminder_channels or ["IN_APP"]
            event.reminder_offsets = reminder_offsets or event.reminder_offsets or ["P1D"]
            event.reminder_schedule_status = "SCHEDULED" if event.start_at else "PENDING_DATE"

        if "local reminder" in lowered or "local reminders" in lowered:
            event.calendar_sync_state = "DISABLED"

        if "calendar sync" in lowered or "sync to" in lowered or "google calendar" in lowered:
            if "google" in lowered:
                event.calendar_sync_provider = "GOOGLE"
            if event.calendar_sync_provider:
                event.calendar_sync_state = "ENABLED"
                event.calendar_last_sync_status = "PENDING"
                event.calendar_last_sync_at = None
                event.calendar_sync_calendar_id = event.calendar_sync_calendar_id or "primary"

    def _normalize_vendor_category(
        self,
        needs_vendor: object | None,
        vendor_category: object | None,
        *,
        current_value: str | None = None,
    ) -> str | None:
        if needs_vendor is None and vendor_category is None:
            return current_value
        if needs_vendor is False:
            return None
        if isinstance(vendor_category, str) and vendor_category.strip():
            return vendor_category.strip()
        if needs_vendor:
            return current_value or "general"
        return None

    def _extract_timezone(self, lowered: str) -> str | None:
        for alias, timezone_name in _TIMEZONE_ALIASES.items():
            if re.search(rf"\b{re.escape(alias)}\b", lowered):
                return timezone_name
        zone_match = re.search(r"\b([A-Za-z]+/[A-Za-z_]+)\b", lowered)
        if zone_match:
            timezone_name = zone_match.group(1)
            try:
                ZoneInfo(timezone_name)
                return timezone_name
            except ZoneInfoNotFoundError:
                return None
        return None

    def _extract_schedule(self, content: str, timezone_name: str) -> dict[str, object] | None:
        date_match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", content)
        if not date_match:
            return None

        try:
            local_zone = ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError:
            local_zone = timezone.utc

        date_value = datetime.fromisoformat(date_match.group(1))
        time_match = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", content, flags=re.IGNORECASE)
        is_all_day = "all day" in content.lower()
        if time_match:
            hours = int(time_match.group(1)) % 12
            if time_match.group(3).lower() == "pm":
                hours += 12
            minutes = int(time_match.group(2) or "0")
        else:
            hours = 9
            minutes = 0

        local_dt = datetime(
            date_value.year,
            date_value.month,
            date_value.day,
            hours,
            minutes,
            tzinfo=local_zone,
        )
        start_at = local_dt.astimezone(timezone.utc)
        end_at = None if is_all_day else start_at + timedelta(hours=3)
        return {
            "start_at": start_at,
            "end_at": end_at,
            "timezone": timezone_name,
            "is_all_day": is_all_day,
        }

    def _extract_recurrence(self, lowered: str) -> str | None:
        if "every year" in lowered or "yearly" in lowered or "birthday" in lowered:
            return "FREQ=YEARLY;INTERVAL=1"
        if "every month" in lowered or "monthly" in lowered:
            return "FREQ=MONTHLY;INTERVAL=1"
        if "every week" in lowered or "weekly" in lowered:
            return "FREQ=WEEKLY;INTERVAL=1"
        if "every day" in lowered or "daily" in lowered:
            return "FREQ=DAILY;INTERVAL=1"
        return None

    def _extract_reminders(self, lowered: str) -> tuple[list[str], list[str]]:
        if "reminder" not in lowered:
            return [], []

        channels = []
        if "email" in lowered:
            channels.append("EMAIL")
        if "push" in lowered:
            channels.append("PUSH")
        if "in-app" in lowered or "in app" in lowered:
            channels.append("IN_APP")
        if not channels:
            channels = ["IN_APP"]

        offsets = []
        if "7 day" in lowered or "week before" in lowered:
            offsets.append("P7D")
        if "1 day" in lowered or "day before" in lowered:
            offsets.append("P1D")
        if "same day" in lowered or "on the day" in lowered:
            offsets.append("PT0M")
        if "1 hour" in lowered:
            offsets.append("PT1H")
        if not offsets:
            offsets = ["P1D"]

        return list(dict.fromkeys(channels)), list(dict.fromkeys(offsets))

    def _build_reminder_preview(self, event: Event) -> list[str]:
        next_occurrence = self._next_occurrence(event)
        if not next_occurrence:
            return []
        start_at = next_occurrence["startAt"]
        previews = []
        for offset in event.reminder_offsets or []:
            previews.append((start_at - self._parse_duration(offset)).isoformat())
        return previews

    def _resolve_template_key(self, event: Event) -> str:
        search_text = " ".join(filter(None, [event.event_type, event.title, event.description])).lower()
        for key in ("birthday", "wedding", "meeting"):
            if key in search_text:
                return key
        return "default"

    def _save_event_message(self, db: Session, *, event_id: str, sender: str, content: str) -> EventChatMessage:
        message = EventChatMessage(event_id=event_id, sender=sender, content=content.strip())
        db.add(message)
        db.commit()
        db.refresh(message)
        return message

    def _get_task(self, db: Session, *, customer_id: str, event_id: str, task_id: str) -> Task:
        self.get_event_for_customer(db, customer_id=customer_id, event_id=event_id)
        task = (
            db.query(Task)
            .filter(Task.event_id == event_id, Task.task_id == task_id)
            .first()
        )
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task

    def _get_customer(self, db: Session, customer_id: str) -> Customer:
        customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        return customer

    def _validate_timezone(self, timezone_name: str) -> None:
        try:
            ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError as exc:
            raise HTTPException(status_code=400, detail="Invalid timezone") from exc

    def _ensure_aware_datetime(self, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def _parse_rrule(self, rule: str) -> dict[str, object]:
        parsed: dict[str, object] = {}
        for part in rule.split(";"):
            match = _RRULE_PART_RE.match(part)
            if not match:
                raise HTTPException(status_code=400, detail="Invalid recurrenceRule")
            key = match.group("key")
            value = match.group("value")
            parsed[key] = value
        freq = parsed.get("FREQ")
        if freq not in _SUPPORTED_FREQ:
            raise HTTPException(status_code=400, detail="Unsupported recurrence frequency")
        interval = int(parsed.get("INTERVAL", "1"))
        if interval < 1:
            raise HTTPException(status_code=400, detail="INTERVAL must be at least 1")
        parsed["INTERVAL"] = interval
        if "COUNT" in parsed:
            count = int(str(parsed["COUNT"]))
            if count < 1:
                raise HTTPException(status_code=400, detail="COUNT must be at least 1")
            parsed["COUNT"] = count
        if "UNTIL" in parsed:
            until = str(parsed["UNTIL"]).replace("Z", "+00:00")
            try:
                parsed["UNTIL"] = self._ensure_aware_datetime(datetime.fromisoformat(until))
            except ValueError as exc:
                raise HTTPException(status_code=400, detail="Invalid UNTIL in recurrenceRule") from exc
        return parsed

    def _parse_duration(self, duration: str) -> timedelta:
        match = _DURATION_RE.match(duration)
        if not match:
            raise HTTPException(status_code=400, detail=f"Invalid reminder offset: {duration}")
        days = int(match.group("days") or 0)
        hours = int(match.group("hours") or 0)
        minutes = int(match.group("minutes") or 0)
        return timedelta(days=days, hours=hours, minutes=minutes)

    def _duration_seconds(self, duration: str) -> int:
        return int(self._parse_duration(duration).total_seconds())

    def _calendar_timestamp(self, value: datetime) -> str:
        return value.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    def _build_ics_payload(self, event: Event, start_at: datetime, end_at: datetime) -> str:
        uid = event.external_calendar_event_id or generate_prefixed_id("CAL")
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Occacia//UC13//EN",
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{self._calendar_timestamp(now_utc())}",
            f"DTSTART:{self._calendar_timestamp(start_at)}",
            f"DTEND:{self._calendar_timestamp(end_at)}",
            f"SUMMARY:{event.title}",
            f"DESCRIPTION:{event.description or self.summarize_event_context_from_event(event)}",
        ]
        if event.location_text:
            lines.append(f"LOCATION:{event.location_text}")
        if event.recurrence_rule:
            lines.append(f"RRULE:{event.recurrence_rule}")
        lines.extend(["END:VEVENT", "END:VCALENDAR"])
        return "\r\n".join(lines)

    def _generate_occurrences(
        self,
        event: Event,
        *,
        from_dt: datetime,
        count: int,
    ) -> list[dict[str, datetime | str | None]]:
        start_at = self._ensure_aware_datetime(event.start_at)
        if start_at is None:
            return []
        duration = (self._ensure_aware_datetime(event.end_at) - start_at) if event.end_at else None
        if not event.recurrence_rule:
            if start_at >= from_dt:
                return [self._serialize_occurrence(event, 1, start_at, duration)]
            return []

        parsed = self._parse_rrule(event.recurrence_rule)
        interval = int(parsed["INTERVAL"])
        limit_until = event.recurrence_until or parsed.get("UNTIL")
        limit_count = event.recurrence_count or parsed.get("COUNT")
        freq = str(parsed["FREQ"])

        occurrences: list[dict[str, datetime | str | None]] = []
        current = start_at
        idx = 1
        max_iterations = max((limit_count or 0) + count + 5, count + 32)
        for _ in range(max_iterations):
            if limit_count and idx > limit_count:
                break
            if limit_until and current > limit_until:
                break
            if current >= from_dt:
                occurrences.append(self._serialize_occurrence(event, idx, current, duration))
                if len(occurrences) >= count:
                    break
            current = self._advance_occurrence(current, freq=freq, interval=interval)
            idx += 1
        return occurrences

    def _next_occurrence(self, event: Event) -> dict[str, datetime | str | None] | None:
        occurrences = self._generate_occurrences(event, from_dt=now_utc(), count=1)
        return occurrences[0] if occurrences else None

    def _serialize_occurrence(
        self,
        event: Event,
        occurrence_no: int,
        start_at: datetime,
        duration: timedelta | None,
    ) -> dict[str, datetime | str | None]:
        end_at = start_at + duration if duration else None
        return {
            "occurrenceId": f"{event.event_id}:{occurrence_no}",
            "startAt": start_at,
            "endAt": end_at,
        }

    def _advance_occurrence(self, current: datetime, *, freq: str, interval: int) -> datetime:
        if freq == "DAILY":
            return current + timedelta(days=interval)
        if freq == "WEEKLY":
            return current + timedelta(weeks=interval)
        if freq == "MONTHLY":
            return self._add_months(current, interval)
        if freq == "YEARLY":
            return self._add_years(current, interval)
        raise HTTPException(status_code=400, detail="Unsupported recurrence frequency")

    def _add_months(self, value: datetime, months: int) -> datetime:
        month_index = value.month - 1 + months
        year = value.year + month_index // 12
        month = month_index % 12 + 1
        day = min(value.day, calendar.monthrange(year, month)[1])
        return value.replace(year=year, month=month, day=day)

    def _add_years(self, value: datetime, years: int) -> datetime:
        year = value.year + years
        day = value.day
        if value.month == 2 and value.day == 29 and not calendar.isleap(year):
            day = 28
        return value.replace(year=year, day=day)


event_planning_service = EventPlanningService()
