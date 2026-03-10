"""
Routes per OpenAPI contract:
  GET /customers/me
  PUT /customers/me
  GET /customers/events
  GET /event-templates
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.customer import Customer
from app.routers.v1.auth_router import get_current_customer
from app.schemas.customer_schema import (
    CustomerProfileResponse,
    CustomerProfileUpdateRequest,
    EventResponse,
    PaginatedEventsResponse,
    StringListResponse,
)
from app.services.customer_service import customer_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Customer"])


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


# ── GET /customers/me ─────────────────────────────────────────────────

@router.get("/customers/me", response_model=CustomerProfileResponse, response_model_by_alias=True)
def get_customer_me(current_customer: Customer = Depends(get_current_customer)):
    """Get current customer profile. Spec: GET /customers/me"""
    return _customer_response(current_customer)


# ── PUT /customers/me ─────────────────────────────────────────────────

@router.put("/customers/me", response_model=CustomerProfileResponse, response_model_by_alias=True)
def update_customer_me(
    body: CustomerProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    """Update current customer profile. Spec: PUT /customers/me"""
    updated_customer = customer_service.update_customer_profile(
        db,
        current_customer,
        full_name=body.full_name,
        phone=body.phone,
        locale=body.locale,
    )
    return _customer_response(updated_customer)


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


@router.get("/event-templates", response_model=StringListResponse)
def list_event_templates(_: Customer = Depends(get_current_customer)):
    return StringListResponse(items=customer_service.list_event_templates())
