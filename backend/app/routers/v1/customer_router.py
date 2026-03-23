"""
app/routers/v1/customer_router.py

Customer profile management, event creation, and event planning (UC-13) routes.
"""
from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.customer import Customer
from app.models.task import Task
from app.models.package_execution_request import PackageExecutionRequest
from app.models.task_request import TaskRequest
from app.core.dependencies import get_current_customer
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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
from app.schemas.recommendation_schema import (
    CreateCustomPackageRequest,
    RecommendationPackageDetailsResponse,
    RecommendationPackageListResponse,
    TaskRecommendationListResponse,
    UpdateCustomPackageRequest,
)
from app.schemas.inquiry_schema import (
    InquiryCreate,
    InquiryResponse,
    PaginatedInquiriesResponse,
)
from app.schemas.offering_schema import TaskOfferingListResponse, TaskOfferingResponse
from app.schemas.package_schema import (
    ConfirmPackageOrderResponse,
    FulfillmentRequestResponse,
    PackageOrderDetailsResponse,
    PackageOrderResponse,
    PaginatedPackageOrdersResponse,
    ReassignTaskRequest,
    ReassignTaskResponse,
)
from app.services.customer_service import customer_service
from app.services.event_planning_service import event_planning_service
from app.services.package_order_service import package_order_service
from app.services.recommendation_service import recommendation_service
from app.services.event_chat_service import event_chat_service
from app.services.offering_service import offering_service
from app.services.inquiry_service import inquiry_service

_bearer = HTTPBearer(auto_error=False)


def get_authenticated_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
):
    from fastapi import HTTPException as _HTTPEx
    from app.core.security import decode_token as _decode
    from app.models.vendor import Vendor as _Vendor

    if credentials is None:
        raise _HTTPEx(status_code=401, detail="Not authenticated")

    token = credentials.credentials

    try:
        payload = _decode(token)
        email: str | None = payload.get("sub")
    except Exception:
        raise _HTTPEx(status_code=401, detail="Invalid or expired token")

    if not email:
        raise _HTTPEx(status_code=401, detail="Invalid token payload")

    customer = db.query(Customer).filter(Customer.email == email).first()
    if customer:
        return customer

    vendor = db.query(_Vendor).filter(_Vendor.email == email).first()
    if vendor:
        return vendor

    raise _HTTPEx(status_code=401, detail="User not found")


logger = logging.getLogger(__name__)
router = APIRouter(tags=["Customer"])


# ── Response Builders ─────────────────────────────────────────────────────────

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
        timezone=event.timezone,
        isAllDay=event.is_all_day,
        recurrenceRule=event.recurrence_rule,
        recurrenceUntil=event.recurrence_until,
        recurrenceCount=event.recurrence_count,
        remindersEnabled=event.reminders_enabled,
        reminderChannels=event.reminder_channels or [],
        reminderOffsets=event.reminder_offsets or [],
        reminderScheduleStatus=event.reminder_schedule_status,
        calendarSyncState=event.calendar_sync_state,
        calendarSyncProvider=event.calendar_sync_provider,
        calendarSyncCalendarId=event.calendar_sync_calendar_id,
        externalCalendarEventId=event.external_calendar_event_id,
        calendarLastSyncAt=event.calendar_last_sync_at,
        calendarLastSyncStatus=event.calendar_last_sync_status,
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
        needsVendor=bool(task.needs_vendor),
        vendorCategory=task.needs_vendor,
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

def _package_order_response(order: PackageExecutionRequest) -> PackageOrderResponse:
    return PackageOrderResponse(
        packageOrderId=order.execution_request_id,
        eventId=order.event_id,
        packageId=order.package_id,
        packageOrderTotalPrice=order.package_total_price,
        currency=order.currency,
        status=order.status,
        createdAt=order.created_at,
        statusUpdatedAt=order.status_updated_at,
        notes=order.notes,
        idempotencyKey=order.idempotency_key,
    )

