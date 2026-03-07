"""
planning_router.py — wires all 5 AI improvements:

  Fix 1  conversation summary compression  (chat_service.build_context_string)
  Fix 2  location filtering                (vendor_service.find_venue_matches)
  Fix 3  budget / guest-count extraction   (regex on user_query + history)
  Fix 4  confidence-scored fallback        (find_venue_matches tiers 1-3)
  Fix 5  blocked-dates awareness           (vendor_service.get_availability_block)
"""

import logging
import re
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.routers.v1.auth_router import get_current_customer
from app.models.customer import Customer
from app.models.persona import Persona
from app.services.ai_service import ai_service
from app.services.chat_service import chat_service
from app.services.vendor_service import vendor_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/planning", tags=["Planning"])

_SESSION_RE = re.compile(r'^[a-zA-Z0-9_\-]{1,64}$')


# ── Request / Response schemas ───────────────────────────────────────────────

class PlanRequest(BaseModel):
    session_id: str
    user_query: str

    @validator("session_id")
    def _validate_session(cls, v):
        if not _SESSION_RE.match(v):
            raise ValueError(
                "session_id must be 1-64 alphanumeric / dash / underscore characters"
            )
        return v


class PlanResponse(BaseModel):
    intent: Optional[str]
    chat_response: Optional[str]
    matched_venues: list = []
    gift_suggestion: Optional[str] = None
    missing_info: list = []
    venue_match_tier: Optional[int] = None   # 1=exact+loc, 2=exact, 3=partial


# ── Helpers ──────────────────────────────────────────────────────────────────

_BUDGET_RE = re.compile(
    r'(?:budget|spend|spending|cost|costs|afford|price)[^\d]{0,10}(\d[\d,]*)',
    re.IGNORECASE,
)
_GUEST_RE = re.compile(
    r'(\d+)\s*(?:people|guests?|persons?|pax)',
    re.IGNORECASE,
)
_DATE_RE = re.compile(
    r'(\d{4}-\d{2}-\d{2})',   # ISO date in query
)


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


def _package_to_dict(pkg) -> dict:
    return {
        "id":          pkg.id,
        "name":        pkg.name,
        "description": pkg.description,
        "price":       getattr(pkg, "price", None),
        "price_per_head": getattr(pkg, "price_per_head", None),
        "tags":        pkg.tags or [],
        "location":    getattr(pkg, "location_coverage", None),
    }


# ── Main endpoint ─────────────────────────────────────────────────────────────

