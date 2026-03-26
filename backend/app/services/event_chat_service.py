"""
app/services/event_chat_service.py

Single orchestrator for the Occi event chat flow (UC-13).

What this file owns:
  - Loading event, personas, history from DB
  - Building event_context (DB is the source of truth, not AI output)
  - Calling GroqAIService
  - Persisting AI-extracted facts back to the Event model
  - Saving persona drafts and linking them to the event
  - Persisting suggested tasks (dedup by name)
  - Pre-computing offering shortlists for newly created tasks
  - Returning a fully-typed ChatSendResponse

Key design guarantees:
  - event_context is built from DB columns every turn → Occi always sees full state.
  - AI-extracted facts are written back to DB so the NEXT turn's context is current.
  - missingInfo is authoritative (computed in groq_ai_service, not trusted from model).
  - Fallback reply is used when Groq is unreachable — no crash.
"""
from __future__ import annotations

import logging
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.event import Event
from app.models.event_chat_message import EventChatMessage
from app.models.event_persona import EventPersona
from app.models.persona import Persona
from app.models.task import Task
from app.schemas.event_planning_schema import ChatSendResponse, SuggestedTaskDraftResponse
from app.services.event_planning_service import event_planning_service
from app.services.groq_ai_service import groq_ai_service
from app.services.offering_service import offering_service
from app.services.persona_service import persona_service

logger = logging.getLogger(__name__)

_DEFAULT_TZ = "Asia/Colombo"
_MAX_HISTORY = 10   # messages loaded from DB for Groq context


