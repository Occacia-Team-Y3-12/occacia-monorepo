"""
app/services/planning_service.py

Persona flow — two complementary paths:

PATH A  (interactive, Redis-backed):
  Step 0 — first message + saved personas exist → show persona list
  Step 1 — user replies → match/confirm or skip
  Step 2 — normal AI loop (profile applied silently)
  Step 4 — save-prompt was shown after packages → wait for yes/no

PATH B  (single-turn, no extra Redis step required):
  AI returns save_persona + ask_save_persona in the SAME response.
  If the user's current message already contains a yes-word, save immediately.
  This handles test cases and real users who say yes in the same message.

Both paths are active simultaneously. Path A adds the multi-turn UX layer
on top; Path B ensures correctness even in single-turn scenarios.
"""
import json
import logging
import re
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.schemas.planning_schema import PlanResponse

logger = logging.getLogger(__name__)

_BUDGET_RE = re.compile(
    r'(?:budget|spend|spending|cost|costs|afford|price)[^\d]{0,10}(\d[\d,]*)',
    re.IGNORECASE,
)
_GUEST_RE  = re.compile(r'(\d+)\s*(?:people|guests?|persons?|pax)', re.IGNORECASE)
_DATE_RE   = re.compile(r'(\d{4}-\d{2}-\d{2})')

_YES_WORDS = {"yes", "sure", "ok", "okay", "save", "please", "yep", "yeah",
              "do it", "go ahead"}
_NO_WORDS  = {"no", "nope", "skip", "don't", "dont", "not now",
              "never mind", "cancel"}

# Redis key templates
_STEP_KEY    = "pflow:step:{sid}"
_CHOSEN_KEY  = "pflow:chosen:{sid}"
_PENDING_KEY = "pflow:pending:{sid}"


# ── Redis helpers ──────────────────────────────────────────────────────────────

def _get_redis():
    try:
        import redis as _redis
        import os
        r = _redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            decode_responses=True,
            socket_connect_timeout=2,
        )
        r.ping()
        return r
    except Exception:
        return None


def _rget(r, key, default=None):
    if r is None:
        return default
    try:
        v = r.get(key)
        return v if v is not None else default
    except Exception:
        return default


def _rset(r, key, value, ttl=3600):
    if r is None:
        return
    try:
        r.setex(key, ttl, str(value))
    except Exception:
        pass


def _rdel(r, *keys):
    if r is None:
        return
    try:
        r.delete(*keys)
    except Exception:
        pass


# ── Text helpers ───────────────────────────────────────────────────────────────

def _user_said_yes(text: str) -> bool:
    lower = text.lower().strip()
    return any(w in lower for w in _YES_WORDS)


def _user_said_no(text: str) -> bool:
    lower = text.lower().strip()
    return any(w in lower for w in _NO_WORDS)


def _extract_budget(text: str) -> Optional[float]:
    m = _BUDGET_RE.search(text)
    if m:
        try:
            return float(m.group(1).replace(",", ""))
        except ValueError:
            pass
    return None


def _extract_guests(text: str) -> Optional[int]:
    m = _GUEST_RE.search(text)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            pass
    return None


def _extract_date(text: str) -> Optional[str]:
    m = _DATE_RE.search(text)
    if m:
        try:
            date.fromisoformat(m.group(1))
            return m.group(1)
        except ValueError:
            pass
    return None


def _safe_list(val) -> list:
    if not val:
        return []
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        try:
            return json.loads(val)
        except Exception:
            return [val]
    return list(val)


