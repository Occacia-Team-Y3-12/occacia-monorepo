from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


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
