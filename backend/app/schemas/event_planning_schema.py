from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ChatMessageResponse(BaseModel):
    message_id: str = Field(alias="messageId")
    sender: str
    content: str
    sent_at: datetime = Field(alias="sentAt")

    model_config = {"populate_by_name": True}


class PaginatedChatMessagesResponse(BaseModel):
    items: list[ChatMessageResponse]
    next_cursor: str | None = Field(default=None, alias="nextCursor")

    model_config = {"populate_by_name": True}


class ChatSendRequest(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("content must not be empty")
        return trimmed


class SuggestedTaskDraftResponse(BaseModel):
    name: str
    description: str | None = None
    quantity: int = 1
    needs_vendor: bool = Field(default=False, alias="needsVendor")
    vendor_category: str | None = Field(default=None, alias="vendorCategory")
    budget_min: float | None = Field(default=None, alias="budgetMin")
    budget_max: float | None = Field(default=None, alias="budgetMax")
    currency: str = "LKR"

    model_config = {"populate_by_name": True}


class ChatSendResponse(BaseModel):
    reply: str
    suggested_tasks: list[SuggestedTaskDraftResponse] = Field(default_factory=list, alias="suggestedTasks")

    model_config = {"populate_by_name": True}


class EventSummaryResponse(BaseModel):
    summary: str


class TaskResponse(BaseModel):
    task_id: str = Field(alias="taskId")
    event_id: str = Field(alias="eventId")
    name: str
    description: str | None = None
    quantity: int = 1
    needs_vendor: bool = Field(default=False, alias="needsVendor")
    vendor_category: str | None = Field(default=None, alias="vendorCategory")
    budget_min: float | None = Field(default=None, alias="budgetMin")
    budget_max: float | None = Field(default=None, alias="budgetMax")
    currency: str
    status: str
    selected_offering_id: str | None = Field(default=None, alias="selectedOfferingId")
    assigned_vendor_id: str | None = Field(default=None, alias="assignedVendorId")
    confirmed_at: datetime | None = Field(default=None, alias="confirmedAt")
    locked_at: datetime | None = Field(default=None, alias="lockedAt")
    due_at: datetime | None = Field(default=None, alias="dueAt")
    expires_at: datetime | None = Field(default=None, alias="expiresAt")
    rejected_at: datetime | None = Field(default=None, alias="rejectedAt")
    rejection_reason: str | None = Field(default=None, alias="rejectionReason")
    status_updated_at: datetime | None = Field(default=None, alias="statusUpdatedAt")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    model_config = {"populate_by_name": True}


class TaskListResponse(BaseModel):
    items: list[TaskResponse]


class TaskCreateRequest(BaseModel):
    name: str
    description: str | None = None
    quantity: int = 1
    needs_vendor: bool = Field(default=False, alias="needsVendor")
    vendor_category: str | None = Field(default=None, alias="vendorCategory")
    budget_min: float | None = Field(default=None, alias="budgetMin")
    budget_max: float | None = Field(default=None, alias="budgetMax")
    currency: str = "LKR"

    @field_validator("name", "currency")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("must not be empty")
        return trimmed

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, value: int) -> int:
        if value < 1:
            raise ValueError("quantity must be at least 1")
        return value

    @field_validator("vendor_category")
    @classmethod
    def validate_vendor_category(cls, value: str | None) -> str | None:
        if value is None:
            return value
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("vendorCategory must not be empty")
        return trimmed

    model_config = {"populate_by_name": True}


class TaskUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    quantity: int | None = None
    needs_vendor: bool | None = Field(default=None, alias="needsVendor")
    vendor_category: str | None = Field(default=None, alias="vendorCategory")
    budget_min: float | None = Field(default=None, alias="budgetMin")
    budget_max: float | None = Field(default=None, alias="budgetMax")
    currency: str | None = None

    @field_validator("name", "currency")
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("must not be empty")
        return trimmed

    @field_validator("quantity")
    @classmethod
    def validate_optional_quantity(cls, value: int | None) -> int | None:
        if value is not None and value < 1:
            raise ValueError("quantity must be at least 1")
        return value

    @field_validator("vendor_category")
    @classmethod
    def validate_optional_vendor_category(cls, value: str | None) -> str | None:
        if value is None:
            return value
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("vendorCategory must not be empty")
        return trimmed

    model_config = {"populate_by_name": True}


