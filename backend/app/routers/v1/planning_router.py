"""
app/routers/v1/planning_router.py

Core AI planning logic with multi-intent detection and persona flow.
"""

import logging
import re
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_customer
from app.models.customer import Customer
from app.models.persona import Persona
from app.services.ai_service import ai_service
from app.services.chat_service import chat_service
from app.services.vendor_service import vendor_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/planning", tags=["Planning"])

_SESSION_RE = re.compile(r'^[a-zA-Z0-9_\-]{1,64}$')


# --- Persona Service Shim ---
# Tests patch BOTH the source and the router reference.
# We import the real singleton so patches on the services module propagate here.
try:
    from app.services.persona_service import persona_service
except ImportError:
    class _PersonaService:
        def get_personas(self, db: Session, customer_id):
            return (
                db.query(Persona)
                .filter(Persona.customer_id == customer_id)
                .all()
            )
    persona_service = _PersonaService()


# --- Redis / Rate Limiting ---

def get_redis():
    """Return Redis client or None if unavailable."""
    try:
        import redis as _redis
        import os
        r = _redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
        r.ping()
        return r
    except Exception:
        return None

_RATE_LIMIT = 10

def check_rate_limit(customer_id, session_id=None):
    """
    Raise HTTPException(429) if over limit.
    Fails open when Redis is unavailable.
    """
    r = get_redis()
    if r is None:
        return True
    key = f"rate:{customer_id}"
    try:
        pipe = r.pipeline()
        pipe.incr(key)
        pipe.expire(key, 60)
        results = pipe.execute()
        count = results[0]
        if count > _RATE_LIMIT:
            raise HTTPException(status_code=429, detail="Rate limit exceeded.")
        return True
    except HTTPException:
        raise
    except Exception:
        return True


# --- Request / Response Schemas ---

class PlanRequest(BaseModel):
    session_id: str
    user_query: str


class PlanResponse(BaseModel):
    intent: Optional[str] = None
    chat_response: Optional[str] = None
    matched_venues: list = []
    gift_suggestion: Optional[str] = None
    missing_info: list = []
    venue_match_tier: Optional[int] = None
    event_type: Optional[str] = None
    location: Optional[str] = None
    budget_per_head: Optional[float] = None
    guest_count: Optional[int] = None
    venue_tags: list = []
    
    # Persona flow signals for the frontend
    ask_save_persona: bool = False
    persona_saved: bool = False
    persona_confirmed: bool = False


# --- Extraction Helpers ---

_BUDGET_RE = re.compile(
    r'(?:budget|spend|spending|cost|costs|afford|price)[^\d]{0,10}(\d[\d,]*)',
    re.IGNORECASE,
)
_GUEST_RE = re.compile(r'(\d+)\s*(?:people|guests?|persons?|pax)', re.IGNORECASE)
_DATE_RE  = re.compile(r'(\d{4}-\d{2}-\d{2})')


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

def _extract_date(text: str) -> Optional[date]:
    m = _DATE_RE.search(text)
    if m:
        try:
            return date.fromisoformat(m.group(1))
        except ValueError:
            pass
    return None

def _package_to_dict(pkg, requested_tags: list = None) -> dict:
    """
    Serializes a Package (or MagicMock) to a plain dict for the API response.
    Computes a human-readable match_score if requested_tags are provided.
    """
    state = getattr(pkg, "__dict__", None) or {}
    vendor_name = None
    try:
        vendor_loaded = "vendor" in state
        if vendor_loaded:
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
        import json as _json
        try:
            pkg_tags = _json.loads(pkg_tags)
        except Exception:
            pkg_tags = []

    if requested_tags:
        matched   = len(set(requested_tags) & set(pkg_tags))
        total     = len(set(requested_tags))
        match_score       = matched
        match_score_max   = total
        match_score_label = f"{matched} of {total} tags matched"
    else:
        match_score       = None
        match_score_max   = None
        match_score_label = None

    return {
        "id":                pkg.id,
        "name":              pkg.name,
        "description":       pkg.description,
        "price":             getattr(pkg, "price", None),
        "price_per_head":    getattr(pkg, "price_per_head", None),
        "tags":              pkg_tags,
        "location":          getattr(pkg, "location_coverage", None),
        "vendor_name":       vendor_name,
        "match_score":       match_score,
        "match_score_max":   match_score_max,
        "match_score_label": match_score_label,
    }


