from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field
from pydantic import field_validator


class CustomerProfileResponse(BaseModel):
    customer_id: str = Field(alias="customerId")
    email: str
    full_name: str = Field(alias="fullName")
    phone: str | None = None
    locale: str | None = None
    status: str

    model_config = {"populate_by_name": True}


class CustomerProfileUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, alias="fullName")
    phone: str | None = None
    locale: str | None = None

    model_config = {"populate_by_name": True}


class EventResponse(BaseModel):
    event_id: str = Field(alias="eventId")
    customer_id: str = Field(alias="customerId")
    event_type: str = Field(alias="eventType")
    title: str
    description: str | None = None
    location_text: str | None = Field(default=None, alias="locationText")
    start_at: datetime | None = Field(default=None, alias="startAt")
    end_at: datetime | None = Field(default=None, alias="endAt")
    timezone: str | None = None
    is_all_day: bool = Field(default=False, alias="isAllDay")
    recurrence_rule: str | None = Field(default=None, alias="recurrenceRule")
    recurrence_until: datetime | None = Field(default=None, alias="recurrenceUntil")
    recurrence_count: int | None = Field(default=None, alias="recurrenceCount")
    reminders_enabled: bool = Field(default=False, alias="remindersEnabled")
    reminder_channels: list[str] = Field(default_factory=list, alias="reminderChannels")
    reminder_offsets: list[str] = Field(default_factory=list, alias="reminderOffsets")
    reminder_schedule_status: str | None = Field(default=None, alias="reminderScheduleStatus")
    calendar_sync_state: str = Field(default="DISABLED", alias="calendarSyncState")
    calendar_sync_provider: str | None = Field(default=None, alias="calendarSyncProvider")
    calendar_sync_calendar_id: str | None = Field(default=None, alias="calendarSyncCalendarId")
    external_calendar_event_id: str | None = Field(default=None, alias="externalCalendarEventId")
    calendar_last_sync_at: datetime | None = Field(default=None, alias="calendarLastSyncAt")
    calendar_last_sync_status: str | None = Field(default=None, alias="calendarLastSyncStatus")
    status: str
    confirmed_at: datetime | None = Field(default=None, alias="confirmedAt")
    persona_ids: list[str] = Field(default_factory=list, alias="personaIds")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    model_config = {"populate_by_name": True}


class PaginatedEventsResponse(BaseModel):
    items: list[EventResponse]
    next_cursor: str | None = Field(default=None, alias="nextCursor")

    model_config = {"populate_by_name": True}


class StringListResponse(BaseModel):
    items: list[str]


class EventCreateRequest(BaseModel):
    event_type: str = Field(alias="eventType")
    title: str
    persona_ids: list[str] = Field(default_factory=list, alias="personaIds")

    @field_validator("event_type", "title")
    @classmethod
    def validate_trimmed_text(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("must not be empty")
        return trimmed

    @field_validator("title")
    @classmethod
    def validate_title_length(cls, value: str) -> str:
        if len(value) < 3:
            raise ValueError("title must be at least 3 characters long")
        return value

    @field_validator("persona_ids")
    @classmethod
    def dedupe_persona_ids(cls, value: list[str]) -> list[str]:
        return list(dict.fromkeys(value))

    model_config = {"populate_by_name": True}


class EventCreateResponse(BaseModel):
    event_id: str = Field(alias="eventId")
    status: str

    model_config = {"populate_by_name": True}


class SetEventPersonasRequest(BaseModel):
    persona_ids: list[str] = Field(alias="personaIds")

    @field_validator("persona_ids")
    @classmethod
    def dedupe_persona_ids(cls, value: list[str]) -> list[str]:
        return list(dict.fromkeys(value))

    model_config = {"populate_by_name": True}