def _package_to_dict(pkg, requested_tags: list = None) -> dict:
    state = getattr(pkg, "__dict__", None) or {}
    vendor_name = None
    try:
        if "vendor" in state:
            v = state["vendor"]
            if v is not None:
                vendor_name = (
                    getattr(v, "display_name", None)
                    or getattr(v, "business_name", None)
                )
        elif hasattr(pkg, "vendor") and not hasattr(type(pkg), "__tablename__"):
            v = pkg.vendor
            if v is not None:
                vendor_name = (
                    getattr(v, "display_name", None)
                    or getattr(v, "business_name", None)
                )
    except Exception:
        vendor_name = None

    pkg_tags = pkg.tags or []
    if isinstance(pkg_tags, str):
        try:
            pkg_tags = json.loads(pkg_tags)
        except Exception:
            pkg_tags = []

    if requested_tags:
        matched           = len(set(requested_tags) & set(pkg_tags))
        total             = len(set(requested_tags))
        match_score       = matched
        match_score_max   = total
        match_score_label = f"{matched} of {total} tags matched"
    else:
        match_score = match_score_max = match_score_label = None

    return {
        "id":                pkg.id,
        "name":              pkg.name,
        "description":       pkg.description,
        "price_per_head":    getattr(pkg, "price_per_head", None),
        "tags":              pkg_tags,
        "location":          getattr(pkg, "location_coverage", None),
        "vendor_name":       vendor_name,
        "match_score":       match_score,
        "match_score_max":   match_score_max,
        "match_score_label": match_score_label,
    }


# ── Persona flow helpers ───────────────────────────────────────────────────────

def _build_persona_choice_message(personas: list) -> str:
    lines = [
        "I'm ready to help you plan something special! "
        "I have these saved profiles:"
    ]
    for i, p in enumerate(personas, 1):
        rel = f" ({p.relationship})" if getattr(p, "relationship", None) else ""
        lines.append(f"  {i}. {p.name}{rel}")
    lines.append(
        "\nWould you like to plan for one of them? "
        "Say their name or number, or tell me who you're planning for "
        "and I'll start fresh."
    )
    return "\n".join(lines)


def _match_persona_from_reply(user_query: str, personas: list):
    """Return matching Persona by name or 1-based number, or None."""
    lower = user_query.lower().strip()
    m = re.search(r'\b(\d+)\b', lower)
    if m:
        idx = int(m.group(1)) - 1
        if 0 <= idx < len(personas):
            return personas[idx]
    for p in personas:
        if p.name and p.name.lower() in lower:
            return p
    return None


def _try_save_persona(db, persona_svc, customer_id, save_data, existing_personas):
    """
    Create and auto-confirm a persona from save_data dict.
    Returns (saved: bool, updated_personas: list).
    Skips silently if name is blank or already exists.
    """
    if not isinstance(save_data, dict):
        return False, existing_personas

    name = (save_data.get("name") or "").strip()
    if not name:
        return False, existing_personas

    if any(p.name.lower() == name.lower() for p in existing_personas):
        return False, existing_personas

    try:
        pdata = {
            "name":              name,
            "relationship":      save_data.get("relationship"),
            "personality":       save_data.get("personality") or "",
            "food_preferences":  save_data.get("food_preferences") or [],
            "music_preferences": save_data.get("music_preferences") or [],
            "personality_tags":  save_data.get("personality_tags") or [],
            "color_preferences": save_data.get("color_preferences") or [],
        }
        age = save_data.get("age")
        if age:
            pdata["personality"] = (pdata["personality"] + f" Age: {age}").strip()

        new_p = persona_svc.create_persona(db, customer_id=customer_id, data=pdata)
        persona_svc.confirm_persona(db, new_p.persona_id, customer_id)
        updated = persona_svc.get_personas(db, customer_id)
        logger.info(f"Persona '{name}' saved for customer {customer_id}")
        return True, updated
    except Exception as e:
        logger.warning(f"Persona save failed: {e}")
        return False, existing_personas


# ══════════════════════════════════════════════════════════════════════════════
# Service
# ══════════════════════════════════════════════════════════════════════════════

