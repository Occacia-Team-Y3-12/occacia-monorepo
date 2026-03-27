from __future__ import annotations

from collections.abc import Iterable

from fastapi import HTTPException
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models import Customer
from app.models.event import Event
from app.models.event_persona import EventPersona
from app.models.persona import Persona


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

    def list_event_types(self) -> list[str]:
        return [
            "Individual",
            "Group",
            "Others",
        ]

    def get_customer_event(
        self,
        db: Session,
        *,
        event_id: str,
        customer_id: str,
    ) -> Event:
        event = (
            db.query(Event)
            .filter(
                Event.event_id == event_id,
                Event.customer_id == customer_id,
            )
            .first()
        )
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        return event

    def create_customer_event(
        self,
        db: Session,
        *,
        customer_id: str,
        event_type: str,
        title: str,
        persona_ids: Iterable[str] | None = None,
    ) -> Event:
        normalized_persona_ids = self._validate_persona_ids(
            db,
            customer_id=customer_id,
            persona_ids=persona_ids or [],
        )
        event = Event(
            customer_id=customer_id,
            event_type=event_type,
            title=title,
            status="DRAFT",
        )

        try:
            db.add(event)
            db.flush()

            for persona_id in normalized_persona_ids:
                db.add(EventPersona(event_id=event.event_id, persona_id=persona_id))

            db.commit()
        except Exception:
            db.rollback()
            raise

        db.refresh(event)
        return event

    def replace_event_personas(
        self,
        db: Session,
        *,
        event_id: str,
        customer_id: str,
        persona_ids: Iterable[str],
    ) -> Event:
        event = self.get_customer_event(db, event_id=event_id, customer_id=customer_id)
        normalized_persona_ids = self._validate_persona_ids(
            db,
            customer_id=customer_id,
            persona_ids=persona_ids,
        )

        try:
            (
                db.query(EventPersona)
                .filter(EventPersona.event_id == event.event_id)
                .delete(synchronize_session=False)
            )
            for persona_id in normalized_persona_ids:
                db.add(EventPersona(event_id=event.event_id, persona_id=persona_id))
            db.commit()
        except Exception:
            db.rollback()
            raise

        db.refresh(event)
        return event

    def delete_draft_event(
        self,
        db: Session,
        *,
        event_id: str,
        customer_id: str,
    ) -> None:
        event = self.get_customer_event(db, event_id=event_id, customer_id=customer_id)
        if event.status != "DRAFT":
            raise HTTPException(
                status_code=409,
                detail="Only draft events can be deleted",
            )

        try:
            (
                db.query(EventPersona)
                .filter(EventPersona.event_id == event.event_id)
                .delete(synchronize_session=False)
            )
            db.delete(event)
            db.commit()
        except Exception:
            db.rollback()
            raise

    def _validate_persona_ids(
        self,
        db: Session,
        *,
        customer_id: str,
        persona_ids: Iterable[str],
    ) -> list[str]:
        normalized_persona_ids = list(dict.fromkeys(persona_ids))
        if not normalized_persona_ids:
            return []

        found_persona_ids = {
            persona_id
            for (persona_id,) in (
                db.query(Persona.persona_id)
                .filter(
                    Persona.customer_id == customer_id,
                    Persona.persona_id.in_(normalized_persona_ids),
                )
                .all()
            )
        }
        missing_persona_ids = [
            persona_id for persona_id in normalized_persona_ids if persona_id not in found_persona_ids
        ]
        if missing_persona_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Persona not found: {missing_persona_ids[0]}",
            )

        return normalized_persona_ids


customer_service = CustomerService()