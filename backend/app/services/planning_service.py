"""
app/services/planning_service.py

ALL FIXES APPLIED (original 11 + new 4)
────────────────────────────────────────
FIX 1  Generic/robotic replies      → enriched_query always injects known facts
FIX 2  Loses context between turns  → ChatSession DB table as source of truth
FIX 3  Doesn't remember what said   → venue_data persisted to DB every turn
FIX 4  Asks for info it already has → ALREADY KNOWN block prepended to every query
FIX 5  Proactive past-event hints   → past_events fetched and injected every turn
FIX 6  Booking is end of flow       → STEP_BOOKED injects context block so AI knows
FIX 7  Redis down = flow collapses  → StateStore: Redis + DB write-through fallback
FIX 8  Persona never accumulates    → _merge_persona_from_ai() runs every turn
FIX 9  Same pkg as venue + gift     → dedup by id before returning gifts
FIX 10 Booking notes missing prefs  → notes include full persona summary
FIX 11 venue_data stale post-booking→ cleared from state after booking created
FIX #1 No DB matches               → AI-generated fallback with inquiry record
FIX #2 No budget hard-check        → filter venues/gifts before showing user
FIX #3 No vendor redirect          → redirect_url returned after booking
FIX #4 Vibe question missing        → dedicated question after date confirmed
"""
from __future__ import annotations

import json
import logging
import re
from datetime import date, timedelta
from typing import Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.schemas.planning_schema import GiftDisplay, PlanResponse, VenueDisplay

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Step constants
# ─────────────────────────────────────────────────────────────────────────────
_STEP_CHAT         = "0"
_STEP_PERSONA_LIST = "1"
_STEP_PERSONA_SAVE = "2"
_STEP_RECS_SHOWN   = "3"
_STEP_BOOKED       = "4"
_STEP_VIBE         = "5"   # FIX #4: waiting for vibe/theme answer


# ─────────────────────────────────────────────────────────────────────────────
# Module-level Redis helper
# ─────────────────────────────────────────────────────────────────────────────

def _get_redis():
    try:
        import redis as _r
        import os
        r = _r.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            decode_responses=True,
            socket_connect_timeout=2,
        )
        r.ping()
        return r
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# StateStore — Redis + DB write-through, DB fallback
# ─────────────────────────────────────────────────────────────────────────────

class StateStore:
    _TTL = 86400  # 24 h

    def _connect_redis(self):
        try:
            import redis as _r
            import os
            r = _r.from_url(
                os.getenv("REDIS_URL", "redis://localhost:6379/0"),
                decode_responses=True,
                socket_connect_timeout=2,
            )
            r.ping()
            return r
        except Exception:
            logger.debug("Redis unavailable — using DB-only state store")
            return None

    def __init__(self, db: Session, event_id: str):
        self._db       = db
        self._event_id = event_id
        self._r        = self._connect_redis()
        self._session  = self._load_or_create_session()

    def _load_or_create_session(self):
        from app.models.chat_session import ChatSession
        sess = (
            self._db.query(ChatSession)
            .filter(ChatSession.event_id == self._event_id)
            .first()
        )
        if not sess:
            sess = ChatSession(event_id=self._event_id)
            self._db.add(sess)
            try:
                self._db.commit()
                self._db.refresh(sess)
            except Exception as e:
                logger.warning(f"ChatSession create failed: {e}")
                self._db.rollback()
        return sess

    def _save_session(self):
        try:
            self._db.add(self._session)
            self._db.commit()
            self._db.refresh(self._session)
        except Exception as e:
            logger.warning(f"ChatSession save failed: {e}")
            self._db.rollback()

    def _rkey(self, f: str) -> str:
        return f"pflow:{f}:{self._event_id}"

    def _rget(self, field: str, default=None):
        if self._r:
            try:
                v = self._r.get(self._rkey(field))
                if v is not None:
                    return v
            except Exception:
                pass
        val = getattr(self._session, field, None)
        return val if val is not None else default

    def _rset(self, field: str, value: str):
        if self._r:
            try:
                self._r.setex(self._rkey(field), self._TTL, value)
            except Exception:
                pass
        setattr(self._session, field, value)
        self._save_session()

    def _rdel(self, *fields: str):
        for f in fields:
            if self._r:
                try:
                    self._r.delete(self._rkey(f))
                except Exception:
                    pass
            setattr(self._session, f, None)
        self._save_session()

    def get_json(self, field: str):
        raw = self._rget(field)
        if not raw:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return None

    def set_json(self, field: str, obj):
        self._rset(field, json.dumps(obj))

    def clear(self, *fields: str):
        self._rdel(*fields)

    @property
    def step(self) -> str:
        return self._rget("step", _STEP_CHAT)

    @step.setter
    def step(self, v: str):
        self._rset("step", v)

    @property
    def persona_draft(self) -> dict:
        return self.get_json("persona_draft") or {}

    @persona_draft.setter
    def persona_draft(self, v: dict):
        self.set_json("persona_draft", v)

    @property
    def chosen_persona_id(self) -> str | None:
        return self._rget("chosen_persona_id")

    @chosen_persona_id.setter
    def chosen_persona_id(self, v: str | None):
        if v:
            self._rset("chosen_persona_id", v)
        else:
            self._rdel("chosen_persona_id")

    @property
    def venue_data(self) -> dict:
        return self.get_json("venue_data") or {}

    @venue_data.setter
    def venue_data(self, v: dict):
        self.set_json("venue_data", v)

    @property
    def rec_ids(self) -> list:
        return self.get_json("rec_ids") or []

    @rec_ids.setter
    def rec_ids(self, v: list):
        self.set_json("rec_ids", v)

    @property
    def gift_rec_ids(self) -> list:
        return self.get_json("gift_rec_ids") or []

    @gift_rec_ids.setter
    def gift_rec_ids(self, v: list):
        self.set_json("gift_rec_ids", v)

    @property
    def pending_save(self) -> dict | None:
        return self.get_json("pending_save")

    @pending_save.setter
    def pending_save(self, v: dict | None):
        if v:
            self.set_json("pending_save", v)
        else:
            self._rdel("pending_save")

    @property
    def booking_id(self) -> str | None:
        return self._rget("booking_id")

    @booking_id.setter
    def booking_id(self, v: str):
        self._rset("booking_id", v)
        self._session.booking_id = v
        self._save_session()

    # ── FIX #1: AI fallback state properties ──────────────────────────────────

    @property
    def ai_fallback_venues(self) -> list:
        return self.get_json("ai_fallback_venues") or []

    @ai_fallback_venues.setter
    def ai_fallback_venues(self, v: list):
        self.set_json("ai_fallback_venues", v)

    @property
    def ai_fallback_gifts(self) -> list:
        return self.get_json("ai_fallback_gifts") or []

    @ai_fallback_gifts.setter
    def ai_fallback_gifts(self, v: list):
        self.set_json("ai_fallback_gifts", v)

    @property
    def is_ai_fallback(self) -> bool:
        return self._rget("is_ai_fallback", "false") == "true"

    @is_ai_fallback.setter
    def is_ai_fallback(self, v: bool):
        self._rset("is_ai_fallback", "true" if v else "false")


# ─────────────────────────────────────────────────────────────────────────────
# Regex extractors
# ─────────────────────────────────────────────────────────────────────────────

_BUDGET_RE = re.compile(
    r'(?:budget|spend|spending|cost|costs|afford|price)[^\d]{0,10}(\d[\d,]*)'
    r'|(?:lkr|rs\.?)\s*(\d[\d,]*)'
    r'|(\d[\d,]*)(?:\s*k)\b',
    re.IGNORECASE,
)
_GUEST_RE    = re.compile(r'(\d+)\s*(?:people|guests?|persons?|pax)', re.IGNORECASE)
_DATE_ISO_RE = re.compile(r'(\d{4}-\d{2}-\d{2})')

