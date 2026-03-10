from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models import Customer
from app.models.event import Event
from app.models.event_persona import EventPersona


class CustomerService:
    def get_customer_by_email(self, db: Session, email: str) -> Customer | None:
        return db.query(Customer).filter(Customer.email == email).first()

    def update_customer_profile(
        self,
        db: Session,
        customer: Customer,
        *,
        full_name: str | None = None,
        phone: str | None = None,
        locale: str | None = None,
    ) -> Customer:
        if full_name is not None:
            customer.full_name = full_name
        if phone is not None:
            customer.phone = phone
        if locale is not None:
            customer.locale = locale

        db.add(customer)
        db.commit()
        db.refresh(customer)
        return customer

    def list_customer_events(
        self,
        db: Session,
        *,
        customer_id: str,
        status: str | None = None,
        limit: int = 20,
        cursor: str | None = None,
    ) -> tuple[list[Event], str | None]:
        query = db.query(Event).filter(Event.customer_id == customer_id)

        if status:
            query = query.filter(Event.status == status)

        if cursor:
            cursor_event = (
                db.query(Event)
                .filter(
                    Event.event_id == cursor,
                    Event.customer_id == customer_id,
                )
                .first()
            )
            if cursor_event:
                query = query.filter(
                    or_(
                        Event.created_at < cursor_event.created_at,
                        and_(
                            Event.created_at == cursor_event.created_at,
                            Event.id < cursor_event.id,
                        ),
                    )
                )

        events = (
            query.order_by(Event.created_at.desc(), Event.id.desc())
            .limit(limit + 1)
            .all()
        )

        next_cursor = None
        if len(events) > limit:
            next_cursor = events[limit - 1].event_id
            events = events[:limit]

        return events, next_cursor

    def get_event_persona_ids(
        self,
        db: Session,
        *,
        event_ids: Iterable[str],
    ) -> dict[str, list[str]]:
        event_ids = list(event_ids)
        if not event_ids:
            return {}

        links = (
            db.query(EventPersona)
            .filter(EventPersona.event_id.in_(event_ids))
            .all()
        )

        persona_ids_by_event: dict[str, list[str]] = {event_id: [] for event_id in event_ids}
        for link in links:
            persona_ids_by_event.setdefault(link.event_id, []).append(link.persona_id)

        return persona_ids_by_event

    def list_event_templates(self) -> list[str]:
        return [
            "Birthday",
            "Family Gathering",
            "Shopping",
        ]


customer_service = CustomerService()