class ConfirmTasksRequest(BaseModel):
    task_ids: list[str] | None = Field(default=None, alias="taskIds")

    model_config = {"populate_by_name": True}


class ConfirmTasksResponse(BaseModel):
    event: "EventResponse"
    tasks: list[TaskResponse]


class EventOccurrenceResponse(BaseModel):
    occurrence_id: str | None = Field(default=None, alias="occurrenceId")
    start_at: datetime = Field(alias="startAt")
    end_at: datetime | None = Field(default=None, alias="endAt")

    model_config = {"populate_by_name": True}


class PaginatedEventOccurrencesResponse(BaseModel):
    items: list[EventOccurrenceResponse]
    next_cursor: str | None = Field(default=None, alias="nextCursor")

    model_config = {"populate_by_name": True}


class EventScheduleModel(BaseModel):
    start_at: datetime = Field(alias="startAt")
    end_at: datetime | None = Field(default=None, alias="endAt")
    timezone: str
    is_all_day: bool = Field(alias="isAllDay")
    recurrence_rule: str | None = Field(default=None, alias="recurrenceRule")
    recurrence_until: datetime | None = Field(default=None, alias="recurrenceUntil")
    recurrence_count: int | None = Field(default=None, alias="recurrenceCount")

    model_config = {"populate_by_name": True}


class EventScheduleUpsertRequest(EventScheduleModel):
    pass


class EventScheduleResponse(BaseModel):
    schedule: EventScheduleModel
    next_occurrence: EventOccurrenceResponse | None = Field(default=None, alias="nextOccurrence")

    model_config = {"populate_by_name": True}


class EventRemindersModel(BaseModel):
    enabled: bool
    channels: list[str]
    offsets: list[str]


class EventRemindersUpsertRequest(EventRemindersModel):
    pass


class EventRemindersResponse(BaseModel):
    reminders: EventRemindersModel


class CalendarProviderCapabilitiesResponse(BaseModel):
    recurrence: bool | None = None
    reminders: bool | None = None
    direct_link_sync: bool | None = Field(default=None, alias="directLinkSync")


class CalendarProviderResponse(BaseModel):
    type: str
    display_name: str = Field(alias="displayName")
    capabilities: CalendarProviderCapabilitiesResponse | None = None

    model_config = {"populate_by_name": True}


class CalendarProviderListResponse(BaseModel):
    providers: list[CalendarProviderResponse]


class CalendarConnectRequest(BaseModel):
    provider: str
    redirect_uri: str = Field(alias="redirectUri")
    scopes: list[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class CalendarConnectResponse(BaseModel):
    provider: str
    authorization_url: str = Field(alias="authorizationUrl")
    state: str

    model_config = {"populate_by_name": True}


class CalendarExchangeCodeRequest(BaseModel):
    provider: str
    code: str
    state: str | None = None
    redirect_uri: str = Field(alias="redirectUri")

    model_config = {"populate_by_name": True}


class CalendarConnectionStatusResponse(BaseModel):
    connected: bool
    provider: str | None = None
    default_calendar_id: str | None = Field(default=None, alias="defaultCalendarId")
    connected_at: datetime | None = Field(default=None, alias="connectedAt")
    last_sync_at: datetime | None = Field(default=None, alias="lastSyncAt")

    model_config = {"populate_by_name": True}


class EventCalendarSyncStatusResponse(BaseModel):
    state: str
    provider: str | None = None
    calendar_id: str | None = Field(default=None, alias="calendarId")
    external_event_id: str | None = Field(default=None, alias="externalEventId")
    calendar_link: str | None = Field(default=None, alias="calendarLink")
    last_sync_at: datetime | None = Field(default=None, alias="lastSyncAt")
    last_sync_status: str | None = Field(default=None, alias="lastSyncStatus")

    model_config = {"populate_by_name": True}


class EventCalendarSyncUpsertRequest(BaseModel):
    state: str
    provider: str | None = None
    calendar_id: str | None = Field(default=None, alias="calendarId")

    model_config = {"populate_by_name": True}


from app.schemas.customer_schema import EventResponse


ConfirmTasksResponse.model_rebuild()