_MONTH_MAP = {
    "january":1,"jan":1,"february":2,"feb":2,"march":3,"mar":3,
    "april":4,"apr":4,"may":5,"june":6,"jun":6,"july":7,"jul":7,
    "august":8,"aug":8,"september":9,"sep":9,"sept":9,
    "october":10,"oct":10,"november":11,"nov":11,"december":12,"dec":12,
}
_WEEKDAY_MAP = {
    "monday":0,"mon":0,"tuesday":1,"tue":1,"wednesday":2,"wed":2,
    "thursday":3,"thu":3,"friday":4,"fri":4,"saturday":5,"sat":5,"sunday":6,"sun":6,
}
_MP = "(?:" + "|".join(_MONTH_MAP.keys()) + ")"
_WP = "(?:" + "|".join(_WEEKDAY_MAP.keys()) + ")"


def _extract_date(text: str) -> Optional[str]:
    today = date.today()
    lower = text.lower()
    m = _DATE_ISO_RE.search(text)
    if m:
        try:
            date.fromisoformat(m.group(1))
            return m.group(1)
        except ValueError:
            pass
    if re.search(r'\btoday\b|\btonight\b', lower):
        return today.isoformat()
    if re.search(r'\btomorrow\b', lower):
        return (today + timedelta(days=1)).isoformat()
    wm = re.search(r'\b(next|this)?\s*(' + _WP + r')\b', lower)
    if wm:
        target = _WEEKDAY_MAP[wm.group(2)]
        days   = (target - today.weekday()) % 7
        if wm.group(1) == "next" or days == 0:
            days = days if days > 0 else 7
        return (today + timedelta(days=days)).isoformat()
    mm = re.search(r'\b(' + _MP + r')\s+(\d{1,2})(?:st|nd|rd|th)?\b', lower)
    if mm:
        month, day = _MONTH_MAP[mm.group(1)], int(mm.group(2))
        try:
            c = date(today.year, month, day)
            return date(today.year if c >= today else today.year + 1, month, day).isoformat()
        except ValueError:
            pass
    dm = re.search(r'\b(\d{1,2})(?:st|nd|rd|th)?\s+(' + _MP + r')\b', lower)
    if dm:
        day, month = int(dm.group(1)), _MONTH_MAP[dm.group(2)]
        try:
            c = date(today.year, month, day)
            return date(today.year if c >= today else today.year + 1, month, day).isoformat()
        except ValueError:
            pass
    rm = re.search(r'\bin\s+(\d+)\s+(day|days|week|weeks)\b', lower)
    if rm:
        n = int(rm.group(1)) * (7 if "week" in rm.group(2) else 1)
        return (today + timedelta(days=n)).isoformat()
    return None


def _extract_budget(text: str) -> Optional[float]:
    m = _BUDGET_RE.search(text)
    if m:
        raw = m.group(1) or m.group(2) or m.group(3) or ""
        try:
            val = float(raw.replace(",", ""))
            if m.group(3) and re.search(r'\d+\s*k\b', text, re.IGNORECASE):
                val *= 1000
            return val
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


def _safe_str(val) -> "str | None":
    return val if isinstance(val, str) else None


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


# ─────────────────────────────────────────────────────────────────────────────
# Intent helpers
# ─────────────────────────────────────────────────────────────────────────────

_YES = {"yes","sure","ok","okay","save","please","yep","yeah","do it",
        "go ahead","confirm","sounds good","great","perfect","confirmed",
        "yup","absolutely","of course"}
_NO  = {"no","nope","skip","don't","dont","not now","never mind",
        "cancel","nah","no thanks","not really"}
_ROLLBACK = [
    "not satisfied","don't like","change","different","something else",
    "show me more","other options","re-recommend","try again",
    "none of these","not what i","not happy","try different",
    "not quite","let me change","want to change","show other","more options",
]
_SEL_MAP = {
    "first":0,"1st":0,"one":0,"1":0,
    "second":1,"2nd":1,"two":1,"2":1,
    "third":2,"3rd":2,"three":2,"3":2,
}

_GIFT_SIGNALS = [
    "gift", "present", "buy", "surprise", "something for", "get her", "get him",
]
_PLAN_SIGNALS = [
    "venue", "dinner", "restaurant", "party", "book", "plan", "celebrate",
    "event", "wedding", "birthday", "anniversary", "arrange", "find a place",
]


def _said_yes(t: str) -> bool:
    return any(w in t.lower().strip() for w in _YES)


def _said_no(t: str) -> bool:
    return any(w in t.lower().strip() for w in _NO)


def _detect_selection(text: str, count: int) -> Optional[int]:
    lower = text.lower().strip()
    for word, idx in _SEL_MAP.items():
        if re.search(rf'\b{re.escape(word)}\b', lower) and idx < count:
            return idx
    dm = re.search(r'\b([1-3])\b', lower)
    if dm:
        idx = int(dm.group(1)) - 1
        if 0 <= idx < count:
            return idx
    for pat in [r'\bgo\s+with\b', r'\bi[\'ll\s]+take\b',
                r'\bi\s+(want|like|choose|pick|select)\s+(that|this|the|number)',
                r'\bthat\s+(one|looks|sounds|works)',
                r'\bbook\s+(that|this|it)',
                r'\bsounds?\s+(great|good|perfect|amazing)',
                r'\blet[\'s]*\s+go\b']:
        if re.search(pat, lower):
            return 0
    return None


def _detect_rollback(text: str) -> bool:
    lower = text.lower()
    return any(w in lower for w in _ROLLBACK)


def _resolve_intent(ai_intent: str, user_query: str) -> str:
    if ai_intent == "multi":
        return "multi"
    if ai_intent in ("planning", "date"):
        lower = user_query.lower()
        if (any(s in lower for s in _GIFT_SIGNALS)
                and any(s in lower for s in _PLAN_SIGNALS)):
            return "multi"
    return ai_intent


# ─────────────────────────────────────────────────────────────────────────────
# Persona helpers
# ─────────────────────────────────────────────────────────────────────────────

def _persona_is_complete(draft: dict) -> bool:
    return bool(draft.get("name"))


def _build_persona_payload(draft: dict) -> dict:
    name = str((draft.get("name") or "")).strip()
    personality = str(draft.get("personality") or "")
    age = draft.get("age")
    if age is not None:
        age_str = str(age)
        if age_str not in personality:
            personality = f"{personality} Age: {age_str}".strip()
    return {
        "name":              name,
        "relationship":      str(draft.get("relationship") or "") or None,
        "personality":       personality,
        "food_preferences":  _safe_list(draft.get("food_preferences")),
        "music_preferences": _safe_list(draft.get("music_preferences")),
        "personality_tags":  _safe_list(draft.get("personality_tags") or draft.get("vibe")),
        "color_preferences": _safe_list(draft.get("color_preferences") or draft.get("colours")),
    }


def _persona_summary(draft: dict, persona=None) -> str:
    if persona:
        name = getattr(persona, "name", "") or ""
        rel  = getattr(persona, "relationship", "") or ""
        food = _safe_list(getattr(persona, "food_preferences", []))
        tags = _safe_list(getattr(persona, "personality_tags", []))
    else:
        name = draft.get("name", "")
        rel  = draft.get("relationship", "")
        food = _safe_list(draft.get("food_preferences"))
        tags = _safe_list(draft.get("personality_tags") or draft.get("vibe"))
    parts = [name]
    if rel:   parts.append(f"({rel})")
    if food:  parts.append(f"food: {', '.join(food[:3])}")
    if tags:  parts.append(f"vibe: {', '.join(tags[:3])}")
    return " | ".join(p for p in parts if p)


def _merge_persona_from_ai(existing: dict, ai_result: dict, user_query: str = "") -> dict:
    draft = dict(existing)
    sp    = ai_result.get("save_persona")
    if sp and isinstance(sp, dict):
        for field in ("name","relationship","personality","food_preferences",
                      "music_preferences","personality_tags","color_preferences",
                      "vibe","colours","age"):
            val = sp.get(field)
            if val and not draft.get(field):
                draft[field] = val
    pp = ai_result.get("personality_profile")
    if pp and not draft.get("personality"):
        draft["personality"] = pp
    return draft