def _fulfillment_request_response(request: TaskRequest) -> FulfillmentRequestResponse:
    return FulfillmentRequestResponse(
        fulfillmentRequestId=request.request_id,
        packageOrderId=request.package_order_id,
        taskId=request.task_id,
        vendorId=request.vendor_id,
        offeringId=request.offering_id,
        status=request.status,
        requestedAt=request.requested_at,
        respondBy=request.respond_by,
        respondedAt=request.responded_at,
        responseNote=request.response_note,
        attemptNo=request.attempt_no,
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
        calendarLink=event_planning_service.build_calendar_link(event),
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


# ── Customer Profile Routes ───────────────────────────────────────────────────

@router.get("/customers/me", response_model=CustomerProfileResponse, response_model_by_alias=True)
def get_customer_me(current_customer: Customer = Depends(get_current_customer)):
    return _customer_response(current_customer)

@router.put("/customers/me", response_model=CustomerProfileResponse, response_model_by_alias=True)
def update_customer_me(
    body: CustomerProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    updated_customer = customer_service.update_customer_profile(
        db,
        current_customer,
        full_name=body.full_name,
        phone=body.phone,
        locale=body.locale,
    )
    return _customer_response(updated_customer)


# ── Customer Event Routes ─────────────────────────────────────────────────────

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


# ── Event Metadata Routes ─────────────────────────────────────────────────────

@router.get("/event-types", response_model=StringListResponse)
def list_event_types(_=Depends(get_authenticated_user)):
    return StringListResponse(items=customer_service.list_event_types())

@router.get("/event-templates", response_model=StringListResponse)
def list_event_templates(_=Depends(get_authenticated_user)):
    return StringListResponse(items=customer_service.list_event_templates())


# ── Event Chat & Summary Routes ───────────────────────────────────────────────

@router.post(
    "/customers/events/{event_id}/chat",
    response_model=ChatSendResponse,
    response_model_by_alias=True,
)
async def send_event_chat_message(
    event_id: str,
    body: ChatSendRequest,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    """
    Unified event chat endpoint (UC-13).
    Delegates entirely to event_chat_service which orchestrates:
      - event + persona + history loading
      - Groq AI call (structured JSON output)
      - persona save + event date update + task persistence
      - message persistence
    """
    return await event_chat_service.send_message(
        db=db,
        customer=current_customer,
        event_id=event_id,
        content=body.content,
    )

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


# ── Event Task Routes ─────────────────────────────────────────────────────────

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

@router.post(
    "/customers/events/{event_id}/tasks/{task_id}/reassign",
    response_model=ReassignTaskResponse,
    response_model_by_alias=True,
)
def reassign_event_task(
    event_id: str,
    task_id: str,
    body: ReassignTaskRequest,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    task, fulfillment_request = package_order_service.reassign_rejected_task(
        db,
        customer_id=current_customer.customer_id,
        event_id=event_id,
        task_id=task_id,
        offering_id=body.offeringId,
    )
    return ReassignTaskResponse(
        task=_task_response(task),
        fulfillmentRequest=_fulfillment_request_response(fulfillment_request),
    )


@router.get(
    "/customers/events/{event_id}/tasks/{task_id}/offerings",
    response_model=TaskOfferingListResponse,
    response_model_by_alias=True,
)
def get_task_offerings(
    event_id: str,
    task_id: str,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    event_planning_service.get_event_for_customer(
        db,
        customer_id=str(current_customer.customer_id),
        event_id=event_id,
    )
    task = db.query(Task).filter(Task.task_id == task_id, Task.event_id == event_id).first()
    if not task:
        from fastapi import HTTPException as _HTTPEx
        raise _HTTPEx(status_code=404, detail="Task not found")
    task_offerings = offering_service.get_task_offerings(db, task_id=task_id)
    items = []
    for task_offering in task_offerings:
        offering = task_offering.offering
        vendor_name = None
        if offering and offering.vendor:
            vendor_name = getattr(offering.vendor, "display_name", None) or getattr(
                offering.vendor, "business_name", None
            )
        items.append(
            TaskOfferingResponse(
                offeringId=offering.offering_id,
                name=offering.name,
                category=offering.category,
                description=offering.description,
                price=offering.price,
                currency=offering.currency,
                unit=offering.unit,
                qualityTier=offering.quality_tier,
                vendorId=offering.vendor_id,
                vendorName=vendor_name,
                rank=task_offering.rank,
                score=task_offering.score,
                isSelected=task_offering.is_selected,
                selectedAt=task_offering.selected_at,
            )
        )
    return TaskOfferingListResponse(items=items)


@router.post(
    "/customers/events/{event_id}/tasks/{task_id}/offerings/{offering_id}/select",
    response_model=TaskOfferingResponse,
    response_model_by_alias=True,
)
def select_task_offering(
    event_id: str,
    task_id: str,
    offering_id: str,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    event_planning_service.get_event_for_customer(
        db,
        customer_id=str(current_customer.customer_id),
        event_id=event_id,
    )
    task = db.query(Task).filter(Task.task_id == task_id, Task.event_id == event_id).first()
    if not task:
        from fastapi import HTTPException as _HTTPEx
        raise _HTTPEx(status_code=404, detail="Task not found")
    task_offering = offering_service.select_offering(
        db,
        task_id=task_id,
        offering_id=offering_id,
        customer_id=str(current_customer.customer_id),
    )
    offering = task_offering.offering
    vendor_name = None
    if offering and offering.vendor:
        vendor_name = getattr(offering.vendor, "display_name", None) or getattr(
            offering.vendor, "business_name", None
        )
    return TaskOfferingResponse(
        offeringId=offering.offering_id,
        name=offering.name,
        category=offering.category,
        description=offering.description,
        price=offering.price,
        currency=offering.currency,
        unit=offering.unit,
        qualityTier=offering.quality_tier,
        vendorId=offering.vendor_id,
        vendorName=vendor_name,
        rank=task_offering.rank,
        score=task_offering.score,
        isSelected=task_offering.is_selected,
        selectedAt=task_offering.selected_at,
    )


# ── Event Recommendation Package Routes ───────────────────────────────────────

@router.post(
    "/customers/events/{event_id}/recommendations",
    response_model=RecommendationPackageListResponse,
    response_model_by_alias=True,
)
def generate_event_recommendations(
    event_id: str,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    return recommendation_service.generate_packages(
        db,
        customer_id=current_customer.customer_id,
        event_id=event_id,
    )

@router.get(
    "/customers/events/{event_id}/tasks/{task_id}/recommendations",
    response_model=TaskRecommendationListResponse,
    response_model_by_alias=True,
)
def get_event_task_recommendations(
    event_id: str,
    task_id: str,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    return recommendation_service.get_task_recommendations(
        db,
        customer_id=current_customer.customer_id,
        event_id=event_id,
        task_id=task_id,
    )

@router.get(
    "/customers/events/{event_id}/packages",
    response_model=RecommendationPackageListResponse,
    response_model_by_alias=True,
)
def list_event_recommendation_packages(
    event_id: str,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    return recommendation_service.get_packages(
        db,
        customer_id=current_customer.customer_id,
        event_id=event_id,
    )

@router.get(
    "/customers/events/{event_id}/packages/{package_id}",
    response_model=RecommendationPackageDetailsResponse,
    response_model_by_alias=True,
)
def get_event_recommendation_package(
    event_id: str,
    package_id: str,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    return recommendation_service.get_package_by_id(
        db,
        customer_id=current_customer.customer_id,
        event_id=event_id,
        package_id=package_id,
    )

@router.post(
    "/customers/events/{event_id}/packages",
    response_model=RecommendationPackageDetailsResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
def create_event_custom_package(
    event_id: str,
    payload: CreateCustomPackageRequest,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    return recommendation_service.create_custom_package(
        db,
        customer_id=current_customer.customer_id,
        event_id=event_id,
        request=payload,
    )

@router.put(
    "/customers/events/{event_id}/packages/{package_id}",
    response_model=RecommendationPackageDetailsResponse,
    response_model_by_alias=True,
)
def update_event_custom_package(
    event_id: str,
    package_id: str,
    payload: UpdateCustomPackageRequest,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    return recommendation_service.update_custom_package(
        db,
        customer_id=current_customer.customer_id,
        event_id=event_id,
        package_id=package_id,
        request=payload,
    )

@router.delete(
    "/customers/events/{event_id}/packages/{package_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_event_custom_package(
    event_id: str,
    package_id: str,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    recommendation_service.delete_custom_package(
        db,
        customer_id=current_customer.customer_id,
        event_id=event_id,
        package_id=package_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post(
    "/customers/events/{event_id}/packages/{package_id}/confirm",
    response_model=ConfirmPackageOrderResponse,
    response_model_by_alias=True,
)
def confirm_event_package(
    event_id: str,
    package_id: str,
    idempotency_key: UUID = Header(alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    order, tasks, fulfillment_requests = package_order_service.confirm_package_order(
        db,
        customer_id=current_customer.customer_id,
        event_id=event_id,
        package_id=package_id,
        idempotency_key=str(idempotency_key),
    )
    return ConfirmPackageOrderResponse(
        packageOrder=_package_order_response(order),
        tasks=[_task_response(task) for task in tasks],
        fulfillmentRequests=[
            _fulfillment_request_response(request)
            for request in fulfillment_requests
        ],
    )

@router.get(
    "/customers/events/{event_id}/package-orders",
    response_model=PaginatedPackageOrdersResponse,
    response_model_by_alias=True,
)
def list_event_package_orders(
    event_id: str,
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = Query(None),
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    items, next_cursor = event_planning_service.list_package_orders(
        db,
        customer_id=current_customer.customer_id,
        event_id=event_id,
        limit=limit,
        cursor=cursor,
    )
    return PaginatedPackageOrdersResponse(
        items=[_package_order_response(item) for item in items],
        nextCursor=next_cursor,
    )

@router.get(
    "/customers/package-orders",
    response_model=PaginatedPackageOrdersResponse,
    response_model_by_alias=True,
)
def list_customer_package_orders(
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = Query(None),
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    items, next_cursor = package_order_service.list_customer_package_orders(
        db,
        customer_id=current_customer.customer_id,
        limit=limit,
        cursor=cursor,
    )
    return PaginatedPackageOrdersResponse(
        items=[_package_order_response(item) for item in items],
        nextCursor=next_cursor,
    )

@router.get(
    "/customers/package-orders/{package_order_id}",
    response_model=PackageOrderDetailsResponse,
    response_model_by_alias=True,
)
def get_customer_package_order(
    package_order_id: str,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    order, tasks = package_order_service.get_customer_package_order_detail(
        db,
        customer_id=current_customer.customer_id,
        package_order_id=package_order_id,
    )
    return PackageOrderDetailsResponse(
        packageOrder=_package_order_response(order),
        tasks=[_task_response(task) for task in tasks],
    )


# --- Inquiries ---

@router.get(
    "/customers/inquiries",
    response_model=PaginatedInquiriesResponse,
    response_model_by_alias=True,
)
def list_customer_inquiries(
    status: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    items, next_cursor = inquiry_service.list_user_inquiries(
        db,
        user_id=str(current_customer.customer_id),
        status=status,
        limit=limit,
        cursor=cursor,
    )
    return PaginatedInquiriesResponse(
        items=[InquiryResponse.model_validate(item) for item in items],
        nextCursor=next_cursor,
    )


@router.post(
    "/customers/inquiries",
    response_model=InquiryResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
def create_customer_inquiry(
    payload: InquiryCreate,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    inquiry = inquiry_service.create_inquiry(
        db,
        user_id=str(current_customer.customer_id),
        role="CUSTOMER",
        subject=payload.subject,
        message=payload.message,
    )
    return InquiryResponse.model_validate(inquiry)


@router.get(
    "/customers/inquiries/{inquiry_id}",
    response_model=InquiryResponse,
    response_model_by_alias=True,
)
def get_customer_inquiry(
    inquiry_id: str,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    inquiry = inquiry_service.get_user_inquiry(
        db,
        inquiry_id=inquiry_id,
        user_id=str(current_customer.customer_id),
    )
    return InquiryResponse.model_validate(inquiry)


# --- Package Order Cancellation ---

@router.put(
    "/customers/package-orders/{package_order_id}/cancel",
    response_model=PackageOrderDetailsResponse,
    response_model_by_alias=True,
)
def cancel_customer_package_order(
    package_order_id: str,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    order = package_order_service.cancel_package_order(
        db,
        package_order_id=package_order_id,
        cancelled_by="CUSTOMER",
        customer_id=str(current_customer.customer_id),
    )
    tasks = package_order_service.get_order_tasks(db, package_order_id=package_order_id)
    return PackageOrderDetailsResponse(
        packageOrder=_package_order_response(order),
        tasks=[_task_response(task) for task in tasks],
    )


# ── Event Schedule & Reminders ────────────────────────────────────────────────

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


# ── Calendar Sync Routes ──────────────────────────────────────────────────────

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
        redirect_uri=body.redirect_uri,
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
