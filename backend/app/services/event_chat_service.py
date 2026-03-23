"""
app/services/event_chat_service.py

Single orchestrator for the event chat flow.
Replaces the split rule-engine + planning-engine + merge logic in customer_router.py.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.event import Event
from app.models.event_persona import EventPersona
from app.models.persona import Persona
from app.models.task import Task
from app.schemas.event_planning_schema import ChatSendResponse, SuggestedTaskDraftResponse
from app.services.event_planning_service import event_planning_service
from app.services.groq_ai_service import groq_ai_service
from app.services.offering_service import offering_service
from app.services.persona_service import persona_service

logger = logging.getLogger(__name__)


class EventChatService:
    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    async def send_message(
        self,
        db: Session,
        customer: Customer,
        event_id: str,
        content: str,
    ) -> ChatSendResponse:
        customer_id = str(customer.customer_id)

        # ── 1. Load & validate event ──────────────────────────────────
        event: Event = (
            db.query(Event)
            .filter(Event.event_id == event_id)
            .first()
        )
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        if str(event.customer_id) != customer_id:
            raise HTTPException(status_code=403, detail="Not your event")

        # ── 2. Load linked personas ───────────────────────────────────
        personas: list[Persona] = (
            db.query(Persona)
            .join(EventPersona, EventPersona.persona_id == Persona.persona_id)
            .filter(EventPersona.event_id == event_id)
            .all()
        )

        # ── 3. Load recent chat history ───────────────────────────────
        from app.models.event_chat_message import EventChatMessage
        history = (
            db.query(EventChatMessage)
            .filter(EventChatMessage.event_id == event_id)
            .order_by(EventChatMessage.sent_at.desc())
            .limit(10)
            .all()
        )
        history = list(reversed(history))  # oldest first for prompt

        # ── 4. Determine needs_persona ────────────────────────────────
        event_type_upper = (event.event_type or "").upper()
        if event_type_upper == "GROUP":
            needs_persona = False
        elif not personas:
            needs_persona = True
        else:
            needs_persona = False

        # ── 5. Load tasks ─────────────────────────────────────────────
        tasks: list[Task] = (
            db.query(Task)
            .filter(Task.event_id == event_id)
            .all()
        )

        # ── 6. Build event context dict ───────────────────────────────
        event_context = {
            "title":          event.title,
            "event_type":     event.event_type,
            "event_date":     event.start_at.date().isoformat() if event.start_at else None,
            "location":       event.location_text,
            "existing_tasks": [t.name for t in tasks],
        }

        # ── 7. Persist user message ───────────────────────────────────
        event_planning_service.save_ai_reply.__func__  # just a check; use private helper
        self._save_message(db, event_id=event_id, sender="CUSTOMER", content=content)

        # ── 8. Call Groq ──────────────────────────────────────────────
        ai_output = await groq_ai_service.plan_event_chat(
            content=content,
            history=history,
            personas=personas,
            event_context=event_context,
            needs_persona=needs_persona,
        )

        reply: str = ai_output.get("reply", "")

        # ── 9. Persist AI reply ───────────────────────────────────────
        self._save_message(db, event_id=event_id, sender="AI", content=reply)

        # ── 10. Post-process structured output ────────────────────────
        persona_saved    = False
        persona_confirmed = False

        # 10a. Save persona draft if requested
        if ai_output.get("save_persona"):
            draft = ai_output.get("personaDraft") or {}
            if draft.get("name"):
                try:
                    persona_data = {
                        "name":               draft["name"],
                        "relationship":       draft.get("relationship"),
                        "personality_tags":   draft.get("personality_tags") or [],
                        "food_preferences":   draft.get("food_preferences") or [],
                        "music_preferences":  draft.get("music_preferences") or [],
                        "color_preferences":  draft.get("color_preferences") or [],
                        "is_confirmed":       False,
                    }
                    new_persona = persona_service.create_persona(db, customer_id=customer_id, data=persona_data)
                    self._link_persona_to_event(db, event_id=event_id, persona_id=new_persona.persona_id)
                    persona_saved = True
                    logger.info("Persona saved and linked: %s → event %s", new_persona.persona_id, event_id)
                except Exception as exc:
                    logger.warning("Failed to save persona draft: %s", exc)

        # 10b. Update event date if extracted
        event_facts = ai_output.get("eventFacts") or {}
        if event_facts.get("date"):
            try:
                self._update_event_date(
                    db,
                    event=event,
                    date_str=event_facts["date"],
                    timezone_str=event_facts.get("timezone") or "Asia/Colombo",
                )
            except Exception as exc:
                logger.warning("Failed to update event date: %s", exc)

        # 10c. Persist suggested tasks (skip duplicates by name)
        suggested_tasks_out: list[SuggestedTaskDraftResponse] = []
        existing_task_names = {t.name.lower() for t in tasks}
        newly_created_task_ids: list[str] = []
        raw_suggested = ai_output.get("suggestedTasks") or []
        for t in raw_suggested:
            task_name = (t.get("name") or "").strip()
            if not task_name:
                continue
            suggested_tasks_out.append(
                SuggestedTaskDraftResponse(
                    name=task_name,
                    description=t.get("description"),
                    quantity=t.get("quantity", 1),
                    currency=t.get("currency", "LKR"),
                )
            )
            if task_name.lower() not in existing_task_names:
                try:
                    task_obj = event_planning_service.create_task(
                        db,
                        customer_id=customer_id,
                        event_id=event_id,
                        payload={
                            "name":        task_name,
                            "description": t.get("description"),
                            "quantity":    t.get("quantity", 1),
                            "currency":    t.get("currency", "LKR"),
                        },
                    )
                    newly_created_task_ids.append(task_obj.task_id)
                    existing_task_names.add(task_name.lower())
                except Exception as exc:
                    logger.warning("Failed to persist task '%s': %s", task_name, exc)

        # 10d. Precompute shortlist for newly created tasks (chat-time capped at 3)
        for task_id in newly_created_task_ids:
            try:
                task_obj = db.query(Task).filter(Task.task_id == task_id).first()
                if not task_obj:
                    continue
                offerings_with_rank = offering_service.find_offerings_for_task(
                    db=db,
                    task=task_obj,
                    limit=3,
                )
                if offerings_with_rank:
                    offering_service.save_task_offering_shortlist(
                        db=db,
                        task_id=task_id,
                        offerings_with_rank=offerings_with_rank,
                    )
            except Exception as exc:
                logger.warning("Failed to shortlist offerings for task %s: %s", task_id, exc)

        # ── 11. Build and return response ─────────────────────────────
        return ChatSendResponse(
            reply=reply,
            suggestedTasks=suggested_tasks_out,
            intent=ai_output.get("intent"),
            missingInfo=ai_output.get("missingInfo") or [],
            askSavePersona=bool(ai_output.get("save_persona") and not persona_saved),
            personaSaved=persona_saved,
            personaConfirmed=persona_confirmed,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _save_message(self, db: Session, *, event_id: str, sender: str, content: str) -> None:
        from app.models.event_chat_message import EventChatMessage
        from app.common.utils import generate_prefixed_id, now_utc
        msg = EventChatMessage(
            message_id=generate_prefixed_id("MSG"),
            event_id=event_id,
            sender=sender,
            content=content,
            sent_at=now_utc(),
        )
        db.add(msg)
        db.commit()

    def _link_persona_to_event(self, db: Session, *, event_id: str, persona_id: str) -> None:
        existing = (
            db.query(EventPersona)
            .filter(
                EventPersona.event_id == event_id,
                EventPersona.persona_id == persona_id,
            )
            .first()
        )
        if not existing:
            link = EventPersona(event_id=event_id, persona_id=persona_id)
            db.add(link)
            db.commit()

    def _update_event_date(
        self,
        db: Session,
        *,
        event: Event,
        date_str: str,
        timezone_str: str,
    ) -> None:
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
        try:
            tz = ZoneInfo(timezone_str)
        except (ZoneInfoNotFoundError, Exception):
            tz = ZoneInfo("Asia/Colombo")

        try:
            naive_date = datetime.strptime(date_str, "%Y-%m-%d")
            aware_dt   = naive_date.replace(tzinfo=tz)
        except ValueError:
            logger.warning("Could not parse date string: %s", date_str)
            return

        event.start_at = aware_dt
        if not event.timezone:
            event.timezone = timezone_str
        db.add(event)
        db.commit()
        logger.info("Event %s date updated to %s", event.event_id, date_str)


event_chat_service = EventChatService()
