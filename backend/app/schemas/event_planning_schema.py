"""
app/schemas/event_planning_schema.py
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

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


class VenueDisplay(BaseModel):
    """Vendor package matched by the AI planning engine."""
    id: str | None = None  # str to support AI-VENUE-1 style IDs
    name: str
    description: str | None = None
    price_per_head: float | None = Field(default=None, alias="pricePerHead")
    tags: list[str] = Field(default_factory=list)
    total_estimated_price: float | None = Field(default=None, alias="totalEstimatedPrice")
    match_score: int | None = Field(default=None, alias="matchScore")
    match_score_max: int | None = Field(default=None, alias="matchScoreMax")
    match_score_label: str | None = Field(default=None, alias="matchScoreLabel")
    vendor_name: str | None = Field(default=None, alias="vendorName")
    vendor_phone: str | None = Field(default=None, alias="vendorPhone")
    vendor_location: str | None = Field(default=None, alias="vendorLocation")
    vendor_email: str | None = Field(default=None, alias="vendorEmail")
    is_verified: bool = Field(default=False, alias="isVerified")
    tweak_note: str | None = Field(default=None, alias="tweakNote")

    model_config = {"populate_by_name": True, "from_attributes": True, "extra": "ignore"}


class GiftDisplay(BaseModel):
    """One of the 3 gift recommendations shown alongside venue packages."""
    id: str | None = None  # str to support AI-GIFT-1 style IDs
    name: str
    description: str | None = None
    price_per_head: float | None = Field(default=None, alias="pricePerHead")
    estimated_price: float | None = Field(default=None, alias="estimatedPrice")
    tags: list[str] = Field(default_factory=list)
    location: str | None = None
    vendor_name: str | None = Field(default=None, alias="vendorName")
    match_score_label: str | None = Field(default=None, alias="matchScoreLabel")
    tweak_note: str | None = Field(default=None, alias="tweakNote")

    model_config = {"populate_by_name": True, "from_attributes": True, "extra": "ignore"}


class ChatSendResponse(BaseModel):
    """
    Response for POST /customers/events/{eventId}/chat  (UC-13).

    Spec-required fields
    --------------------
    reply           — the AI/system reply text to display in chat
    suggestedTasks  — template-based task drafts for the customer to review

    Extended fields  (additive — not in OpenAPI spec)
    -------------------------------------------------
    These carry the AI planning engine's full output so the frontend
    can update persona state, show vendor matches, track missing planning
    info, and handle bookings without a second request.
    Clients that only consume reply + suggestedTasks are unaffected.
    """

    # ── Spec fields ───────────────────────────────────────────────────────────
    reply: str
    suggested_tasks: list[SuggestedTaskDraftResponse] = Field(
        default_factory=list, alias="suggestedTasks"
    )

    # ── Planning engine — conversation state ──────────────────────────────────
    intent: str | None = None
    reasoning: str | None = None
    personality_profile: str | None = Field(default=None, alias="personalityProfile")
    gift_suggestion: str | None = Field(default=None, alias="giftSuggestion")
    event_type: str | None = Field(default=None, alias="eventType")
    event_date: str | None = Field(default=None, alias="eventDate")
    location: str | None = None
    budget_per_head: float | None = Field(default=None, alias="budgetPerHead")
    guest_count: int | None = Field(default=None, alias="guestCount")
    venue_tags: list[str] = Field(default_factory=list, alias="venueTags")
    missing_info: list[str] = Field(default_factory=list, alias="missingInfo")

    # 3 venue package recommendations
    matched_venues: list[VenueDisplay] = Field(default_factory=list, alias="matchedVenues")
    # 3 gift recommendations (priced from 25% of total budget)
    matched_gifts: list[GiftDisplay] = Field(default_factory=list, alias="matchedGifts")
    # Legacy generated packages (kept for backward compat)
    matched_packages: List[Dict[str, Any]] = Field(default_factory=list, alias="matchedPackages")

    venue_match_tier: int | None = Field(default=None, alias="venueMatchTier")

    # ── Persona flow flags ────────────────────────────────────────────────────
    ask_save_persona: bool = Field(default=False, alias="askSavePersona")
    persona_saved: bool = Field(default=False, alias="personaSaved")
    persona_confirmed: bool = Field(default=False, alias="personaConfirmed")

    # ── Booking ───────────────────────────────────────────────────────────────
    booking_created: bool = Field(default=False, alias="bookingCreated")
    booking_id: str | None = Field(default=None, alias="bookingId")

    # ── FIX #3 — redirect after booking ──────────────────────────────────────
    # For real DB bookings: /customers/package-orders/{bookingId}
    # For AI fallback bookings: None (show inquiry message instead)
    redirect_url: str | None = Field(default=None, alias="redirectUrl")

    # ── FIX #1 — AI fallback indicator ───────────────────────────────────────
    # True when matched_venues/gifts are AI-generated concepts, not real DB packages
    is_ai_fallback: bool = Field(default=False, alias="isAiFallback")

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