"""
app/services/event_chat_service.py

Orchestrator for the Occi event chat flow.

Phase flow:
  0 — PERSONA COLLECTION   : learn about the person the event is for
  1 — EVENT PURPOSE         : clarify the occasion
  2 — EVENT LOGISTICS       : date · guest count · budget · location
  3 — TASK GENERATION       : generate exactly 5 tailored tasks
  4 — COMPLETE              : follow-up, refinement, additions

One offering is shortlisted per task (best match by category + score).
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
from app.services.groq_ai_service import (
    PHASE_COMPLETE,
    PHASE_EVENT_LOGISTICS,
    PHASE_EVENT_PURPOSE,
    PHASE_PERSONA_COLLECTION,
    PHASE_TASK_GENERATION,
    groq_ai_service,
)
from app.services.offering_service import offering_service
from app.services.persona_service import persona_service

logger = logging.getLogger(__name__)

_DEFAULT_TZ  = "Asia/Colombo"
_MAX_HISTORY = 10

# These mirror the field_key values in PERSONA_QUESTIONS so _persona_missing_fields
# returns the same keys the prompt builder understands.
_PERSONA_REQUIRED_FIELDS: list[tuple[str, str | None]] = [
    # (model attribute,  missing-field key)
    ("name",              "name"),
    ("relationship",      "relationship"),
    ("birthday",          "age"),           # Persona stores age info via birthday
    ("gender",            "gender"),
    ("personality_tags",  "personality_tags"),
    ("food_preferences",  "food_preferences"),
    ("music_preferences", "music_preferences"),
    ("color_preferences", "color_preferences"),
    ("location",          "location"),
]


class EventChatService:

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

        # 3 ── Load recent chat history ───────────────────────────────────────
        history: list[EventChatMessage] = (
            db.query(EventChatMessage)
            .filter(EventChatMessage.event_id == event_id)
            .order_by(EventChatMessage.sent_at.asc())
            .limit(_MAX_HISTORY)
            .all()
        )

        # 4 ── Build event context ────────────────────────────────────────────
        existing_tasks: list[Task] = (
            db.query(Task).filter(Task.event_id == event_id).all()
        )
        event_context = self._build_event_context(event, existing_tasks)

        # 5 ── Determine phase ────────────────────────────────────────────────
        current_phase, needs_persona, persona_missing_fields = self._determine_phase(
            event_context=event_context,
            personas=personas,
            event=event,
        )

        # 6 ── Persist the customer message ───────────────────────────────────
        self._save_message(db, event_id=event_id, sender="CUSTOMER", content=content)

        # 7 ── Call Groq ──────────────────────────────────────────────────────
        try:
            ai_output = await groq_ai_service.plan_event_chat(
                content=content,
                history=history,
                personas=personas,
                event_context=event_context,
                needs_persona=needs_persona,
                persona_missing_fields=persona_missing_fields,
                current_phase=current_phase,
            )
        except Exception as exc:
            logger.exception("Groq call failed for event %s: %s", event_id, exc)
            fallback = (
                "I'm your planning assistant, but I'm having a bit of trouble connecting "
                "right now — sorry about that! Please feel free to keep adding details, "
                "and I'll pick right back up once I'm back online."
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

        # 8 ── Persist AI reply ───────────────────────────────────────────────
        self._save_message(db, event_id=event_id, sender="AI", content=reply)

        # 9 ── Write AI-extracted facts to Event ─────────────────────────────
        self._persist_extracted_facts(db, event=event, ai_output=ai_output)

        # 10 ── Handle persona draft ──────────────────────────────────────────
        persona_saved     = False
        persona_confirmed = False

        if ai_output.get("save_persona"):
            draft = ai_output.get("personaDraft") or {}
            name  = (draft.get("name") or "").strip()

            if name:
                # Check if persona already linked to this event
                existing = next(
                    (p for p in personas if (p.name or "").lower() == name.lower()),
                    None,
                )

                if existing:
                    update_data = self._build_persona_update(draft, existing)
                    if update_data:
                        try:
                            persona_service.update_persona(
                                db,
                                persona_id=existing.persona_id,
                                customer_id=customer_id,
                                data=update_data,
                            )
                            persona_saved = True
                            logger.info("Persona '%s' updated for event %s", name, event_id)
                        except Exception as exc:
                            logger.warning("Persona update failed: %s", exc)
                else:
                    try:
                        # Build full candidate dict from AI draft.
                        # age is not a model column — map it to birthday if birthday absent.
                        raw_age      = draft.get("age")
                        raw_birthday = draft.get("birthday")
                        birthday_val = raw_birthday or (f"age:{raw_age}" if raw_age else None)

                        candidate = {
                            "name":              name,
                            "relationship":      draft.get("relationship"),
                            "gender":            draft.get("gender"),
                            "birthday":          birthday_val,
                            "location":          draft.get("location"),
                            "personality_tags":  draft.get("personality_tags")  or [],
                            "food_preferences":  draft.get("food_preferences")  or [],
                            "music_preferences": draft.get("music_preferences") or [],
                            "color_preferences": draft.get("color_preferences") or [],
                            "interests":         draft.get("interests")         or [],
                            "is_confirmed":      False,
                        }

                        # Filter to only columns the Persona model actually declares
                        # so unknown fields never raise TypeError on create.
                        data = self._filter_to_model_columns(Persona, candidate)

                        new_persona = persona_service.create_persona(
                            db,
                            customer_id=customer_id,
                            data=data,
                        )
                        self._link_persona(db, event_id=event_id, persona_id=new_persona.persona_id)
                        persona_saved = True
                        logger.info("Persona '%s' created for event %s", name, event_id)
                    except Exception as exc:
                        logger.warning("Persona save failed: %s", exc)

        # 11 ── Persist suggested tasks ───────────────────────────────────────
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
                            "name":            task_name,
                            "description":     t.get("description"),
                            "quantity":        int(t.get("quantity") or 1),
                            "currency":        t.get("currency", "LKR"),
                            "vendor_category": t.get("vendor_category"),
                            "needs_vendor":    True,
                        },
                    )
                    new_task_ids.append(task_obj.task_id)
                    existing_names.add(task_name.lower())
                except Exception as exc:
                    logger.warning("Task persist failed '%s': %s", task_name, exc)

        # 12 ── Shortlist exactly ONE offering per new task ───────────────────
        for task_id in new_task_ids:
            try:
                task_obj = db.query(Task).filter(Task.task_id == task_id).first()
                if not task_obj:
                    continue
                ranked = offering_service.find_offerings_for_task(
                    db=db, task=task_obj, limit=1,
                )
                if ranked:
                    offering_service.save_task_offering_shortlist(
                        db=db, task_id=task_id, offerings_with_rank=ranked,
                    )
                    logger.info(
                        "Offering '%s' shortlisted for task '%s'",
                        ranked[0]["offering"].offering_id, task_id,
                    )
            except Exception as exc:
                logger.warning("Shortlist failed for task %s: %s", task_id, exc)

        return ChatSendResponse(
            reply=reply,
            suggestedTasks=suggested_out,
            intent=ai_output.get("intent"),
            missingInfo=ai_output.get("missingInfo") or [],
            askSavePersona=bool(ai_output.get("save_persona") and not persona_saved),
            personaSaved=persona_saved,
            personaConfirmed=persona_confirmed,
        )

    # ── Phase determination ────────────────────────────────────────────────────

    def _determine_phase(
        self,
        event_context: dict,
        personas: list[Persona],
        event: Event,
    ) -> tuple[str, bool, list[str]]:
        """
        Returns (phase, needs_persona, persona_missing_fields).

        Logic:
          GROUP events skip persona collection entirely.
          For all others: persona must be collected before anything else.
        """
        event_type_upper = (event.event_type or "").upper()
        ctx = event_context or {}

        # GROUP events don't need a persona
        if event_type_upper == "GROUP":
            needs_persona = False
        else:
            needs_persona = not personas

        if needs_persona:
            return PHASE_PERSONA_COLLECTION, True, []

        # Non-group: check persona completeness
        if event_type_upper != "GROUP" and personas:
            missing = self._persona_missing_fields(personas[0])
            if missing:
                return PHASE_PERSONA_COLLECTION, False, missing

        # Persona is complete — check event purpose
        if not ctx.get("event_purpose"):
            inferred = self._infer_purpose_from_title(event.title or "")
            if not inferred:
                return PHASE_EVENT_PURPOSE, False, []
            # Auto-populate inferred purpose into context for this turn
            ctx["event_purpose"] = inferred

        # Check logistics
        if not ctx.get("event_date") or not ctx.get("budget_total") or not ctx.get("guest_count"):
            return PHASE_EVENT_LOGISTICS, False, []

        # Check tasks
        if not ctx.get("existing_tasks"):
            return PHASE_TASK_GENERATION, False, []

        return PHASE_COMPLETE, False, []

    @staticmethod
    def _persona_missing_fields(persona: Persona) -> list[str]:
        """
        Return a list of field_keys that are missing from the persona.
        Keys match the field_key values in PERSONA_QUESTIONS.
        Note: the 'age' key maps to the 'birthday' model attribute.
        """
        missing: list[str] = []
        for attr, key in _PERSONA_REQUIRED_FIELDS:
            val = getattr(persona, attr, None)
            if isinstance(val, list):
                if not val:
                    missing.append(key)
            elif not val:
                missing.append(key)
        return missing

    @staticmethod
    def _infer_purpose_from_title(title: str) -> str | None:
        title_lower = title.lower()
        keyword_map = {
            "birthday":   "Birthday",
            "anniversary":"Anniversary",
            "wedding":    "Wedding",
            "graduation": "Graduation",
            "farewell":   "Farewell",
            "baby shower":"Baby Shower",
            "engagement": "Engagement",
            "proposal":   "Proposal",
            "date night": "Date Night",
            "valentine":  "Valentine's Day",
            "christmas":  "Christmas",
            "new year":   "New Year",
            "promotion":  "Promotion Celebration",
            "surprise":   "Surprise Party",
        }
        for keyword, purpose in keyword_map.items():
            if keyword in title_lower:
                return purpose
        return None

    # ── Event context builder ─────────────────────────────────────────────────

    def _build_event_context(
        self,
        event: Event,
        existing_tasks: list[Task],
    ) -> dict:
        ctx: dict = {
            "title":           event.title,
            "event_type":      event.event_type,
            "event_purpose":   None,
            "event_date":      None,
            "location":        event.location_text or None,
            "guest_count":     None,
            "budget_total":    None,
            "budget_per_head": None,
            "expectations":    None,
            "existing_tasks":  [t.name for t in existing_tasks],
        }

        if event.start_at:
            try:
                ctx["event_date"] = event.start_at.date().isoformat()
            except Exception:
                pass

        # Load soft facts from description blob
        soft = self._parse_facts(event.description or "")
        for key in ("guest_count", "budget_total", "budget_per_head", "expectations", "event_purpose"):
            if soft.get(key):
                ctx[key] = soft[key]

        # Infer purpose from title if not set
        if not ctx["event_purpose"]:
            inferred = self._infer_purpose_from_title(event.title or "")
            if inferred:
                ctx["event_purpose"] = inferred

        # Derive budget_per_head
        if ctx["budget_total"] and ctx["guest_count"] and not ctx["budget_per_head"]:
            try:
                ctx["budget_per_head"] = round(
                    float(ctx["budget_total"]) / float(ctx["guest_count"]), 2
                )
            except (TypeError, ZeroDivisionError):
                pass

        return ctx

    # ── Fact persistence ──────────────────────────────────────────────────────

    def _persist_extracted_facts(
        self,
        db: Session,
        event: Event,
        ai_output: dict,
    ) -> None:
        ef      = ai_output.get("eventFacts") or {}
        changed = False

        if ef.get("date") and not event.start_at:
            tz_str = ef.get("timezone") or _DEFAULT_TZ
            aware  = self._parse_date(ef["date"], tz_str)
            if aware:
                event.start_at = aware
                event.timezone = tz_str
                changed = True

        if ef.get("timezone") and not event.timezone:
            event.timezone = ef["timezone"]
            changed = True

        if ef.get("location") and not event.location_text:
            event.location_text = ef["location"]
            changed = True

        current      = self._parse_facts(event.description or "")
        soft_changed = False

        updates = {
            "event_purpose": ef.get("purpose"),
            "guest_count":   str(ef["guestCount"])   if ef.get("guestCount")   else None,
            "budget_total":  str(ef["budgetTotal"])   if ef.get("budgetTotal")  else None,
            "budget_per_head": str(ef["budgetPerHead"]) if ef.get("budgetPerHead") else None,
            "expectations":  str(ef["expectations"])[:300] if ef.get("expectations") else None,
        }

        for key, value in updates.items():
            if value and not current.get(key):
                current[key] = value
                soft_changed = True

        if soft_changed:
            event.description = self._write_facts(current, event.description or "")
            changed = True

        if changed:
            db.add(event)
            db.commit()
            logger.info(
                "Event %s updated | purpose=%s date=%s guests=%s budget=%s",
                event.event_id,
                ef.get("purpose"),
                ef.get("date"),
                ef.get("guestCount"),
                ef.get("budgetTotal"),
            )

    # ── Persona update helper ─────────────────────────────────────────────────

    @staticmethod
    def _build_persona_update(draft: dict, existing: Persona) -> dict:
        update: dict = {}

        # Scalar fields: only set if missing on existing persona.
        # All keys are attempted; _filter_to_model_columns will drop any
        # that don't exist on the actual Persona model.
        for draft_key, model_key in [
            ("relationship", "relationship"),
            ("gender",       "gender"),
            ("birthday",     "birthday"),
            ("location",     "location"),
        ]:
            if draft.get(draft_key) and not getattr(existing, model_key, None):
                update[model_key] = draft[draft_key]

        # If age is provided but birthday is not yet set, store as birthday note
        if draft.get("age") and not getattr(existing, "birthday", None):
            update["birthday"] = f"age:{draft['age']}"

        # List fields: merge new items (only if attribute exists on model)
        for key in ("personality_tags", "food_preferences", "music_preferences",
                    "color_preferences", "interests"):
            existing_list = getattr(existing, key, None) or []
            new_items     = draft.get(key) or []
            merged        = list(dict.fromkeys(existing_list + new_items))  # preserve order, dedup
            if len(merged) > len(existing_list):
                update[key] = merged

        # Filter to model columns before returning so update_persona never
        # receives columns that don't exist in the DB schema.
        try:
            from sqlalchemy import inspect as sa_inspect
            valid = {c.key for c in sa_inspect(type(existing)).mapper.column_attrs}
            return {k: v for k, v in update.items() if k in valid}
        except Exception:
            return update

    # ── Fact codec (stored in event.description) ──────────────────────────────

    _PREFIX_START = "[FACTS:"
    _PREFIX_END   = "]\n"

    def _parse_facts(self, description: str) -> dict[str, str]:
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
        if existing.startswith(self._PREFIX_START):
            end = existing.find(self._PREFIX_END)
            if end != -1:
                existing = existing[end + len(self._PREFIX_END):]
        pairs  = ",".join(f"{k}={v}" for k, v in facts.items() if v)
        prefix = f"{self._PREFIX_START}{pairs}{self._PREFIX_END}"
        return prefix + existing

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_date(date_str: str, tz_str: str) -> datetime | None:
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

    @staticmethod
    def _save_message(db: Session, *, event_id: str, sender: str, content: str) -> None:
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

    @staticmethod
    def _filter_to_model_columns(model_cls, data: dict) -> dict:
        """
        Return a copy of `data` containing only keys that correspond to actual
        columns on the SQLAlchemy model.  This prevents TypeError when the AI
        draft contains fields (gender, location, interests …) that haven't been
        added to the database model yet.
        """
        try:
            from sqlalchemy import inspect as sa_inspect
            valid = {c.key for c in sa_inspect(model_cls).mapper.column_attrs}
            return {k: v for k, v in data.items() if k in valid}
        except Exception:
            # Fallback: return data as-is if introspection fails
            return data


event_chat_service = EventChatService()