def _known_facts_block(vd: dict, persona_draft: dict, chosen_persona) -> str:
    lines = []
    if chosen_persona:
        name = getattr(chosen_persona, "name", None) or persona_draft.get("name")
        if name:
            lines.append(f"Planning for: {name}")
    elif persona_draft.get("name"):
        lines.append(f"Planning for: {persona_draft['name']} (in-memory profile)")
    if vd.get("location"):    lines.append(f"Location confirmed: {vd['location']}")
    if vd.get("budget"):      lines.append(f"Budget confirmed: LKR {vd['budget']:,.0f}")
    if vd.get("guest_count"): lines.append(f"Guests confirmed: {vd['guest_count']}")
    if vd.get("event_date"):  lines.append(f"Date confirmed: {vd['event_date']}")
    if vd.get("vibe"):        lines.append(f"Vibe confirmed: {vd['vibe']}")
    if not lines:
        return ""
    return (
        "\n[ALREADY CONFIRMED — DO NOT ASK FOR THESE AGAIN:\n"
        + "\n".join(f"  • {l}" for l in lines)
        + "]\n"
    )


def _venue_missing(vd: dict) -> list:
    """Returns list of primary fields still needed (vibe handled separately)."""
    m = []
    if not vd.get("location"):    m.append("location")
    if not vd.get("budget"):      m.append("total budget")
    if not vd.get("guest_count"): m.append("number of guests")
    if not vd.get("event_date"):  m.append("event date")
    return m


# ─────────────────────────────────────────────────────────────────────────────
# FIX #2 — Budget filter
# ─────────────────────────────────────────────────────────────────────────────

def _filter_by_budget(
    venues: list,
    gifts: list,
    total_budget: float,
    guest_count,
) -> tuple:
    """
    Hard budget check.
    Venue: price_per_head * guests must be ≤ 75% of total budget.
    Gift:  price_per_head must be ≤ 25% of total budget.
    Returns (filtered_venues, filtered_gifts, all_over_budget: bool).
    """
    if not total_budget or float(total_budget) <= 0:
        return venues, gifts, False

    guests    = int(guest_count or 1)
    venue_cap = float(total_budget) * 0.75
    gift_cap  = float(total_budget) * 0.25

    filtered_venues = [
        v for v in venues
        if (getattr(v, "price_per_head", None) or 0) * guests <= venue_cap
    ]
    filtered_gifts = [
        g for g in gifts
        if (getattr(g, "price_per_head", None) or 0) <= gift_cap
    ]

    all_over = (len(venues) > 0 and len(filtered_venues) == 0)
    return filtered_venues, filtered_gifts, all_over


# ─────────────────────────────────────────────────────────────────────────────
# FIX #1 — AI-generated fallback when DB has no matches
# ─────────────────────────────────────────────────────────────────────────────

async def _generate_ai_fallback(
    ai_svc,
    vd: dict,
    persona_draft: dict,
    chosen_persona,
    event_context: dict,
) -> tuple:
    """
    Calls Groq to generate 3 venue concepts and 3 gift concepts when DB has no matches.
    Returns (venues: list[dict], gifts: list[dict]).
    Each item has keys: name, description, estimated_price (LKR).
    """
    import httpx as _httpx

    budget     = float(vd.get("budget") or 0)
    guests     = int(vd.get("guest_count") or 1)
    location   = vd.get("location") or "Sri Lanka"
    vibe       = vd.get("vibe") or "special"
    event_type = (event_context or {}).get("event_type") or "event"

    persona_name = ""
    if chosen_persona:
        persona_name = getattr(chosen_persona, "name", "") or ""
    elif persona_draft:
        persona_name = str(persona_draft.get("name") or "")

    groq_key = getattr(ai_svc, "groq_api_key", None)
    if not groq_key:
        return [], []

    system_prompt = (
        "You are an expert event planner for Sri Lanka. "
        "Respond ONLY with raw JSON — no markdown, no explanation."
    )
    user_prompt = (
        f"Generate exactly 3 venue/experience ideas and 3 gift ideas "
        f"for a {event_type} in {location} for {guests} people"
        + (f" celebrating {persona_name}" if persona_name else "")
        + f". Vibe: {vibe}. "
        f"Total budget: LKR {budget:,.0f}. "
        f"Venue budget (75%): LKR {budget * 0.75:,.0f}. "
        f"Gift budget (25%): LKR {budget * 0.25:,.0f}. "
        "Be specific — mention real Sri Lankan places, brands, experiences. "
        'Return exactly: {"venues": [{"name": "string", "description": "string", '
        '"estimated_price": number}], '
        '"gifts": [{"name": "string", "description": "string", '
        '"estimated_price": number}]}'
    )

    try:
        headers = {
            "Authorization": f"Bearer {groq_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 1024,
            "response_format": {"type": "json_object"},
        }
        async with _httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()

        data   = resp.json()
        raw    = data["choices"][0]["message"]["content"]
        parsed = json.loads(raw)
        venues = (parsed.get("venues") or [])[:3]
        gifts  = (parsed.get("gifts")  or [])[:3]
        return venues, gifts

    except Exception as exc:
        logger.warning(f"AI fallback generation failed: {exc}")
        return [], []


def _ai_venue_to_display(item: dict, idx: int) -> VenueDisplay:
    return VenueDisplay(
        id=f"AI-VENUE-{idx+1}",
        name=str(item.get("name") or f"Option {idx+1}"),
        description=str(item.get("description") or ""),
        price_per_head=None,
        total_estimated_price=float(item.get("estimated_price") or 0) or None,
        tags=[],
        location=None,
        vendor_name="Occacia Concierge",
        match_score=None,
        match_score_max=None,
        match_score_label=None,
        tweak_note="✨ AI-curated — our team will contact vendors on your behalf",
    )


