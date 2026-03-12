"""
app/routers/v1/customer_router.py

Customer profile management, event creation, and event planning (UC-13) routes.
"""
from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.customer import Customer
from app.models.task import Task
from app.routers.v1.auth_router import get_current_customer
from app.schemas.customer_schema import (
    CustomerProfileResponse,
    CustomerProfileUpdateRequest,
    EventCreateRequest,
    EventCreateResponse,
    EventResponse,
    PaginatedEventsResponse,
    SetEventPersonasRequest,
    StringListResponse,
)
from app.schemas.event_planning_schema import (
    CalendarConnectRequest,
    CalendarConnectResponse,
    CalendarConnectionStatusResponse,
    CalendarExchangeCodeRequest,
    CalendarProviderListResponse,
    ChatMessageResponse,
    ChatSendRequest,
    ChatSendResponse,
    ConfirmTasksRequest,
    ConfirmTasksResponse,
    EventCalendarSyncStatusResponse,
    EventCalendarSyncUpsertRequest,
    EventOccurrenceResponse,
    EventRemindersModel,
    EventRemindersResponse,
    EventRemindersUpsertRequest,
    EventScheduleModel,
    EventScheduleResponse,
    EventScheduleUpsertRequest,
    EventSummaryResponse,
    PaginatedChatMessagesResponse,
    PaginatedEventOccurrencesResponse,
    TaskCreateRequest,
    TaskListResponse,
    TaskResponse,
    TaskUpdateRequest,
)
from app.services.customer_service import customer_service
from app.services.event_planning_service import event_planning_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Customer"])


# --- Response Builders ---

def _customer_response(customer: Customer) -> CustomerProfileResponse:
    return CustomerProfileResponse(
        customerId=customer.customer_id,
        email=customer.email,
        fullName=customer.full_name,
        phone=customer.phone,
        locale=customer.locale,
        status=customer.status,
    )

def _event_response(event, persona_ids: list[str]) -> EventResponse:
    return EventResponse(
        eventId=event.event_id,
        customerId=event.customer_id,
        eventType=event.event_type,
        title=event.title,
        description=event.description,
        locationText=event.location_text,
        startAt=event.start_at,
        endAt=event.end_at,
        status=event.status,
        confirmedAt=event.confirmed_at,
        personaIds=persona_ids,
        createdAt=event.created_at,
        updatedAt=event.updated_at,
    )

def _task_response(task: Task) -> TaskResponse:
    return TaskResponse(
        taskId=task.task_id,
        eventId=task.event_id,
        name=task.name,
        description=task.description,
        quantity=task.quantity,
        budgetMin=task.budget_min,
        budgetMax=task.budget_max,
        currency=task.currency,
        status=task.status,
        selectedOfferingId=task.selected_offering_id,
        assignedVendorId=task.assigned_vendor_id,
        confirmedAt=task.confirmed_at,
        lockedAt=task.locked_at,
        dueAt=task.due_at,
        expiresAt=task.expires_at,
        rejectedAt=task.rejected_at,
        rejectionReason=task.rejection_reason,
        statusUpdatedAt=task.status_updated_at,
        createdAt=task.created_at,
        updatedAt=task.updated_at,
    )

def _schedule_response(event) -> EventScheduleResponse:
    next_occurrence = event_planning_service._next_occurrence(event)
    return EventScheduleResponse(
        schedule=EventScheduleModel(
            startAt=event.start_at,
            endAt=event.end_at,
            timezone=event.timezone,
            isAllDay=event.is_all_day,
            recurrenceRule=event.recurrence_rule,
            recurrenceUntil=event.recurrence_until,
            recurrenceCount=event.recurrence_count,
        ),
        nextOccurrence=EventOccurrenceResponse(**next_occurrence) if next_occurrence else None,
    )

def _reminders_response(event) -> EventRemindersResponse:
    return EventRemindersResponse(
        reminders=EventRemindersModel(
            enabled=event.reminders_enabled,
            channels=event.reminder_channels or [],
            offsets=event.reminder_offsets or [],
        )
    )