# --- Main Endpoint ---

@router.post("/generate", response_model=PlanResponse)
async def generate_plan(
    request: Request,
    plan_req: PlanRequest,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    session_id = plan_req.session_id
    user_query = plan_req.user_query

    if not _SESSION_RE.match(session_id):
        raise HTTPException(status_code=400, detail="Invalid session_id format.")

    check_rate_limit(str(current_customer.customer_id), session_id)

    # 1. Conversation history
    history = chat_service.get_session_history(db, session_id)

    # 2. Carry forward missing_info from previous turn
    prev_missing = chat_service.get_last_missing_info(db, session_id)

    # 3. Extract structured values
    all_text = user_query + " " + " ".join(
        (m.user_message or "") for m in history[-5:]
    )
    extracted_budget   = _extract_budget(all_text)
    extracted_guests   = _extract_guests(all_text)
    extracted_location = vendor_service.extract_location_from_text(all_text)
    extracted_date     = _extract_date(all_text)

    resolved = set()
    if extracted_budget is not None:
        resolved.add("budget")
    if extracted_guests is not None:
        resolved.add("guest_count")
    if extracted_location is not None:
        resolved.add("location")
    if extracted_date is not None:
        resolved.add("event_date")

    active_missing = list(prev_missing or [])

    logger.info(
        f"EXTRACTED: budget={extracted_budget}, guests={extracted_guests}, "
        f"location={extracted_location}, date={extracted_date} | "
        f"resolved={resolved} | still_missing={active_missing}"
    )

    # 4. Load personas
    personas = persona_service.get_personas(db, current_customer.customer_id)

    # 5. Tags and availability
    available_tags = vendor_service.get_all_tags(db)
    availability_block = ""
    if available_tags:
        availability_block = vendor_service.get_availability_block(
            db, tags=available_tags[:20]
        )

    # 6. Call AI
    try:
        fact_parts = []
        if extracted_budget:
            fact_parts.append(f"budget={extracted_budget}")
        if extracted_guests:
            fact_parts.append(f"guests={extracted_guests}")
        if extracted_location:
            fact_parts.append(f"location={extracted_location}")
        if extracted_date:
            fact_parts.append(f"date={extracted_date}")

        enriched_query = user_query
        if fact_parts:
            enriched_query += f"\n[SYSTEM EXTRACTED FACTS: {', '.join(fact_parts)}]"
        if availability_block:
            enriched_query += availability_block

        ai_result = await ai_service.generate_date_plan(
            raw_query      = enriched_query,
            history        = history,
            personas       = personas if personas else None,
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
            "venue_tags":    [],
            "missing_info":  [],
        }

    intent          = ai_result.get("intent", "chat")
    venue_tags      = ai_result.get("venue_tags") or []
    new_missing     = ai_result.get("missing_info") or []
    chat_response   = ai_result.get("chat_response", "")
    gift_suggestion = ai_result.get("gift_suggestion")
    event_type      = ai_result.get("event_type")

    # --- Persona Flow ---
    
    save_persona_data = ai_result.get("save_persona")
    ask_save_persona  = ai_result.get("ask_save_persona", False)
    _query_lower_pers = user_query.lower().strip()
    _YES_SIGNALS      = ["yes", "sure", "ok", "okay", "save", "please", "yep", "yeah", "do it"]
    _user_said_yes    = any(s in _query_lower_pers for s in _YES_SIGNALS)

    if save_persona_data and isinstance(save_persona_data, dict) and _user_said_yes:
        try:
            name = save_persona_data.get("name", "").strip()
            if name:
                existing = persona_service.get_personas(db, str(current_customer.customer_id))
                already_exists = any(
                    p.name.lower() == name.lower() for p in existing
                )
                if not already_exists:
                    pdata = {
                        "name":              name,
                        "relationship":      save_persona_data.get("relationship"),
                        "personality":       save_persona_data.get("personality"),
                        "food_preferences":  save_persona_data.get("food_preferences") or [],
                        "music_preferences": save_persona_data.get("music_preferences") or [],
                        "personality_tags":  save_persona_data.get("personality_tags") or [],
                        "color_preferences": save_persona_data.get("color_preferences") or [],
                    }
                    
                    age = save_persona_data.get("age")
                    if age:
                        pdata["personality"] = (
                            (pdata["personality"] or "") + f" Age: {age}"
                        ).strip()

                    new_persona = persona_service.create_persona(
                        db,
                        customer_id=str(current_customer.customer_id),
                        data=pdata,
                    )
                    
                    persona_service.confirm_persona(
                        db, new_persona.persona_id, str(current_customer.customer_id)
                    )
                    logger.info(
                        f"PERSONA AUTO-SAVED & CONFIRMED from chat: "
                        f"{new_persona.persona_id} name='{name}'"
                    )
                    personas = persona_service.get_personas(db, str(current_customer.customer_id))
        except Exception as e:
            logger.warning(f"Persona auto-save failed: {e}")

    use_persona_name = ai_result.get("use_persona_name", "").strip() if ai_result.get("use_persona_name") else ""
    if use_persona_name and personas:
        matched_persona = next(
            (p for p in personas if p.name.lower() == use_persona_name.lower()),
            None,
        )
        if matched_persona and not matched_persona.is_confirmed:
            try:
                persona_service.confirm_persona(
                    db,
                    matched_persona.persona_id,
                    str(current_customer.customer_id),
                )
                personas = persona_service.get_personas(db, str(current_customer.customer_id))
                logger.info(f"PERSONA CONFIRMED via AI suggestion: '{use_persona_name}'")
            except Exception as e:
                logger.warning(f"Persona auto-confirm failed: {e}")

    # --- Multi-Intent Detection ---
    
    _query_lower = (user_query or "").lower()
    _GIFT_SIGNALS = ["gift", "present", "buy", "surprise", "something for", "get her", "get him"]
    _PLAN_SIGNALS = ["venue", "dinner", "restaurant", "party", "book", "plan", 
                     "celebrate", "event", "wedding", "birthday", "anniversary",
                     "arrange", "find a place"]
                     
    _has_gift_signal = any(s in _query_lower for s in _GIFT_SIGNALS)
    _has_plan_signal = any(s in _query_lower for s in _PLAN_SIGNALS)

    if _has_gift_signal and _has_plan_signal:
        intent = "multi"
        logger.info("MULTI-INTENT DETECTED: running both venue + gift matchers.")

    # 7. Venue / Gift Matching
    matched_venues   = []
    venue_match_tier = None

    budget_for_filter   = ai_result.get("budget_per_head") or extracted_budget
    location_for_filter = ai_result.get("location") or extracted_location

    if intent == "multi" and venue_tags:
        # Venue matching
        pkgs = vendor_service.find_perfect_matches(
            db,
            criteria={
                "venue_tags":      venue_tags,
                "budget_per_head": budget_for_filter,
                "location":        location_for_filter,
                "guest_count":     extracted_guests,
            },
        )
        matched_venues = [_package_to_dict(p, requested_tags=venue_tags) for p in pkgs]

        # Gift matching
        gift_tags = list(venue_tags)
        response_lower = (chat_response or "").lower()
        for persona in personas:
            if persona.name and persona.name.lower() in response_lower:
                hobbies      = list(persona.preferences_json or [])
                food_tags    = list(persona.food_preferences  or [])
                music_tags   = list(persona.music_preferences or [])
                p_tags       = list(persona.personality_tags  or [])
                merged       = list(set(hobbies + food_tags + music_tags + p_tags))
                gift_tags    = list(set(gift_tags + merged))
                logger.info(f"PERSONA '{persona.name}' merged all preference tags into gift tags: {merged}")
                
        gift_pkgs = vendor_service.find_gift_matches(
            db,
            gift_tags=gift_tags,
            budget=budget_for_filter,
        )
        
        if gift_pkgs and not gift_suggestion:
            first_gift = gift_pkgs[0]
            gift_suggestion = (
                f"{first_gift.name} - {getattr(first_gift, 'description', '') or ''}"
            ).strip(" -")

        logger.info(
            f"MULTI VENUES: {len(matched_venues)} | "
            f"GIFT: {'yes' if gift_suggestion else 'no'}"
        )

    elif intent in ("planning", "date", "gift") and venue_tags:
        if intent == "gift":
            gift_tags = list(venue_tags)
            response_lower = (chat_response or "").lower()
            for persona in personas:
                if persona.name and persona.name.lower() in response_lower:
                    hobbies      = list(persona.preferences_json or [])
                    food_tags    = list(persona.food_preferences  or [])
                    music_tags   = list(persona.music_preferences or [])
                    p_tags       = list(persona.personality_tags  or [])
                    merged       = list(set(hobbies + food_tags + music_tags + p_tags))
                    gift_tags    = list(set(gift_tags + merged))
                    logger.info(f"PERSONA '{persona.name}' merged all preference tags: {merged}")
                    
            pkgs = vendor_service.find_gift_matches(
                db,
                gift_tags=gift_tags,
                budget=budget_for_filter,
            )
        else:
            pkgs = vendor_service.find_perfect_matches(
                db,
                criteria={
                    "venue_tags":      venue_tags,
                    "budget_per_head": budget_for_filter,
                    "location":        location_for_filter,
                    "guest_count":     extracted_guests,
                },
            )

        matched_venues = [_package_to_dict(p, requested_tags=venue_tags) for p in pkgs]

        if pkgs:
            canonical_loc = vendor_service.extract_location_from_text(
                location_for_filter or ""
            )
            first = pkgs[0]
            pkg_tags = first.tags or []
            if isinstance(pkg_tags, str):
                import json as _json
                try:
                    pkg_tags = _json.loads(pkg_tags)
                except Exception:
                    pkg_tags = []
            
            all_tags_match = set(venue_tags).issubset(set(pkg_tags))
            loc_match = canonical_loc and canonical_loc in (
                getattr(first, "location_coverage", "") or ""
            ).lower()
            
            if all_tags_match and loc_match:
                venue_match_tier = 1
            elif all_tags_match:
                venue_match_tier = 2
            else:
                venue_match_tier = 3

        logger.info(
            f"VENUES: {len(matched_venues)} matched "
            f"(tier={venue_match_tier}, intent={intent}, tags={venue_tags}, "
            f"location={location_for_filter})"
        )

    # 8. Persist message
    chat_service.save_message(
        db,
        session_id   = session_id,
        user_msg     = user_query,
        ai_msg       = chat_response or "",
        customer_id  = current_customer.customer_id,
        missing_info = new_missing,
    )

    _persona_saved = (
        bool(save_persona_data) and _user_said_yes
        and isinstance(save_persona_data, dict)
        and bool(save_persona_data.get("name", "").strip())
    )
    _persona_confirmed = bool(use_persona_name)

    return PlanResponse(
        intent             = intent,
        chat_response      = chat_response,
        matched_venues     = matched_venues,
        gift_suggestion    = gift_suggestion,
        missing_info       = new_missing,
        venue_match_tier   = venue_match_tier,
        event_type         = event_type,
        location           = ai_result.get("location") or extracted_location,
        budget_per_head    = ai_result.get("budget_per_head") or extracted_budget,
        guest_count        = ai_result.get("guest_count") or extracted_guests,
        venue_tags         = venue_tags,
        ask_save_persona   = bool(ask_save_persona),
        persona_saved      = _persona_saved,
        persona_confirmed  = _persona_confirmed,
    )