@router.post("/generate", response_model=PlanResponse)
async def generate_plan(
    request: PlanRequest,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    session_id  = request.session_id
    user_query  = request.user_query

    # ── 1. Load conversation history ─────────────────────────────────────────
    history = chat_service.get_session_history(db, session_id)

    # ── 2. Load missing_info from previous turn (Fix 4 carry-over) ───────────
    prev_missing = chat_service.get_last_missing_info(db, session_id)

    # ── 3. FIX 3: Extract structured values from the current message ─────────
    #    and from recent history so we don't re-ask for things already told.
    all_text = user_query + " ".join(
        (m.user_message or "") for m in history[-5:]
    )

    extracted_budget   = _extract_budget(all_text)
    extracted_guests   = _extract_guests(all_text)
    extracted_location = vendor_service.extract_location_from_text(all_text)
    extracted_date     = _extract_date(all_text)

    # Remove from missing_info anything we just extracted
    resolved = set()
    if extracted_budget   is not None: resolved.add("budget")
    if extracted_guests   is not None: resolved.add("guest_count")
    if extracted_location is not None: resolved.add("location")
    if extracted_date     is not None: resolved.add("event_date")

    active_missing = [m for m in prev_missing if m not in resolved]

    logger.info(
        f"🔍 EXTRACTED: budget={extracted_budget}, guests={extracted_guests}, "
        f"location={extracted_location}, date={extracted_date} | "
        f"resolved={resolved} | still_missing={active_missing}"
    )

    # ── 4. Load personas ──────────────────────────────────────────────────────
    personas = (
        db.query(Persona)
        .filter(Persona.customer_id == current_customer.customer_id)
        .all()
    )

    # ── 5. Get real venue tags from DB ────────────────────────────────────────
    available_tags = vendor_service.get_all_tags(db)

    # ── 6. FIX 5: Build availability block for AI prompt ─────────────────────
    availability_block = ""
    if available_tags:
        availability_block = vendor_service.get_availability_block(
            db, tags=available_tags[:20]   # cap to avoid huge prompt
        )

    # ── 7. Build compressed context string (Fix 1) ───────────────────────────
    context_string_override = None   # ai_service builds it internally

    # ── 8. Call AI ────────────────────────────────────────────────────────────
    try:
        # Inject extracted facts + availability block into query
        enriched_query = user_query
        if extracted_budget or extracted_guests or extracted_location:
            fact_parts = []
            if extracted_budget:   fact_parts.append(f"budget={extracted_budget}")
            if extracted_guests:   fact_parts.append(f"guests={extracted_guests}")
            if extracted_location: fact_parts.append(f"location={extracted_location}")
            if extracted_date:     fact_parts.append(f"date={extracted_date}")
            enriched_query = (
                f"{user_query}\n"
                f"[SYSTEM EXTRACTED FACTS: {', '.join(fact_parts)}]"
            )

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
        logger.error(f"🔥 AI call failed: {exc}")
        ai_result = {
            "intent":       "chat",
            "chat_response": (
                "I'm having a little trouble connecting right now. "
                "Could you try again in a moment?"
            ),
            "venue_tags":   [],
            "missing_info": [],
        }

    intent        = ai_result.get("intent", "chat")
    venue_tags    = ai_result.get("venue_tags") or []
    new_missing   = ai_result.get("missing_info") or []
    chat_response = ai_result.get("chat_response", "")
    gift_suggestion = ai_result.get("gift_suggestion")

    # ── 9. Venue / gift matching (Fix 2 + Fix 4) ─────────────────────────────
    matched_venues = []
    venue_match_tier = None

    if intent in ("planning", "date", "gift") and venue_tags:

        # Determine budget for filtering (AI value takes priority over extracted)
        budget_for_filter = (
            ai_result.get("budget_per_head")
            or extracted_budget
        )

        # Location: AI may return it, else we extracted it from text
        location_for_filter = (
            ai_result.get("location")
            or extracted_location
        )

        event_date_for_filter = extracted_date

        if intent == "gift":
            # Persona enrichment: merge hobbies if persona name mentioned
            gift_tags = list(venue_tags)
            response_lower = (chat_response or "").lower()
            for persona in personas:
                if persona.name and persona.name.lower() in response_lower:
                    hobbies = persona.preferences_json or []
                    gift_tags = list(set(gift_tags + hobbies))
                    logger.info(
                        f"👤 PERSONA '{persona.name}' matched — "
                        f"merged hobbies: {hobbies}"
                    )
            pkgs = vendor_service.find_gift_matches(
                db,
                gift_tags=gift_tags,
                budget=budget_for_filter,
                location=location_for_filter,
            )
        else:
            pkgs = vendor_service.find_venue_matches(
                db,
                tags=venue_tags,
                budget=budget_for_filter,
                location=location_for_filter,
                event_date=event_date_for_filter,
            )

        matched_venues = [_package_to_dict(p) for p in pkgs]

        # Determine tier for response metadata
        if pkgs:
            # Infer tier from log (simplistic: check if all tags present + location)
            canonical_loc = vendor_service.extract_location_from_text(
                location_for_filter or ""
            )
            first = pkgs[0]
            all_tags_match = set(venue_tags).issubset(set(first.tags or []))
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
            f"🏠 VENUES: {len(matched_venues)} matched "
            f"(tier={venue_match_tier}, intent={intent}, tags={venue_tags}, "
            f"location={location_for_filter})"
        )

    # ── 10. Save message to DB ────────────────────────────────────────────────
    chat_service.save_message(
        db,
        session_id   = session_id,
        user_msg     = user_query,
        ai_msg       = chat_response or "",
        customer_id  = current_customer.customer_id,
        missing_info = new_missing,
    )

    return PlanResponse(
        intent           = intent,
        chat_response    = chat_response,
        matched_venues   = matched_venues,
        gift_suggestion  = gift_suggestion,
        missing_info     = new_missing,
        venue_match_tier = venue_match_tier,
    )