class PlanningService:

    async def process_plan(
        self,
        db: Session,
        customer: Customer,
        session_id: str,
        user_query: str,
        persona_svc,
        ai_svc,
        chat_svc,
        vendor_svc,
        event_context: dict = None,
    ) -> PlanResponse:

        r           = _get_redis()
        customer_id = str(customer.customer_id)

        step_key    = _STEP_KEY.replace("{sid}",   session_id)
        chosen_key  = _CHOSEN_KEY.replace("{sid}", session_id)
        pending_key = _PENDING_KEY.replace("{sid}", session_id)

        current_step = int(_rget(r, step_key, "0"))

        # Fetch all customer personas (scoped to this customer by persona_svc)
        personas = persona_svc.get_personas(db, customer_id)

        # Resolve chosen persona from Redis
        chosen_persona = None
        chosen_id = _rget(r, chosen_key, "")
        if chosen_id:
            chosen_persona = next(
                (p for p in personas if p.persona_id == chosen_id), None
            )

        history      = chat_svc.get_session_history(db, session_id)
        prev_missing = chat_svc.get_last_missing_info(db, session_id)
        # Guard: prev_missing may arrive as dict from older storage format
        if isinstance(prev_missing, dict):
            prev_missing = prev_missing.get("items", [])

        # ══════════════════════════════════════════════════════════════════════
        # STEP 0 — very first message + saved personas → show list
        # Only runs when Redis is reachable (r is not None).
        # When Redis is unavailable (tests, no Redis env) we skip the
        # interactive flow entirely and go straight to the AI loop.
        # ══════════════════════════════════════════════════════════════════════
        if r is not None and current_step == 0 and not history and personas:
            msg = _build_persona_choice_message(personas)
            chat_svc.save_message(
                db, session_id=session_id, user_msg=user_query, ai_msg=msg,
                customer_id=customer.customer_id, missing_info=[],
            )
            _rset(r, step_key, "1")
            return PlanResponse(
                intent="chat", reasoning="Persona selection prompt shown.",
                personality_profile=None, chat_response=msg,
                gift_suggestion=None, missing_info=[],
                venue_match_tier=None, event_type=None, event_date=None,
                location=None, budget_per_head=None, guest_count=None,
                venue_tags=[], matched_venues=[],
                ask_save_persona=False, persona_saved=False, persona_confirmed=False,
            )

        # ══════════════════════════════════════════════════════════════════════
        # STEP 1 — user replied to persona-selection prompt
        # ══════════════════════════════════════════════════════════════════════
        if r is not None and current_step == 1 and personas:
            matched = _match_persona_from_reply(user_query, personas)
            if matched:
                try:
                    persona_svc.confirm_persona(db, matched.persona_id, customer_id)
                except Exception:
                    pass
                _rset(r, chosen_key, matched.persona_id)
                _rset(r, step_key, "2")
                chosen_persona = matched
                msg = (
                    f"Great! I'll plan this around {matched.name}'s preferences. "
                    f"Now tell me — what's the occasion, when is it, "
                    f"and what's your rough budget?"
                )
                chat_svc.save_message(
                    db, session_id=session_id, user_msg=user_query, ai_msg=msg,
                    customer_id=customer.customer_id,
                    missing_info=["occasion", "date", "budget"],
                )
                return PlanResponse(
                    intent="chat",
                    reasoning=f"Persona '{matched.name}' selected.",
                    personality_profile=None, chat_response=msg,
                    gift_suggestion=None,
                    missing_info=["occasion", "date", "budget"],
                    venue_match_tier=None, event_type=None, event_date=None,
                    location=None, budget_per_head=None, guest_count=None,
                    venue_tags=[], matched_venues=[],
                    ask_save_persona=False, persona_saved=False,
                    persona_confirmed=True,
                )
            else:
                _rset(r, step_key, "2")

        # ══════════════════════════════════════════════════════════════════════
        # STEP 4 — user replied to "save this person?" prompt
        # ══════════════════════════════════════════════════════════════════════
        if r is not None and current_step == 4:
            pending_json = _rget(r, pending_key, "")
            save_data    = json.loads(pending_json) if pending_json else {}

            persona_saved = False
            if _user_said_yes(user_query) and save_data:
                persona_saved, personas = _try_save_persona(
                    db, persona_svc, customer_id, save_data, personas
                )
                reply = (
                    f"Done! I've saved {save_data.get('name', 'their')} profile "
                    f"so you can use it next time."
                    if persona_saved else
                    "No problem — I'll skip saving for now."
                )
            else:
                reply = "No problem — I won't save anything."

            _rdel(r, pending_key, step_key)
            chat_svc.save_message(
                db, session_id=session_id, user_msg=user_query, ai_msg=reply,
                customer_id=customer.customer_id, missing_info=[],
            )
            return PlanResponse(
                intent="chat", reasoning="Persona save step completed.",
                personality_profile=None, chat_response=reply,
                gift_suggestion=None, missing_info=[],
                venue_match_tier=None, event_type=None, event_date=None,
                location=None, budget_per_head=None, guest_count=None,
                venue_tags=[], matched_venues=[],
                ask_save_persona=False, persona_saved=persona_saved,
                persona_confirmed=False,
            )

        # ══════════════════════════════════════════════════════════════════════
        # STEP 2 / default — normal AI planning loop
        # ══════════════════════════════════════════════════════════════════════
        _rset(r, step_key, "2")

        all_text = (
            user_query + " "
            + " ".join((m.user_message or "") for m in history[-5:])
        )
        extracted_budget   = _extract_budget(all_text)
        extracted_guests   = _extract_guests(all_text)
        extracted_location = vendor_svc.extract_location_from_text(all_text)
        extracted_date     = _extract_date(all_text)
        active_missing     = list(prev_missing or [])
        available_tags     = vendor_svc.get_all_tags(db)
        availability_block = (
            vendor_svc.get_availability_block(db, tags=available_tags[:20])
            if available_tags else ""
        )

        # Personas for AI: chosen persona if set, else all
        personas_for_ai = [chosen_persona] if chosen_persona else personas

        try:
            fact_parts = []
            if extracted_budget:   fact_parts.append(f"budget={extracted_budget}")
            if extracted_guests:   fact_parts.append(f"guests={extracted_guests}")
            if extracted_location: fact_parts.append(f"location={extracted_location}")
            if extracted_date:     fact_parts.append(f"date={extracted_date}")

            enriched_query = user_query
            if fact_parts:
                enriched_query += f"\n[SYSTEM EXTRACTED FACTS: {', '.join(fact_parts)}]"
            if event_context:
                ctx_parts = []
                if event_context.get("title"):
                    ctx_parts.append(f"Event title: {event_context['title']}")
                if event_context.get("event_type"):
                    ctx_parts.append(f"Event type: {event_context['event_type']}")
                if event_context.get("start_at"):
                    ctx_parts.append(f"Scheduled date: {event_context['start_at']}")
                if event_context.get("location_text"):
                    ctx_parts.append(f"Location: {event_context['location_text']}")
                if event_context.get("existing_tasks"):
                    ctx_parts.append(f"Tasks already added: {', '.join(event_context['existing_tasks'])}")
                if ctx_parts:
                    enriched_query += f"\n[EVENT CONTEXT: {'; '.join(ctx_parts)}]"
            if availability_block:
                enriched_query += availability_block

            ai_result = await ai_svc.generate_date_plan(
                raw_query      = enriched_query,
                history        = history,
                personas       = personas_for_ai if personas_for_ai else None,
                available_tags = available_tags if available_tags else None,
                missing_info   = active_missing if active_missing else None,
            )
        except Exception as exc:
            logger.error(f"AI call failed: {exc}")
            ai_result = {
                "intent":        "chat",
                "chat_response": (
                    "Things are a bit foggy on our end right now. "
                    "Could you try again in a moment?"
                ),
                "venue_tags":   [],
                "missing_info": [],
            }

        intent            = ai_result.get("intent", "chat")
        venue_tags        = ai_result.get("venue_tags") or []
        new_missing       = ai_result.get("missing_info") or []
        chat_response     = ai_result.get("chat_response", "")
        gift_suggestion   = ai_result.get("gift_suggestion")
        event_type        = ai_result.get("event_type")
        budget_for_filter = ai_result.get("budget_per_head") or extracted_budget
        location_filter   = ai_result.get("location") or extracted_location

        # ── use_persona_name: AI suggests an existing saved persona ───────────
        # Restored to fix test_persona_confirmed_flag_when_ai_suggests and
        # test_suggested_persona_confirmed_in_db.
        use_persona_name  = (ai_result.get("use_persona_name") or "").strip()
        persona_confirmed = False

        if use_persona_name and personas:
            matched_p = next(
                (p for p in personas if p.name.lower() == use_persona_name.lower()),
                None,
            )
            if matched_p:
                try:
                    persona_svc.confirm_persona(db, matched_p.persona_id, customer_id)
                except Exception:
                    pass
                if not chosen_persona:
                    _rset(r, chosen_key, matched_p.persona_id)
                    chosen_persona = matched_p
                persona_confirmed = True

        # Also confirmed if we already had a chosen persona from Redis
        if chosen_persona:
            persona_confirmed = True

        # ── PATH B: single-turn persona save ──────────────────────────────────
        # If the AI returned save_persona AND this message contains a yes-word,
        # save immediately without a second turn.
        # If ask_save_persona is True but no yes-word, queue for step 4.
        save_persona_data = ai_result.get("save_persona")
        ask_save_persona  = bool(ai_result.get("ask_save_persona", False))
        persona_saved     = False

        if save_persona_data and isinstance(save_persona_data, dict):
            if _user_said_yes(user_query):
                # Single-turn save (covers all test_persona_saved_when_user_says_* tests)
                persona_saved, personas = _try_save_persona(
                    db, persona_svc, customer_id, save_persona_data, personas
                )
            elif ask_save_persona:
                # Queue for next turn (PATH A multi-turn UX)
                name = (save_persona_data.get("name") or "").strip()
                already = (
                    any(p.name.lower() == name.lower() for p in personas)
                    if name else True
                )
                if name and not already:
                    _rset(r, pending_key, json.dumps(save_persona_data))
                    save_prompt = (
                        f"\n\nBy the way — would you like me to save {name}'s details "
                        f"as a profile? That way you won't have to describe them again."
                    )
                    chat_response = (chat_response or "") + save_prompt
                    _rset(r, step_key, "4")

        # ── Intent override ───────────────────────────────────────────────────
        _ql = (user_query or "").lower()
        if (any(s in _ql for s in ["gift", "present", "buy", "surprise",
                                    "get her", "get him"])
                and any(s in _ql for s in ["venue", "dinner", "restaurant",
                                            "party", "book", "plan", "event"])):
            intent = "multi"

        # ── Venue / gift matching ─────────────────────────────────────────────
        matched_venues   = []
        venue_match_tier = None

        # For gift enrichment, use chosen persona first, then fall back to all
        enrich_personas = personas_for_ai if personas_for_ai else personas

        if intent == "multi" and venue_tags:
            pkgs = vendor_svc.find_perfect_matches(
                db, criteria={
                    "venue_tags":      venue_tags,
                    "budget_per_head": budget_for_filter,
                    "location":        location_filter,
                    "guest_count":     extracted_guests,
                },
            )
            matched_venues = [_package_to_dict(p, requested_tags=venue_tags) for p in pkgs]
            gift_tags  = list(venue_tags)
            resp_lower = (chat_response or "").lower()
            for p in enrich_personas:
                if p.name and p.name.lower() in resp_lower:
                    gift_tags = list(set(
                        gift_tags
                        + _safe_list(p.preferences_json)
                        + _safe_list(p.food_preferences)
                        + _safe_list(p.personality_tags)
                    ))
            gift_pkgs = vendor_svc.find_gift_matches(
                db, gift_tags=gift_tags, budget=budget_for_filter
            )
            if gift_pkgs and not gift_suggestion:
                gift_suggestion = (
                    f"{gift_pkgs[0].name} - "
                    f"{getattr(gift_pkgs[0], 'description', '') or ''}"
                ).strip(" -")

        elif intent == "gift" and venue_tags:
            gift_tags  = list(venue_tags)
            resp_lower = (chat_response or "").lower()
            for p in enrich_personas:
                if p.name and p.name.lower() in resp_lower:
                    gift_tags = list(set(
                        gift_tags
                        + _safe_list(p.preferences_json)
                        + _safe_list(p.food_preferences)
                        + _safe_list(p.personality_tags)
                    ))
            pkgs = vendor_svc.find_gift_matches(
                db, gift_tags=gift_tags, budget=budget_for_filter
            )
            matched_venues = [_package_to_dict(p, requested_tags=venue_tags) for p in pkgs]

        elif intent in ("planning", "date") and venue_tags:
            pkgs = vendor_svc.find_perfect_matches(
                db, criteria={
                    "venue_tags":      venue_tags,
                    "budget_per_head": budget_for_filter,
                    "location":        location_filter,
                    "guest_count":     extracted_guests,
                },
            )
            matched_venues = [_package_to_dict(p, requested_tags=venue_tags) for p in pkgs]
            if pkgs:
                canonical_loc = vendor_svc.extract_location_from_text(
                    location_filter or ""
                )
                first    = pkgs[0]
                pkg_tags = first.tags or []
                if isinstance(pkg_tags, str):
                    try:
                        pkg_tags = json.loads(pkg_tags)
                    except Exception:
                        pkg_tags = []
                all_match = set(venue_tags).issubset(set(pkg_tags))
                loc_match = canonical_loc and canonical_loc in (
                    getattr(first, "location_coverage", "") or ""
                ).lower()
                if all_match and loc_match:
                    venue_match_tier = 1
                elif all_match:
                    venue_match_tier = 2
                else:
                    venue_match_tier = 3

        # ── After packages shown → append save prompt if not yet queued ───────
        if (matched_venues and ask_save_persona
                and save_persona_data and not persona_saved
                and current_step != 4):
            name = (
                save_persona_data.get("name") or ""
            ).strip() if isinstance(save_persona_data, dict) else ""
            already = (
                any(p.name.lower() == name.lower() for p in personas)
                if name else True
            )
            if name and not already:
                save_prompt = (
                    f"\n\nAlso — would you like me to save {name}'s details as a profile? "
                    f"I can remember their preferences for next time."
                )
                chat_response = (chat_response or "") + save_prompt
                _rset(r, pending_key, json.dumps(save_persona_data))
                _rset(r, step_key, "4")

        # ── Persist turn ──────────────────────────────────────────────────────
        chat_svc.save_message(
            db,
            session_id=session_id,
            user_msg=user_query,
            ai_msg=chat_response or "",
            customer_id=customer.customer_id,
            missing_info=new_missing,
        )

        return PlanResponse(
            intent              = intent,
            reasoning           = ai_result.get("reasoning"),
            personality_profile = ai_result.get("personality_profile"),
            chat_response       = chat_response,
            gift_suggestion     = gift_suggestion,
            missing_info        = new_missing,
            venue_match_tier    = venue_match_tier,
            event_type          = event_type,
            event_date          = extracted_date,
            location            = ai_result.get("location") or extracted_location,
            budget_per_head     = ai_result.get("budget_per_head") or extracted_budget,
            guest_count         = ai_result.get("guest_count") or extracted_guests,
            venue_tags          = venue_tags,
            matched_venues      = matched_venues,
            ask_save_persona    = ask_save_persona,
            persona_saved       = persona_saved,
            persona_confirmed   = persona_confirmed,
        )


planning_service = PlanningService()