def _calendar_status_response(customer: Customer) -> CalendarConnectionStatusResponse:
    return CalendarConnectionStatusResponse(
        connected=bool(customer.calendar_provider),
        provider=customer.calendar_provider,
        defaultCalendarId=customer.calendar_default_id,
        connectedAt=customer.calendar_connected_at,
        lastSyncAt=customer.calendar_last_sync_at,
    )

def _event_calendar_sync_response(event) -> EventCalendarSyncStatusResponse:
    return EventCalendarSyncStatusResponse(
        state=event.calendar_sync_state,
        provider=event.calendar_sync_provider,
        calendarId=event.calendar_sync_calendar_id,
        externalEventId=event.external_calendar_event_id,
        lastSyncAt=event.calendar_last_sync_at,
        lastSyncStatus=event.calendar_last_sync_status,
    )

def _message_response(message) -> ChatMessageResponse:
    return ChatMessageResponse(
        messageId=message.message_id,
        sender=message.sender,
        content=message.content,
        sentAt=message.sent_at,
    )


# --- Customer Profile Routes ---

@router.get("/customers/me", response_model=CustomerProfileResponse, response_model_by_alias=True)
def get_customer_me(current_customer: Customer = Depends(get_current_customer)):
    """Get current customer profile."""
    return _customer_response(current_customer)