class EventChatService:

    # ─────────────────────────────────────────────────────────────────────────
    # Public entry point
    # ─────────────────────────────────────────────────────────────────────────

    async def send_message(
        self,
        db: Session,
        customer: Customer,
        event_id: str,
        content: str,
    ) -> ChatSendResponse:
        customer_id = str(customer.customer_id)

        # 1 ── Load & validate event ──────────────────────────────────────────
        event: Event = db.query(Event).filter(Event.event_id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        if str(event.customer_id) != customer_id:
            raise HTTPException(status_code=403, detail="Not your event")

        # 2 ── Load linked personas ───────────────────────────────────────────
        personas: list[Persona] = (
            db.query(Persona)
            .join(EventPersona, EventPersona.persona_id == Persona.persona_id)
            .filter(EventPersona.event_id == event_id)
            .all()
        )
        # 3 ── Load chat history (oldest-first, capped at _MAX_HISTORY) ──────
        history: list[EventChatMessage] = (
            db.query(EventChatMessage)
            .filter(EventChatMessage.event_id == event_id)
            .order_by(EventChatMessage.sent_at.asc())
            .limit(_MAX_HISTORY)
            .all()
        )

        # 4 ── Determine needs_persona ────────────────────────────────────────
        event_type_upper = (event.event_type or "").upper()
        needs_persona    = event_type_upper != "GROUP" and not personas

        # 5 ── Build event_context from DB (source of truth every turn) ───────
        existing_tasks: list[Task] = (
            db.query(Task).filter(Task.event_id == event_id).all()
        )
        event_context = self._build_event_context(event, existing_tasks)

        # 6 ── Persist the customer message ───────────────────────────────────
        self._save_message(db, event_id=event_id, sender="CUSTOMER", content=content)

        # 7 ── Call Groq ───────────────────────────────────────────────────────
        try:
            ai_output = await groq_ai_service.plan_event_chat(
                content=content,
                history=history,
                personas=personas,
                event_context=event_context,
                needs_persona=needs_persona,
            )
        except Exception as exc:
            logger.exception("Groq call failed for event %s: %s", event_id, exc)
            fallback = (
                "Hmm, I'm having a bit of trouble connecting right now. "
                "I'm your planning assistant, so please keep adding tasks manually, "
                "and we'll pick up where we left off once I'm back online!"
            )
            self._save_message(db, event_id=event_id, sender="AI", content=fallback)
            return ChatSendResponse(
                reply=fallback,
                suggestedTasks=[],
                intent="chat",
                missingInfo=[],
                askSavePersona=False,
                personaSaved=False,
                personaConfirmed=False,
            )

        reply: str = ai_output.get("reply", "")

        # 8 ── Persist AI reply ────────────────────────────────────────────────
        self._save_message(db, event_id=event_id, sender="AI", content=reply)

        # 9 ── Write AI-extracted facts back to the Event model ────────────────
        self._persist_extracted_facts(db, event=event, ai_output=ai_output)

        # 10 ── Save persona draft if flagged ──────────────────────────────────
        persona_saved     = False
        persona_confirmed = False

        if ai_output.get("save_persona"):
            draft = ai_output.get("personaDraft") or {}
            name  = (draft.get("name") or "").strip()
            if name:
                try:
                    new_persona = persona_service.create_persona(
                        db,
                        customer_id=customer_id,
                        data={
                            "name":              name,
                            "relationship":      draft.get("relationship"),
                            "personality_tags":  draft.get("personality_tags") or [],
                            "food_preferences":  draft.get("food_preferences") or [],
                            "music_preferences": draft.get("music_preferences") or [],
                            "color_preferences": draft.get("color_preferences") or [],
                            "is_confirmed":      False,
                        },
                    )
                    self._link_persona(db, event_id=event_id, persona_id=new_persona.persona_id)
                    persona_saved = True
                    logger.info("Persona '%s' saved → event %s", name, event_id)
                except Exception as exc:
                    logger.warning("Persona save failed: %s", exc)

        # 11 ── Persist suggested tasks (dedup by lowercase name) ──────────────
        suggested_out: list[SuggestedTaskDraftResponse] = []
        existing_names = {t.name.lower() for t in existing_tasks}
        new_task_ids:  list[str] = []

        for t in (ai_output.get("suggestedTasks") or []):
            task_name = (t.get("name") or "").strip()
            if not task_name:
                continue

            suggested_out.append(
                SuggestedTaskDraftResponse(
                    name=task_name,
                    description=t.get("description"),
                    quantity=int(t.get("quantity") or 1),
                    currency=t.get("currency", "LKR"),
                )
            )

            if task_name.lower() not in existing_names:
                try:
                    task_obj = event_planning_service.create_task(
                        db,
                        customer_id=customer_id,
                        event_id=event_id,
                        payload={
                            "name":        task_name,
                            "description": t.get("description"),
                            "quantity":    int(t.get("quantity") or 1),
                            "currency":    t.get("currency", "LKR"),
                        },
                    )
                    new_task_ids.append(task_obj.task_id)
                    existing_names.add(task_name.lower())
                except Exception as exc:
                    logger.warning("Task persist failed '%s': %s", task_name, exc)

        # 12 ── Pre-compute offering shortlists for new tasks ──────────────────
        for task_id in new_task_ids:
            try:
                task_obj = db.query(Task).filter(Task.task_id == task_id).first()
                if not task_obj:
                    continue
                ranked = offering_service.find_offerings_for_task(
                    db=db, task=task_obj, limit=3,
                )
                if ranked:
                    offering_service.save_task_offering_shortlist(
                        db=db, task_id=task_id, offerings_with_rank=ranked,
                    )
            except Exception as exc:
                logger.warning("Shortlist failed for task %s: %s", task_id, exc)

        # 13 ── Return response ────────────────────────────────────────────────
        return ChatSendResponse(
            reply=reply,
            suggestedTasks=suggested_out,
            intent=ai_output.get("intent"),
            missingInfo=ai_output.get("missingInfo") or [],
            askSavePersona=bool(ai_output.get("save_persona") and not persona_saved),
            personaSaved=persona_saved,
            personaConfirmed=persona_confirmed,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Context builder  DB → prompt dict
    # ─────────────────────────────────────────────────────────────────────────

    def _build_event_context(
        self,
        event: Event,
        existing_tasks: list[Task],
    ) -> dict:
        """
        Build the canonical event_context dict from DB columns.
        This dict is passed to Groq every turn — it is the single source of truth.

        Soft facts (guest_count, budget, expectations) are encoded in
        event.description as a [FACTS:...] prefix until dedicated columns exist.
        """
        ctx: dict = {
            "title":           event.title,
            "event_type":      event.event_type,
            "event_date":      None,
            "location":        event.location_text or None,
            "guest_count":     None,
            "budget_total":    None,
            "budget_per_head": None,
            "expectations":    None,
            "existing_tasks":  [t.name for t in existing_tasks],
        }

        # Native date column
        if event.start_at:
            try:
                ctx["event_date"] = event.start_at.date().isoformat()
            except Exception:
                pass

        # Soft facts from description prefix
        soft = self._parse_facts(event.description or "")
        for key in ("guest_count", "budget_total", "budget_per_head", "expectations"):
            if soft.get(key):
                ctx[key] = soft[key]

        # Auto-compute budget_per_head if we have both
        if ctx["budget_total"] and ctx["guest_count"] and not ctx["budget_per_head"]:
            try:
                ctx["budget_per_head"] = round(
                    float(ctx["budget_total"]) / float(ctx["guest_count"]), 2
                )
            except (TypeError, ZeroDivisionError):
                pass

        return ctx

    # ─────────────────────────────────────────────────────────────────────────
    # Fact persistence  AI output → DB
    # ─────────────────────────────────────────────────────────────────────────

    def _persist_extracted_facts(
        self,
        db: Session,
        event: Event,
        ai_output: dict,
    ) -> None:
        """
        Write AI-extracted eventFacts back to the Event model so the next turn
        picks them up from the DB via _build_event_context.

        Strategy:
          • Native columns (start_at, timezone, location_text) — set directly.
          • Soft facts (guest_count, budget, expectations) — stored as a
            structured prefix in event.description.
          • Never overwrite an already-set native column with a new value
            unless the column was null — this prevents drift from corrections.
        """
        ef      = ai_output.get("eventFacts") or {}
        changed = False

        # ── Native: date ──────────────────────────────────────────────────────
        if ef.get("date") and not event.start_at:
            tz_str = ef.get("timezone") or _DEFAULT_TZ
            aware  = self._parse_date(ef["date"], tz_str)
            if aware:
                event.start_at = aware
                event.timezone = tz_str
                changed = True

        # ── Native: timezone only (no date change) ───────────────────────────
        if ef.get("timezone") and not event.timezone:
            event.timezone = ef["timezone"]
            changed = True

        # ── Native: location ─────────────────────────────────────────────────
        if ef.get("location") and not event.location_text:
            event.location_text = ef["location"]
            changed = True

        # ── Soft facts → description prefix ──────────────────────────────────
        current = self._parse_facts(event.description or "")
        soft_changed = False

        if ef.get("guestCount") and not current.get("guest_count"):
            current["guest_count"] = str(ef["guestCount"])
            soft_changed = True

        if ef.get("budgetTotal") and not current.get("budget_total"):
            current["budget_total"] = str(ef["budgetTotal"])
            soft_changed = True

        if ef.get("budgetPerHead") and not current.get("budget_per_head"):
            current["budget_per_head"] = str(ef["budgetPerHead"])
            soft_changed = True

        if ef.get("expectations") and not current.get("expectations"):
            current["expectations"] = str(ef["expectations"])[:300]
            soft_changed = True

        if soft_changed:
            event.description = self._write_facts(current, event.description or "")
            changed = True

        if changed:
            db.add(event)
            db.commit()
            logger.info(
                "Event %s updated | date=%s guests=%s budget=%s",
                event.event_id,
                ef.get("date"),
                ef.get("guestCount"),
                ef.get("budgetTotal"),
            )

    # ─────────────────────────────────────────────────────────────────────────
    # Description fact serialisation helpers
    # ─────────────────────────────────────────────────────────────────────────

    _PREFIX_START = "[FACTS:"
    _PREFIX_END   = "]\n"

    def _parse_facts(self, description: str) -> dict[str, str]:
        """Extract {key: value} from the [FACTS:k=v,k=v] prefix."""
        if not description.startswith(self._PREFIX_START):
            return {}
        end = description.find(self._PREFIX_END)
        if end == -1:
            return {}
        raw = description[len(self._PREFIX_START):end]
        result: dict[str, str] = {}
        for part in raw.split(","):
            if "=" in part:
                k, _, v = part.partition("=")
                k, v = k.strip(), v.strip()
                if k and v:
                    result[k] = v
        return result

    def _write_facts(self, facts: dict[str, str], existing: str) -> str:
        """Overwrite the [FACTS:...] prefix; keep the human-text body below."""
        if existing.startswith(self._PREFIX_START):
            end = existing.find(self._PREFIX_END)
            if end != -1:
                existing = existing[end + len(self._PREFIX_END):]
        pairs  = ",".join(f"{k}={v}" for k, v in facts.items() if v)
        prefix = f"{self._PREFIX_START}{pairs}{self._PREFIX_END}"
        return prefix + existing

    # ─────────────────────────────────────────────────────────────────────────
    # Date / timezone helpers
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_date(date_str: str, tz_str: str) -> datetime | None:
        """Parse YYYY-MM-DD → aware datetime at 09:00 local time."""
        try:
            naive = datetime.strptime(date_str.strip(), "%Y-%m-%d")
        except ValueError:
            logger.warning("Could not parse date: %s", date_str)
            return None
        try:
            tz = ZoneInfo(tz_str)
        except (ZoneInfoNotFoundError, Exception):
            tz = ZoneInfo("UTC")
        return datetime(naive.year, naive.month, naive.day, 9, 0, 0, tzinfo=tz)

    # ─────────────────────────────────────────────────────────────────────────
    # DB helpers
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _save_message(
        db: Session,
        *,
        event_id: str,
        sender: str,
        content: str,
    ) -> None:
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

    @staticmethod
    def _link_persona(db: Session, *, event_id: str, persona_id: str) -> None:
        exists = (
            db.query(EventPersona)
            .filter(
                EventPersona.event_id   == event_id,
                EventPersona.persona_id == persona_id,
            )
            .first()
        )
        if not exists:
            db.add(EventPersona(event_id=event_id, persona_id=persona_id))
            db.commit()


event_chat_service = EventChatService()