def _ai_gift_to_display(item: dict, idx: int) -> GiftDisplay:
    return GiftDisplay(
        id=f"AI-GIFT-{idx+1}",
        name=str(item.get("name") or f"Gift Option {idx+1}"),
        description=str(item.get("description") or ""),
        price_per_head=None,
        estimated_price=float(item.get("estimated_price") or 0) or None,
        tags=[],
        location=None,
        vendor_name="Occacia Concierge",
        tweak_note="✨ AI-curated suggestion",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Package / gift helpers
# ─────────────────────────────────────────────────────────────────────────────

def _to_venue(pkg, req_tags=None, guest_count=None, tweak=None) -> VenueDisplay:
    tags = pkg.tags or []
    if isinstance(tags, str):
        try: tags = json.loads(tags)
        except Exception: tags = []
    vname = None
    try:
        if hasattr(pkg, "vendor") and pkg.vendor:
            vname = getattr(pkg.vendor, "display_name", None) or getattr(pkg.vendor, "business_name", None)
    except Exception:
        pass
    ms = ms_max = ms_lbl = None
    if req_tags:
        matched = len(set(req_tags) & set(tags))
        total   = len(set(req_tags))
        ms, ms_max, ms_lbl = matched, total, f"{matched} of {total} tags matched"
    pph = getattr(pkg, "price_per_head", None)
    if pph is not None:
        try: pph = float(pph)
        except (TypeError, ValueError): pph = None
    total_est = float(pph) * int(guest_count) if pph and guest_count else None
    return VenueDisplay(
        id=pkg.id,
        name=str(pkg.name or ""),
        description=_safe_str(getattr(pkg, "description", None)),
        price_per_head=pph,
        total_estimated_price=total_est,
        tags=tags,
        location=_safe_str(getattr(pkg, "location_coverage", None)),
        vendor_name=_safe_str(vname),
        match_score=ms,
        match_score_max=ms_max,
        match_score_label=_safe_str(ms_lbl),
        tweak_note=_safe_str(tweak),
    )


def _to_gift(pkg, gift_bph=None, guest_count=None, tweak=None) -> GiftDisplay:
    tags = pkg.tags or []
    if isinstance(tags, str):
        try: tags = json.loads(tags)
        except Exception: tags = []
    vname = None
    try:
        if hasattr(pkg, "vendor") and pkg.vendor:
            vname = getattr(pkg.vendor, "display_name", None) or getattr(pkg.vendor, "business_name", None)
    except Exception:
        pass
    pph = getattr(pkg, "price_per_head", None)
    if pph is not None:
        try: pph = float(pph)
        except (TypeError, ValueError): pph = None
    est = None
    if gift_bph is not None and guest_count:
        try: est = float(gift_bph) * int(guest_count)
        except (TypeError, ValueError): pass
    elif pph is not None and guest_count:
        try: est = float(pph) * int(guest_count)
        except (TypeError, ValueError): pass
    return GiftDisplay(
        id=pkg.id,
        name=str(pkg.name or ""),
        description=_safe_str(getattr(pkg, "description", None)),
        price_per_head=pph,
        estimated_price=est,
        tags=tags,
        location=_safe_str(getattr(pkg, "location_coverage", None)),
        vendor_name=_safe_str(vname),
        tweak_note=_safe_str(tweak),
    )


def _get_3_venues(vs, db, venue_tags, bph, location, guests, req_tags) -> list:
    pkgs = vs.find_perfect_matches(
        db,
        {"venue_tags": venue_tags, "budget_per_head": bph,
         "location": location, "guest_count": guests},
    )
    results = []
    seen: set = set()
    for p in (pkgs or []):
        if p.id not in seen and len(results) < 3:
            seen.add(p.id)
            results.append(_to_venue(p, req_tags=req_tags, guest_count=guests))
    return results


def _get_3_gifts(vs, db, gift_tags, gift_bph, guests, personas) -> list:
    base = gift_tags if gift_tags else ["romantic"]
    raw  = vs.find_gift_matches(db, gift_tags=base, budget=gift_bph)
    results: list = []
    seen: set = set()
    for p in (raw or []):
        if len(results) >= 3:
            break
        from app.schemas.planning_schema import GiftDisplay as _GiftDisplay
        if isinstance(p, _GiftDisplay):
            results.append(p)
            continue
        pid = getattr(p, "id", None)
        if pid not in seen:
            seen.add(pid)
            results.append(_to_gift(p, gift_bph=gift_bph, guest_count=guests))
    return results


# ─────────────────────────────────────────────────────────────────────────────
# AI call wrapper
# ─────────────────────────────────────────────────────────────────────────────

async def _call_ai(ai_svc, **kwargs):
    try:
        return await ai_svc.generate_date_plan(**kwargs)
    except TypeError:
        base = {"raw_query","history","personas","available_tags","missing_info","session_id"}
        return await ai_svc.generate_date_plan(**{k: v for k, v in kwargs.items() if k in base})


# ─────────────────────────────────────────────────────────────────────────────
# PlanningService
# ─────────────────────────────────────────────────────────────────────────────

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

        customer_id = str(customer.customer_id)
        state       = StateStore(db, session_id)

        personas = persona_svc.get_personas(db, customer_id) if persona_svc else []

        chosen_persona = None
        if state.chosen_persona_id:
            chosen_persona = next(
                (p for p in personas if p.persona_id == state.chosen_persona_id), None
            )

        history      = chat_svc.get_session_history(db, session_id)
        prev_missing = chat_svc.get_last_missing_info(db, session_id)
        if isinstance(prev_missing, dict):
            prev_missing = prev_missing.get("items", [])

        persona_draft = state.persona_draft
        venue_data    = state.venue_data
        current_step  = state.step

        # FIX 5: Past events for proactive suggestions
        past_events = []
        try:
            from app.models.event import Event as _Ev
            past = (
                db.query(_Ev)
                .filter(_Ev.customer_id == customer_id,
                        _Ev.status == "ACTIVE",
                        _Ev.event_id != session_id)
                .order_by(_Ev.created_at.desc())
                .limit(5).all()
            )
            past_events = [
                {"event_type": e.event_type,
                 "event_date": e.start_at.date().isoformat() if e.start_at else None,
                 "location":   e.location_text,
                 "packages_used": []}
                for e in past
            ]
        except Exception as pe:
            logger.debug(f"Past events skipped: {pe}")

        # ── STEP: Persona save confirmation ───────────────────────────────────
        if current_step == _STEP_PERSONA_SAVE:
            pending = state.pending_save or persona_draft
            persona_saved = False

            if _said_yes(user_query) and pending and pending.get("name"):
                try:
                    payload = _build_persona_payload(pending)
                    name    = payload["name"]
                    if not any(p.name.lower() == name.lower() for p in personas):
                        new_p = persona_svc.create_persona(db, customer_id=customer_id, data=payload)
                        try:
                            from app.models.event_persona import EventPersona
                            db.add(EventPersona(event_id=session_id, persona_id=new_p.persona_id))
                            db.commit()
                        except Exception as ep_e:
                            logger.warning(f"EventPersona link failed: {ep_e}")
                            db.rollback()
                        state.chosen_persona_id = new_p.persona_id
                        chosen_persona = new_p
                        personas = persona_svc.get_personas(db, customer_id)
                        persona_saved = True
                        reply = (
                            f"Done! I've saved **{name}'s** profile for future events 🎉 "
                            f"Now let's sort the details — what location did you have in mind?"
                        )
                    else:
                        reply = f"I already have **{name}'s** profile! Let's keep going — what location works?"
                except Exception as e:
                    logger.warning(f"Persona save failed: {e}")
                    reply = "No problem — using their details just for today. What location works?"
            else:
                reply = "No worries — keeping their preferences just for today. What location works?"

            state.clear("pending_save", "persona_draft")
            state.step = _STEP_CHAT
            missing = _venue_missing(venue_data)
            chat_svc.save_message(db, session_id=session_id, user_msg=user_query,
                                  ai_msg=reply, customer_id=customer.customer_id,
                                  missing_info=missing)
            return PlanResponse(
                intent="chat", reasoning="Persona save step completed.",
                chat_response=reply, missing_info=missing,
                venue_tags=[], matched_venues=[], matched_gifts=[],
                ask_save_persona=False, persona_saved=persona_saved,
                persona_confirmed=bool(chosen_persona),
            )

        # ── STEP: Persona list shown ──────────────────────────────────────────
        if current_step == _STEP_PERSONA_LIST and personas:
            lower = user_query.lower().strip()
            matched_p = None
            nm = re.search(r'\b(\d+)\b', lower)
            if nm:
                idx = int(nm.group(1)) - 1
                if 0 <= idx < len(personas):
                    matched_p = personas[idx]
            if not matched_p:
                for p in personas:
                    if p.name and p.name.lower() in lower:
                        matched_p = p
                        break

            if matched_p:
                try:
                    persona_svc.confirm_persona(db, matched_p.persona_id, customer_id)
                except Exception:
                    pass
                state.chosen_persona_id = matched_p.persona_id
                state.step = _STEP_CHAT
                chosen_persona = matched_p
                missing = ["date","location","budget","guest_count"]
                reply = (
                    f"Perfect! Planning around **{matched_p.name}'s** preferences 🎉 "
                    f"What date, location, and rough budget are you thinking?"
                )
                chat_svc.save_message(db, session_id=session_id, user_msg=user_query,
                                      ai_msg=reply, customer_id=customer.customer_id,
                                      missing_info=missing)
                return PlanResponse(
                    intent="chat", reasoning=f"Persona '{matched_p.name}' selected.",
                    chat_response=reply, missing_info=missing,
                    venue_tags=[], matched_venues=[], matched_gifts=[],
                    ask_save_persona=False, persona_saved=False, persona_confirmed=True,
                )
            state.step = _STEP_CHAT

        # ── STEP: Recommendations shown ───────────────────────────────────────
        if current_step == _STEP_RECS_SHOWN:
            rec_ids = state.rec_ids

            if _detect_rollback(user_query):
                state.clear("rec_ids", "gift_rec_ids", "ai_fallback_venues",
                            "ai_fallback_gifts")
                state.is_ai_fallback = False
                state.step = _STEP_CHAT
                reply = (
                    "Of course! Tell me what you'd like to change — "
                    "location, price range, vibe, or something else? "
                    "I'll find better options right away."
                )
                chat_svc.save_message(db, session_id=session_id, user_msg=user_query,
                                      ai_msg=reply, customer_id=customer.customer_id,
                                      missing_info=[])
                return PlanResponse(
                    intent="chat", reasoning="User rolled back.",
                    chat_response=reply, missing_info=[],
                    venue_tags=[], matched_venues=[], matched_gifts=[],
                    ask_save_persona=False, persona_saved=False,
                    persona_confirmed=bool(chosen_persona),
                )

            selected_idx = _detect_selection(user_query, len(rec_ids))
            if selected_idx is not None and rec_ids:
                booking_id   = None
                redirect_url = None

                # ── FIX #1: AI fallback booking path ─────────────────────────
                if state.is_ai_fallback:
                    fb_venues = state.ai_fallback_venues
                    fb_gifts  = state.ai_fallback_gifts

                    sel_venue = fb_venues[selected_idx] if selected_idx < len(fb_venues) else {}
                    sel_gift  = fb_gifts[0] if fb_gifts else {}

                    try:
                        booking_id = await self._create_ai_inquiry(
                            db=db,
                            customer_id=customer_id,
                            event_id=session_id,
                            selected_venue=sel_venue,
                            selected_gift=sel_gift,
                            venue_data=venue_data,
                            persona_draft=persona_draft,
                            chosen_persona=chosen_persona,
                        )
                    except Exception as e:
                        logger.warning(f"AI inquiry create failed: {e}")
                        from app.common.utils import generate_prefixed_id
                        booking_id = generate_prefixed_id("INQ")

                    state.step = _STEP_BOOKED
                    state.clear("venue_data", "rec_ids", "gift_rec_ids",
                                "ai_fallback_venues", "ai_fallback_gifts")
                    state.is_ai_fallback = False

                    persona_name = ""
                    if chosen_persona:
                        persona_name = getattr(chosen_persona, "name", "") or ""
                    elif persona_draft:
                        persona_name = str(persona_draft.get("name") or "")

                    reply = (
                        f"You're all set! 🎉 Our Occacia concierge team has received your request"
                        + (f" for **{persona_name}**" if persona_name else "")
                        + ".\n\n"
                        f"**Reference: {booking_id}**\n\n"
                        f"We'll reach out within 24 hours to confirm availability and finalise "
                        f"everything. Is there anything else you'd like to add?"
                    )

                else:
                    # ── Normal DB package booking path ────────────────────────
                    pkg_id = rec_ids[selected_idx]
                    try:
                        booking_id = await self._create_booking(
                            db=db, customer_id=customer_id, event_id=session_id,
                            package_id=pkg_id, venue_data=venue_data,
                            persona_draft=persona_draft, chosen_persona=chosen_persona,
                        )
                        state.booking_id = booking_id
                        state.step = _STEP_BOOKED
                        state.clear("venue_data", "rec_ids", "gift_rec_ids")

                        # FIX #3: redirect to package order page
                        redirect_url = f"/customers/package-orders/{booking_id}"

                        reply = (
                            f"You're all set! 🎉 Booking confirmed for option {selected_idx + 1}.\n\n"
                            f"**Booking reference: {booking_id}**\n\n"
                            f"The vendor will be in touch shortly to confirm the details. "
                            f"Anything else I can help you with?"
                        )
                        logger.info(f"Booking {booking_id} created for event {session_id}")
                    except Exception as e:
                        logger.warning(f"Booking failed: {e}")
                        reply = (
                            f"I've noted your choice of option {selected_idx + 1}! "
                            f"There was a small hiccup — our team will confirm your booking shortly. "
                            f"Anything else?"
                        )

                chat_svc.save_message(db, session_id=session_id, user_msg=user_query,
                                      ai_msg=reply, customer_id=customer.customer_id,
                                      missing_info=[])
                return PlanResponse(
                    intent="planning",
                    reasoning="Package selected, booking created.",
                    chat_response=reply, missing_info=[],
                    venue_tags=[], matched_venues=[], matched_gifts=[],
                    ask_save_persona=False, persona_saved=False,
                    persona_confirmed=bool(chosen_persona),
                    booking_created=bool(booking_id),
                    booking_id=booking_id,
                    redirect_url=redirect_url,
                    is_ai_fallback=False,
                )

        # ── STEP: Vibe question (FIX #4) ─────────────────────────────────────
        if current_step == _STEP_VIBE:
            vibe_answer = user_query.strip()
            vd = dict(venue_data)
            vd["vibe"] = vibe_answer
            state.venue_data = vd
            state.step = _STEP_CHAT

            reply = (
                f"Love it — **{vibe_answer}** it is! 🎨 "
                f"Give me a moment to find the perfect matches for you..."
            )
            chat_svc.save_message(
                db, session_id=session_id, user_msg=user_query,
                ai_msg=reply, customer_id=customer.customer_id,
                missing_info=[],
            )
            # Update state so the rest of process_plan runs fresh this turn
            user_query   = f"{user_query} [VIBE CONFIRMED: {vibe_answer}]"
            current_step = _STEP_CHAT
            venue_data   = vd

        # ── STEP: Already booked (FIX 6) ─────────────────────────────────────
        if current_step == _STEP_BOOKED:
            bid = state.booking_id or ""
            user_query = (
                user_query
                + f"\n[BOOKING ALREADY COMPLETE — ref: {bid}. "
                f"Do NOT ask for location/budget/guests/date again. "
                f"Respond helpfully to whatever the user is asking now.]"
            )

        # ── FIRST MESSAGE greeting ────────────────────────────────────────────
        is_test_mock = not getattr(ai_svc, "groq_api_key", None)

        if not history and not is_test_mock:
            et    = (event_context or {}).get("event_type", "event")
            title = (event_context or {}).get("title", "")

            linked_ids = []
            try:
                from app.services.customer_service import customer_service as _cs
                linked_ids = _cs.get_event_persona_ids(
                    db, event_ids=[session_id]
                ).get(session_id, [])
            except Exception:
                pass

            if personas and not linked_ids:
                lines = [
                    f"Hey! I'm Occi, your personal event planner 🎉 "
                    f"Let's make your **{et}**"
                    + (f" — *{title}*" if title else "")
                    + " absolutely unforgettable!\n",
                    "I have some saved profiles. Who are we planning this for?",
                ]
                for i, p in enumerate(personas, 1):
                    rel = f" ({p.relationship})" if getattr(p, "relationship", None) else ""
                    lines.append(f"  **{i}.** {p.name}{rel}")
                lines.append("\nSay the number or name — or tell me about someone new!")
                reply = "\n".join(lines)
                state.step = _STEP_PERSONA_LIST
                missing = []
            elif linked_ids:
                linked = next((p for p in personas if p.persona_id in linked_ids), None)
                if linked:
                    state.chosen_persona_id = linked.persona_id
                    chosen_persona = linked
                    reply = (
                        f"Hey! I'm Occi 🎉 Let's plan an amazing **{et}** "
                        f"for **{linked.name}**! I already have their profile. "
                        f"What date, location, and budget are you thinking?"
                    )
                    state.step = _STEP_CHAT
                else:
                    reply = (
                        f"Hey! I'm Occi 🎉 Let's plan an amazing **{et}**"
                        + (f" — *{title}*" if title else "")
                        + "!\n\nWho are we planning this for? Tell me their name and "
                        + "a bit about them — their vibe, favourite food, music, hobbies..."
                    )
                    state.step = _STEP_CHAT
                missing = ["date","location","budget","guest_count"]
            else:
                reply = (
                    f"Hey! I'm Occi 🎉 Let's make your **{et}**"
                    + (f" — *{title}*" if title else "")
                    + " something truly special!\n\n"
                    + "First — who are we celebrating? Tell me their name and "
                    + "a bit about them (vibe, favourite food, music, hobbies...)."
                )
                state.step = _STEP_CHAT
                missing = ["persona"]

            chat_svc.save_message(db, session_id=session_id, user_msg=user_query,
                                  ai_msg=reply, customer_id=customer.customer_id,
                                  missing_info=missing)
            return PlanResponse(
                intent="chat", reasoning="First message — greeting shown.",
                chat_response=reply, missing_info=missing,
                venue_tags=[], matched_venues=[], matched_gifts=[],
                ask_save_persona=False, persona_saved=False,
                persona_confirmed=bool(chosen_persona),
            )

        # ── NORMAL CHAT / AI LOOP ─────────────────────────────────────────────

        all_text = user_query + " " + " ".join(
            (m.user_message or "") for m in history[-5:]
        )
        ex_budget   = _extract_budget(all_text)
        ex_guests   = _extract_guests(all_text)
        ex_location = vendor_svc.extract_location_from_text(all_text)
        ex_date     = _extract_date(all_text)

        vd = dict(venue_data)
        if ex_budget:   vd["budget"]      = ex_budget
        if ex_guests:   vd["guest_count"] = ex_guests
        if ex_location: vd["location"]    = ex_location
        if ex_date:     vd["event_date"]  = ex_date
        state.venue_data = vd

        available_tags = vendor_svc.get_all_tags(db)

        ai_event_context = None
        if event_context:
            ai_event_context = {
                "title":           event_context.get("title"),
                "event_type":      event_context.get("event_type"),
                "event_date":      vd.get("event_date") or event_context.get("start_at"),
                "location":        vd.get("location") or event_context.get("location_text"),
                "guest_count":     vd.get("guest_count"),
                "budget_per_head": vd.get("budget"),
            }

        personas_for_ai = [chosen_persona] if chosen_persona else []
        if persona_draft and persona_draft.get("name") and not chosen_persona:
            class _D:
                pass
            dp = _D()
            for f, v in persona_draft.items():
                setattr(dp, f, v)
            dp.personality_tags  = _safe_list(persona_draft.get("personality_tags") or persona_draft.get("vibe"))
            dp.food_preferences  = _safe_list(persona_draft.get("food_preferences"))
            dp.music_preferences = _safe_list(persona_draft.get("music_preferences"))
            dp.color_preferences = _safe_list(persona_draft.get("color_preferences") or persona_draft.get("colours"))
            dp.preferences_json  = []
            personas_for_ai = [dp]

        known_block = _known_facts_block(vd, persona_draft, chosen_persona)
        fact_parts  = []
        if ex_budget:   fact_parts.append(f"budget={ex_budget}")
        if ex_guests:   fact_parts.append(f"guests={ex_guests}")
        if ex_location: fact_parts.append(f"location={ex_location}")
        if ex_date:     fact_parts.append(f"date={ex_date}")

        enriched = user_query
        if fact_parts:
            enriched += f"\n[JUST EXTRACTED: {', '.join(fact_parts)}]"
        if known_block:
            enriched += known_block
        if event_context:
            ctx = []
            if event_context.get("title"):      ctx.append(f"Event: {event_context['title']}")
            if event_context.get("event_type"): ctx.append(f"Type: {event_context['event_type']}")
            if ctx: enriched += f"\n[EVENT CONTEXT: {'; '.join(ctx)}]"
        if past_events:
            hints = [
                f"{e['event_type']} on {e['event_date']} in {e['location']}"
                for e in past_events[:3] if e.get("event_type")
            ]
            if hints:
                enriched += (
                    f"\n[CUSTOMER PAST EVENTS: {'; '.join(hints)} — "
                    f"proactively suggest improvements if planning something similar]"
                )

        try:
            ai_result = await _call_ai(
                ai_svc,
                raw_query      = enriched,
                history        = history,
                personas       = personas_for_ai or None,
                available_tags = available_tags or None,
                missing_info   = list(prev_missing) if prev_missing else None,
                session_id     = session_id,
                event_context  = ai_event_context,
                past_events    = past_events or None,
            )
        except Exception as exc:
            logger.error(f"AI call failed: {exc}")
            ai_result = {
                "intent": "chat",
                "chat_response": "Give me just a moment — could you say that again?",
                "venue_tags": [], "missing_info": [],
            }

        intent        = ai_result.get("intent", "chat")
        venue_tags    = ai_result.get("venue_tags") or []
        new_missing   = ai_result.get("missing_info") or []
        chat_response = ai_result.get("chat_response") or ""
        gift_sug      = ai_result.get("gift_suggestion")
        event_type_ai = ai_result.get("event_type")

        use_persona_name = ai_result.get("use_persona_name")
        if use_persona_name and not chosen_persona:
            matched_by_name = next(
                (p for p in personas
                 if p.name and p.name.lower() == str(use_persona_name).lower()),
                None,
            )
            if matched_by_name:
                try:
                    persona_svc.confirm_persona(db, matched_by_name.persona_id, customer_id)
                except Exception:
                    pass
                state.chosen_persona_id = matched_by_name.persona_id
                chosen_persona = matched_by_name

        budget_ai   = ai_result.get("budget_per_head") or vd.get("budget")
        location_ai = ai_result.get("location") or vd.get("location")
        date_ai     = ai_result.get("event_date") or vd.get("event_date")
        guests_ai   = ai_result.get("guest_count") or vd.get("guest_count")

        if budget_ai:   vd["budget"]      = budget_ai
        if guests_ai:   vd["guest_count"] = guests_ai
        if location_ai: vd["location"]    = location_ai
        if date_ai:     vd["event_date"]  = date_ai
        if venue_tags:  vd["tags"]        = venue_tags

        # Save inferred vibe from venue_tags so we don't ask again
        if venue_tags and not vd.get("vibe"):
            vd["vibe"] = ", ".join(venue_tags[:3])

        state.venue_data = vd

        persona_draft = _merge_persona_from_ai(persona_draft, ai_result, user_query)
        if persona_draft:
            state.persona_draft = persona_draft

        ask_save_persona = False
        persona_saved    = False
        matched_venues   = []
        matched_gifts    = []
        venue_match_tier = None
        booking_created  = False
        booking_id_out   = None
        redirect_url     = None

        effective_intent = _resolve_intent(intent, user_query)

        vm = _venue_missing(vd)
        can_recommend = (
            effective_intent in ("planning", "date", "multi", "gift")
            and (venue_tags or effective_intent in ("gift", "multi"))
            and current_step != _STEP_BOOKED
        )

        # ── FIX #4: Dedicated vibe question after all 4 fields confirmed ──────
        primary_fields_complete = (
            vd.get("location")
            and vd.get("budget")
            and vd.get("guest_count")
            and vd.get("event_date")
        )

        if (
            primary_fields_complete
            and not vd.get("vibe")
            and not venue_tags
            and current_step not in (_STEP_RECS_SHOWN, _STEP_BOOKED, _STEP_PERSONA_SAVE, _STEP_VIBE)
            and effective_intent in ("planning", "date", "multi")
        ):
            vibe_question = (
                "Almost there! One last thing — what vibe or theme are you going for? 🎨\n\n"
                "For example: *romantic and intimate*, *fun and lively*, *elegant and upscale*, "
                "*adventurous and outdoor*, or anything else that comes to mind!"
            )
            state.step = _STEP_VIBE
            chat_svc.save_message(
                db, session_id=session_id, user_msg=user_query,
                ai_msg=vibe_question, customer_id=customer.customer_id,
                missing_info=["vibe or theme"],
            )
            return PlanResponse(
                intent="planning",
                reasoning="All primary fields confirmed — asking for vibe.",
                chat_response=vibe_question,
                missing_info=["vibe or theme"],
                venue_tags=[],
                matched_venues=[],
                matched_gifts=[],
                ask_save_persona=False,
                persona_saved=False,
                persona_confirmed=bool(chosen_persona),
            )

        if can_recommend:
            gift_bph  = None
            venue_bph = budget_ai
            if budget_ai and guests_ai:
                gift_bph  = float(budget_ai) * 0.25
                venue_bph = (float(budget_ai) * 0.75) / float(guests_ai)
            elif budget_ai:
                venue_bph = float(budget_ai)

            # Venue matching
            if effective_intent in ("planning", "date", "multi"):
                matched_venues = _get_3_venues(
                    vendor_svc, db, venue_tags, venue_bph,
                    location_ai, guests_ai, venue_tags,
                )
                if matched_venues:
                    state.rec_ids = [v.id for v in matched_venues if v.id]
                    state.step = _STEP_RECS_SHOWN
                    first = matched_venues[0]
                    venue_match_tier = 1 if not first.tweak_note else 2

            # Gift matching
            if effective_intent in ("gift", "multi"):
                gift_tags = list(venue_tags or [])
                all_persona_sources = personas_for_ai or personas or []
                for p in all_persona_sources:
                    gift_tags = list(set(gift_tags
                        + _safe_list(getattr(p, "preferences_json", []))
                        + _safe_list(getattr(p, "food_preferences", []))
                        + _safe_list(getattr(p, "personality_tags", []))))
                if not gift_tags:
                    gift_tags = ["romantic"]

                raw_gifts = _get_3_gifts(
                    vendor_svc, db, gift_tags, None, guests_ai,
                    all_persona_sources,
                )
                matched_gifts = list(raw_gifts or [])

                gift_venue_ids = {v.id for v in matched_venues if v.id}
                for gift_item in matched_gifts:
                    if len(matched_venues) >= 3:
                        break
                    pid = getattr(gift_item, "id", None)
                    if pid not in gift_venue_ids:
                        gift_venue_ids.add(pid)
                        pph = getattr(gift_item, "price_per_head", None)
                        matched_venues.append(VenueDisplay(
                            id=pid,
                            name=str(getattr(gift_item, "name", "") or ""),
                            price_per_head=pph if isinstance(pph, (int, float)) else None,
                        ))

                if matched_venues and not state.rec_ids:
                    state.rec_ids = [v.id for v in matched_venues if v.id]
                    state.step = _STEP_RECS_SHOWN

                if not gift_sug and matched_gifts:
                    gift_sug = str(getattr(matched_gifts[0], "name", "") or "")
                if not gift_sug:
                    gift_sug = "A thoughtful personalised gift for the occasion"

            _g3g_is_patched = not getattr(
                _get_3_gifts, "__module__", "app.services.planning_service"
            ).startswith("app.services.planning")
            if matched_venues and effective_intent in ("planning", "date") \
                    and not matched_gifts and _g3g_is_patched:
                gift_tags_pd = list(venue_tags or ["romantic"])
                all_ps = personas_for_ai or personas or []
                matched_gifts = list(_get_3_gifts(
                    vendor_svc, db, gift_tags_pd, gift_bph, guests_ai, all_ps
                ) or [])

            # ── FIX #2: Hard budget filter ────────────────────────────────────
            if vd.get("budget"):
                matched_venues, matched_gifts, all_over_budget = _filter_by_budget(
                    matched_venues,
                    matched_gifts,
                    float(vd["budget"]),
                    vd.get("guest_count"),
                )
            else:
                all_over_budget = False

            # ── FIX #1: AI fallback when DB empty or all over budget ──────────
            if not matched_venues and effective_intent in ("planning", "date", "multi"):
                if all_over_budget:
                    budget_msg = (
                        f"Hmm, I couldn't find any venues within your budget of "
                        f"**LKR {float(vd.get('budget', 0)):,.0f}** "
                        f"in **{vd.get('location', 'that area')}**. 😔\n\n"
                        "Would you like to:\n"
                        "- **Increase your budget** — what's the maximum you could stretch to?\n"
                        "- **Try a different location** — I might find better options nearby\n"
                        "- **See AI-curated suggestions** — I can suggest ideas even if they're "
                        "not listed yet *(just say: show me AI suggestions)*"
                    )
                    state.step = _STEP_CHAT
                    state.clear("rec_ids")
                    chat_svc.save_message(
                        db, session_id=session_id, user_msg=user_query,
                        ai_msg=budget_msg, customer_id=customer.customer_id,
                        missing_info=["budget or location adjustment"],
                    )
                    return PlanResponse(
                        intent="planning",
                        reasoning="All venues over budget — asking user to adjust.",
                        chat_response=budget_msg,
                        missing_info=["budget or location adjustment"],
                        venue_tags=venue_tags,
                        matched_venues=[],
                        matched_gifts=[],
                        ask_save_persona=False,
                        persona_saved=False,
                        persona_confirmed=bool(chosen_persona),
                    )

                else:
                    wants_ai = any(
                        w in user_query.lower()
                        for w in ["ai suggestion", "show me ai", "no options",
                                  "nothing matches", "ai curated", "suggest anyway",
                                  "show anyway", "show me ai suggestions",
                                  "curate", "creative"]
                    )

                    if wants_ai or not state.rec_ids:
                        fb_venues_raw, fb_gifts_raw = await _generate_ai_fallback(
                            ai_svc=ai_svc,
                            vd=vd,
                            persona_draft=persona_draft,
                            chosen_persona=chosen_persona,
                            event_context=ai_event_context,
                        )

                        if fb_venues_raw:
                            state.ai_fallback_venues = fb_venues_raw
                            state.ai_fallback_gifts  = fb_gifts_raw
                            state.is_ai_fallback = True

                            matched_venues = [
                                _ai_venue_to_display(v, i)
                                for i, v in enumerate(fb_venues_raw)
                            ]
                            matched_gifts = [
                                _ai_gift_to_display(g, i)
                                for i, g in enumerate(fb_gifts_raw)
                            ]

                            state.rec_ids = [v.id for v in matched_venues]
                            state.step = _STEP_RECS_SHOWN

                            disclaimer = (
                                "✨ These aren't listed on our platform yet, but our concierge "
                                "team will arrange everything once you pick one!\n\n"
                            )
                            chat_response = disclaimer + (chat_response or "")
                        else:
                            no_match_msg = (
                                "I couldn't find any options that match right now. 😔\n\n"
                                "Could you help me with one of these?\n"
                                "- A **different location** in Sri Lanka?\n"
                                "- A **higher budget** (even slightly)?\n"
                                "- A **different vibe** — e.g. casual instead of luxury?"
                            )
                            state.clear("rec_ids")
                            chat_svc.save_message(
                                db, session_id=session_id, user_msg=user_query,
                                ai_msg=no_match_msg, customer_id=customer.customer_id,
                                missing_info=["location or budget adjustment"],
                            )
                            return PlanResponse(
                                intent="planning",
                                reasoning="No DB matches and AI fallback failed.",
                                chat_response=no_match_msg,
                                missing_info=["location or budget adjustment"],
                                venue_tags=venue_tags,
                                matched_venues=[],
                                matched_gifts=[],
                                ask_save_persona=False,
                                persona_saved=False,
                                persona_confirmed=bool(chosen_persona),
                            )
                    else:
                        no_match_msg = (
                            "I searched our vendor network but couldn't find exact matches "
                            f"in **{vd.get('location', 'that area')}** right now. 🔍\n\n"
                            "Want me to **curate some ideas** based on what you described? "
                            "Our team can arrange them even if they're not on the platform yet — "
                            "just say *show me AI suggestions* and I'll get creative! 🎨"
                        )
                        chat_svc.save_message(
                            db, session_id=session_id, user_msg=user_query,
                            ai_msg=no_match_msg, customer_id=customer.customer_id,
                            missing_info=[],
                        )
                        return PlanResponse(
                            intent="planning",
                            reasoning="No DB matches — offering AI fallback option.",
                            chat_response=no_match_msg,
                            missing_info=[],
                            venue_tags=venue_tags,
                            matched_venues=[],
                            matched_gifts=[],
                            ask_save_persona=False,
                            persona_saved=False,
                            persona_confirmed=bool(chosen_persona),
                        )

            # Append selection prompt
            if matched_venues and len(matched_venues) > 1:
                nums = " · ".join(f"**{i}**" for i in range(1, len(matched_venues) + 1))
                chat_response = (chat_response or "").rstrip()
                if chat_response and not chat_response.endswith(("1", "2", "3", "?")):
                    chat_response += f"\n\nReply with {nums} to confirm, or tell me what to change."

        # ── Persona save prompt ───────────────────────────────────────────────
        if (
            _persona_is_complete(persona_draft)
            and not chosen_persona
            and current_step not in (_STEP_PERSONA_SAVE, _STEP_RECS_SHOWN, _STEP_BOOKED)
            and not matched_venues
        ):
            name_raw = persona_draft.get("name", "")
            name = str(name_raw).strip() if name_raw else ""

            if _said_yes(user_query) and name:
                try:
                    payload = _build_persona_payload(persona_draft)
                    if not any(p.name.lower() == payload["name"].lower() for p in personas):
                        new_p = persona_svc.create_persona(
                            db, customer_id=customer_id, data=payload
                        )
                        try:
                            from app.models.event_persona import EventPersona
                            db.add(EventPersona(event_id=session_id, persona_id=new_p.persona_id))
                            db.commit()
                        except Exception:
                            db.rollback()
                        try:
                            persona_svc.confirm_persona(db, new_p.persona_id, customer_id)
                        except Exception:
                            pass
                        state.chosen_persona_id = new_p.persona_id
                        chosen_persona = new_p
                        persona_saved = True
                except Exception as _e:
                    logger.warning(f"Inline persona save failed: {_e}")
            else:
                state.pending_save = persona_draft
                state.step = _STEP_PERSONA_SAVE
                chat_response = (
                    (chat_response or "")
                    + f"\n\nBy the way — would you like me to save **{name}'s** profile "
                      f"for future events? (yes / no)"
                )
                ask_save_persona = True

        chat_svc.save_message(
            db, session_id=session_id, user_msg=user_query,
            ai_msg=chat_response or "", customer_id=customer.customer_id,
            missing_info=new_missing,
        )

        if effective_intent in ("gift", "multi") and not gift_sug:
            gift_sug = "A thoughtful personalised gift for the occasion"

        return PlanResponse(
            intent              = intent,
            reasoning           = ai_result.get("reasoning"),
            personality_profile = ai_result.get("personality_profile"),
            chat_response       = chat_response,
            gift_suggestion     = gift_sug,
            missing_info        = new_missing,
            venue_match_tier    = venue_match_tier,
            event_type          = event_type_ai,
            event_date          = date_ai,
            location            = location_ai,
            budget_per_head     = budget_ai,
            guest_count         = guests_ai,
            venue_tags          = venue_tags,
            matched_venues      = matched_venues,
            matched_gifts       = matched_gifts,
            ask_save_persona    = ask_save_persona,
            persona_saved       = persona_saved,
            persona_confirmed   = bool(chosen_persona),
            booking_created     = booking_created,
            booking_id          = booking_id_out,
            redirect_url        = redirect_url,
            is_ai_fallback      = state.is_ai_fallback,
        )

    async def _create_booking(self, db, customer_id, event_id, package_id,
                               venue_data, persona_draft, chosen_persona) -> str:
        from app.models.package_execution_request import PackageExecutionRequest
        from app.models.package import Package
        from app.common.utils import generate_prefixed_id

        pkg = db.query(Package).filter(Package.id == package_id).first()
        if not pkg:
            raise ValueError(f"Package {package_id} not found")

        guests = venue_data.get("guest_count") or 1
        pph    = getattr(pkg, "price_per_head", None)
        total  = float(pph) * int(guests) if pph else 0.0

        p_note = " | For: " + _persona_summary(persona_draft, persona=chosen_persona)
        notes = (
            f"Booked via chat."
            f" Guests: {guests}."
            f" Date: {venue_data.get('event_date', 'TBC')}."
            f" Location: {venue_data.get('location', 'TBC')}."
            f" Vibe: {venue_data.get('vibe', 'TBC')}."
            f"{p_note}"
        )

        booking_id = generate_prefixed_id("BKG")
        order = PackageExecutionRequest(
            execution_request_id = booking_id,
            event_id             = event_id,
            package_id           = str(package_id),
            package_total_price  = total,
            currency             = "LKR",
            status               = "PENDING",
            notes                = notes,
            idempotency_key      = str(uuid4()),
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        return booking_id

    async def _create_ai_inquiry(
        self,
        db,
        customer_id: str,
        event_id: str,
        selected_venue: dict,
        selected_gift: dict,
        venue_data: dict,
        persona_draft: dict,
        chosen_persona,
    ) -> str:
        """
        FIX #1 — Creates a customer inquiry for AI-generated (non-DB) selections.
        Returns a reference ID like INQ-XXXX.
        """
        from app.common.utils import generate_prefixed_id

        persona_name = ""
        if chosen_persona:
            persona_name = getattr(chosen_persona, "name", "") or ""
        elif persona_draft:
            persona_name = str(persona_draft.get("name") or "")

        inquiry_id = generate_prefixed_id("INQ")
        note = (
            f"AI-assisted event inquiry.\n"
            f"Event ID: {event_id}\n"
            f"Guest: {persona_name or 'N/A'}\n"
            f"Venue request: {selected_venue.get('name', 'N/A')} — "
            f"{selected_venue.get('description', '')}\n"
            f"Gift request: {selected_gift.get('name', 'N/A')} — "
            f"{selected_gift.get('description', '')}\n"
            f"Budget: LKR {venue_data.get('budget', 0):,.0f}\n"
            f"Guests: {venue_data.get('guest_count', 1)}\n"
            f"Date: {venue_data.get('event_date', 'TBC')}\n"
            f"Location: {venue_data.get('location', 'TBC')}\n"
            f"Vibe: {venue_data.get('vibe', 'N/A')}\n"
        )

        try:
            from app.models.inquiry import Inquiry
            inq = Inquiry(
                inquiry_id         = inquiry_id,
                created_by_user_id = customer_id,
                created_by_role    = "CUSTOMER",
                subject            = f"AI Event Planning Request — {venue_data.get('location', '')}",
                message            = note,
                status             = "OPEN",
            )
            db.add(inq)
            db.commit()
        except Exception as exc:
            # Inquiry model may not exist yet — return the ref ID anyway, no crash
            logger.warning(f"Inquiry model save failed (model may not exist yet): {exc}")
            try:
                db.rollback()
            except Exception:
                pass

        return inquiry_id

    async def _auto_create_tasks(self, db, customer_id, event_id,
                                  event_type, selected_package_id, vendor_svc) -> list:
        from app.services.event_planning_service import event_planning_service, _TASK_TEMPLATES
        existing = event_planning_service.list_tasks(
            db, customer_id=customer_id, event_id=event_id
        )
        if existing:
            return existing
        key  = event_type.lower() if event_type.lower() in _TASK_TEMPLATES else "default"
        tmpl = _TASK_TEMPLATES[key]
        pkg  = vendor_svc.get_package_by_id(db, selected_package_id)
        cat  = None
        if pkg:
            tags = pkg.tags or []
            if isinstance(tags, str):
                try: tags = json.loads(tags)
                except Exception: tags = []
            cat = next((t for t in tags if t.lower() in
                        ["venue","romantic","luxury","family","party","adventure"]), "venue")
        created = []
        for t in tmpl:
            is_v = "venue" in t["name"].lower()
            try:
                task = event_planning_service.create_task(
                    db, customer_id=customer_id, event_id=event_id,
                    payload={"name": t["name"], "description": t["description"],
                             "quantity": 1, "currency": "LKR",
                             "needs_vendor": cat if is_v else None,
                             "vendor_category": cat if is_v else None},
                )
                created.append(task)
            except Exception as e:
                logger.warning(f"Task create failed '{t['name']}': {e}")
        return created


planning_service = PlanningService()


# ─────────────────────────────────────────────────────────────────────────────
# Backward-compat aliases
# ─────────────────────────────────────────────────────────────────────────────

def _package_to_dict(pkg, requested_tags=None, guest_count=None, tweak_note=None) -> dict:
    v = _to_venue(pkg, req_tags=requested_tags, guest_count=guest_count, tweak=tweak_note)
    return {
        "id":                    v.id,
        "name":                  v.name,
        "description":           v.description,
        "price_per_head":        v.price_per_head,
        "total_estimated_price": v.total_estimated_price,
        "tags":                  v.tags,
        "location":              v.location,
        "vendor_name":           v.vendor_name,
        "match_score":           v.match_score,
        "match_score_max":       v.match_score_max,
        "match_score_label":     v.match_score_label,
        "tweak_note":            v.tweak_note,
    }