@router.put("/customers/me", response_model=CustomerProfileResponse, response_model_by_alias=True)
def update_customer_me(
    body: CustomerProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    """Update current customer profile."""
    updated_customer = customer_service.update_customer_profile(
        db,
        current_customer,
        full_name=body.full_name,
        phone=body.phone,
        locale=body.locale,
    )
    return _customer_response(updated_customer)


# --- Customer Event Routes ---

@router.get(
    "/customers/events",
    response_model=PaginatedEventsResponse,
    response_model_by_alias=True,
)
def list_customer_events(
    status: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    events, next_cursor = customer_service.list_customer_events(
        db,
        customer_id=current_customer.customer_id,
        status=status,
        limit=limit,
        cursor=cursor,
    )
    persona_ids_by_event = customer_service.get_event_persona_ids(
        db,
        event_ids=[event.event_id for event in events],
    )
    return PaginatedEventsResponse(
        items=[
            _event_response(event, persona_ids_by_event.get(event.event_id, []))
            for event in events
        ],
        nextCursor=next_cursor,
    )

@router.post(
    "/customers/events",
    response_model=EventCreateResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
def create_customer_event(
    body: EventCreateRequest,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    event = customer_service.create_customer_event(
        db,
        customer_id=current_customer.customer_id,
        event_type=body.event_type,
        title=body.title,
        persona_ids=body.persona_ids,
    )
    return EventCreateResponse(eventId=event.event_id, status=event.status)

@router.get(
    "/customers/events/{event_id}",
    response_model=EventResponse,
    response_model_by_alias=True,
)
def get_customer_event(
    event_id: str,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    event = customer_service.get_customer_event(
        db,
        event_id=event_id,
        customer_id=current_customer.customer_id,
    )
    persona_ids = customer_service.get_event_persona_ids(db, event_ids=[event.event_id]).get(event.event_id, [])
    return _event_response(event, persona_ids)

@router.put(
    "/customers/events/{event_id}/personas",
    response_model=EventResponse,
    response_model_by_alias=True,
)
def set_event_personas(
    event_id: str,
    body: SetEventPersonasRequest,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    event = customer_service.replace_event_personas(
        db,
        event_id=event_id,
        customer_id=current_customer.customer_id,
        persona_ids=body.persona_ids,
    )
    persona_ids = customer_service.get_event_persona_ids(db, event_ids=[event.event_id]).get(event.event_id, [])
    return _event_response(event, persona_ids)

@router.delete("/customers/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer_event(
    event_id: str,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    customer_service.delete_draft_event(
        db,
        event_id=event_id,
        customer_id=current_customer.customer_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Event Metadata Routes ---

@router.get("/event-types", response_model=StringListResponse)
def list_event_types(_: Customer = Depends(get_current_customer)):
    return StringListResponse(items=customer_service.list_event_types())

@router.get("/event-templates", response_model=StringListResponse)
def list_event_templates(_: Customer = Depends(get_current_customer)):
    return StringListResponse(items=customer_service.list_event_templates())


# --- Event Chat & Summary Routes ---

@router.post(
    "/customers/events/{event_id}/chat",
    response_model=ChatSendResponse,
    response_model_by_alias=True,
)
def send_event_chat_message(
    event_id: str,
    body: ChatSendRequest,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    reply, suggested_tasks = event_planning_service.send_chat_message(
        db,
        customer_id=current_customer.customer_id,
        event_id=event_id,
        content=body.content,
    )
    return ChatSendResponse(reply=reply, suggestedTasks=suggested_tasks)

@router.post(
    "/customers/events/{event_id}/summarize",
    response_model=EventSummaryResponse,
)
def summarize_event(
    event_id: str,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    return EventSummaryResponse(
        summary=event_planning_service.summarize_event_context(
            db,
            customer_id=current_customer.customer_id,
            event_id=event_id,
        )
    )

@router.get(
    "/customers/events/{event_id}/messages",
    response_model=PaginatedChatMessagesResponse,
    response_model_by_alias=True,
)
def list_event_messages(
    event_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    messages, next_cursor = event_planning_service.list_messages(
        db,
        customer_id=current_customer.customer_id,
        event_id=event_id,
        limit=limit,
        cursor=cursor,
    )
    return PaginatedChatMessagesResponse(
        items=[_message_response(message) for message in messages],
        nextCursor=next_cursor,
    )


# --- Event Task Routes ---

@router.get(
    "/customers/events/{event_id}/tasks",
    response_model=TaskListResponse,
    response_model_by_alias=True,
)
def list_event_tasks(
    event_id: str,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    tasks = event_planning_service.list_tasks(
        db,
        customer_id=current_customer.customer_id,
        event_id=event_id,
    )
    return TaskListResponse(items=[_task_response(task) for task in tasks])

@router.post(
    "/customers/events/{event_id}/tasks",
    response_model=TaskResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
def create_event_task(
    event_id: str,
    body: TaskCreateRequest,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    task = event_planning_service.create_task(
        db,
        customer_id=current_customer.customer_id,
        event_id=event_id,
        payload=body.model_dump(),
    )
    return _task_response(task)

@router.post(
    "/customers/events/{event_id}/tasks/confirm",
    response_model=ConfirmTasksResponse,
    response_model_by_alias=True,
)
def confirm_event_tasks(
    event_id: str,
    body: ConfirmTasksRequest | None = None,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    event, tasks = event_planning_service.confirm_tasks(
        db,
        customer_id=current_customer.customer_id,
        event_id=event_id,
        task_ids=body.task_ids if body else None,
    )
    persona_ids = customer_service.get_event_persona_ids(db, event_ids=[event.event_id]).get(event.event_id, [])
    return ConfirmTasksResponse(
        event=_event_response(event, persona_ids),
        tasks=[_task_response(task) for task in tasks],
    )

@router.put(
    "/customers/events/{event_id}/tasks/{task_id}",
    response_model=TaskResponse,
    response_model_by_alias=True,
)
def update_event_task(
    event_id: str,
    task_id: str,
    body: TaskUpdateRequest,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    task = event_planning_service.update_task(
        db,
        customer_id=current_customer.customer_id,
        event_id=event_id,
        task_id=task_id,
        payload=body.model_dump(exclude_none=True),
    )
    return _task_response(task)

@router.delete("/customers/events/{event_id}/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event_task(
    event_id: str,
    task_id: str,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    event_planning_service.delete_task(
        db,
        customer_id=current_customer.customer_id,
        event_id=event_id,
        task_id=task_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Event Schedule & Reminders ---

@router.get(
    "/customers/events/{event_id}/schedule",
    response_model=EventScheduleResponse,
    response_model_by_alias=True,
)
def get_event_schedule(
    event_id: str,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    event = event_planning_service.get_schedule(
        db,
        customer_id=current_customer.customer_id,
        event_id=event_id,
    )
    return _schedule_response(event)

@router.put(
    "/customers/events/{event_id}/schedule",
    response_model=EventScheduleResponse,
    response_model_by_alias=True,
)
def upsert_event_schedule(
    event_id: str,
    body: EventScheduleUpsertRequest,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    event = event_planning_service.upsert_schedule(
        db,
        customer_id=current_customer.customer_id,
        event_id=event_id,
        payload=body.model_dump(),
    )
    return _schedule_response(event)

@router.get(
    "/customers/events/{event_id}/reminders",
    response_model=EventRemindersResponse,
    response_model_by_alias=True,
)
def get_event_reminders(
    event_id: str,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    event = event_planning_service.get_reminders(
        db,
        customer_id=current_customer.customer_id,
        event_id=event_id,
    )
    return _reminders_response(event)

@router.put(
    "/customers/events/{event_id}/reminders",
    response_model=EventRemindersResponse,
    response_model_by_alias=True,
)
def upsert_event_reminders(
    event_id: str,
    body: EventRemindersUpsertRequest,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    event = event_planning_service.upsert_reminders(
        db,
        customer_id=current_customer.customer_id,
        event_id=event_id,
        payload=body.model_dump(),
    )
    return _reminders_response(event)

@router.get(
    "/customers/events/{event_id}/occurrences",
    response_model=PaginatedEventOccurrencesResponse,
    response_model_by_alias=True,
)
def list_event_occurrences(
    event_id: str,
    from_: datetime | None = Query(default=None, alias="from"),
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    occurrences, next_cursor = event_planning_service.list_occurrences(
        db,
        customer_id=current_customer.customer_id,
        event_id=event_id,
        from_dt=from_,
        limit=limit,
        cursor=cursor,
    )
    return PaginatedEventOccurrencesResponse(
        items=[EventOccurrenceResponse(**occurrence) for occurrence in occurrences],
        nextCursor=next_cursor,
    )


# --- Calendar Sync Routes ---

@router.get(
    "/customers/events/{event_id}/calendar-sync",
    response_model=EventCalendarSyncStatusResponse,
    response_model_by_alias=True,
)
def get_event_calendar_sync(
    event_id: str,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    event = event_planning_service.get_calendar_sync_status(
        db,
        customer_id=current_customer.customer_id,
        event_id=event_id,
    )
    return _event_calendar_sync_response(event)

@router.put(
    "/customers/events/{event_id}/calendar-sync",
    response_model=EventCalendarSyncStatusResponse,
    response_model_by_alias=True,
)
def upsert_event_calendar_sync(
    event_id: str,
    body: EventCalendarSyncUpsertRequest,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    event = event_planning_service.upsert_calendar_sync(
        db,
        customer_id=current_customer.customer_id,
        event_id=event_id,
        payload=body.model_dump(),
    )
    return _event_calendar_sync_response(event)

@router.get(
    "/customers/calendar/providers",
    response_model=CalendarProviderListResponse,
    response_model_by_alias=True,
)
def list_calendar_providers(_: Customer = Depends(get_current_customer)):
    return CalendarProviderListResponse(providers=event_planning_service.list_calendar_providers())

@router.post(
    "/customers/calendar/connect",
    response_model=CalendarConnectResponse,
    response_model_by_alias=True,
)
def start_calendar_connect(
    body: CalendarConnectRequest,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    return CalendarConnectResponse(
        **event_planning_service.start_calendar_connect(
            db,
            customer_id=current_customer.customer_id,
            provider=body.provider,
            redirect_uri=body.redirect_uri,
        )
    )

@router.post(
    "/customers/calendar/exchange-code",
    response_model=CalendarConnectionStatusResponse,
    response_model_by_alias=True,
)
def exchange_calendar_code(
    body: CalendarExchangeCodeRequest,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    customer = event_planning_service.exchange_calendar_code(
        db,
        customer_id=current_customer.customer_id,
        provider=body.provider,
        code=body.code,
        state=body.state,
    )
    return _calendar_status_response(customer)

@router.get(
    "/customers/calendar/status",
    response_model=CalendarConnectionStatusResponse,
    response_model_by_alias=True,
)
def get_calendar_status(
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    customer = event_planning_service.get_calendar_status(db, customer_id=current_customer.customer_id)
    return _calendar_status_response(customer)

@router.delete("/customers/calendar/disconnect", status_code=status.HTTP_204_NO_CONTENT)
def disconnect_calendar(
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    event_planning_service.disconnect_calendar(db, customer_id=current_customer.customer_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)