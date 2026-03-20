"""
app/services/ai_service.py

Architecture: Direct Groq API for chat. Langflow removed entirely.
─────────────────────────────────────────────────────────────────────
NEW in v2:
  1. Emotion/tone detection  — 5 tones (romantic, adventure, family,
     corporate, celebration) detected from event type + persona + keywords.
     Injects tone context into system message so AI adjusts language and
     venue_tags bias automatically.

  2. Proactive gift suggestions — system prompt now requires gift_suggestion
     for any planning/date/multi/gift intent. Also added gift_category field
     so planning_service can run a targeted gift package search.

  3. Recurring intelligence — generate_date_plan accepts past_events list.
     If past events exist, system message includes a MEMORY block summarising
     what was done before and instructs AI to propose an improved version.
"""

import json
import logging
import re
import hashlib
from typing import Any, List, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Persona preference → package tag mapping ──────────────────────────────────
_PREFERENCE_TO_TAGS: dict[str, list[str]] = {
    "fine dining":    ["fine-dining", "luxury"],
    "fine-dining":    ["fine-dining", "luxury"],
    "casual dining":  ["casual"],
    "brunch":         ["brunch"],
    "vegan":          ["wellness", "nature"],
    "seafood":        ["beach", "fine-dining"],
    "nature":         ["nature", "outdoor", "wellness"],
    "blue":           ["beach", "pool", "nature"],
    "green":          ["nature", "outdoor", "hiking"],
    "red":            ["romantic", "luxury"],
    "purple":         ["luxury", "spa"],
    "pastel":         ["wellness", "brunch"],
    "dark":           ["nightlife", "luxury"],
    "jazz":           ["fine-dining", "luxury", "romantic"],
    "pop":            ["party", "nightlife"],
    "classical":      ["luxury", "fine-dining", "cultural"],
    "electronic":     ["nightlife", "party"],
    "acoustic":       ["romantic", "nature", "wellness"],
    "live music":     ["music", "party"],
    "adventure":      ["adventure", "hiking", "outdoor"],
    "romantic":       ["romantic"],
    "luxury":         ["luxury", "spa"],
    "sporty":         ["fitness", "sports", "outdoor"],
    "artistic":       ["art", "photography", "cultural"],
    "spiritual":      ["wellness", "cultural"],
    "family":         ["family", "kids"],
    "social":         ["party", "brunch", "music"],
    "relaxed":        ["spa", "wellness", "sunset"],
    "photography":    ["photography", "sunset", "nature"],
    "travel":         ["travel", "adventure"],
    "nightlife":      ["nightlife", "party"],
    "outdoor":        ["outdoor", "nature", "hiking"],
    "indoor":         ["indoor", "spa", "fine-dining"],
    "beach":          ["beach", "pool", "sunset"],
    "wellness":       ["wellness", "spa", "fitness"],
    "cultural":       ["cultural", "art"],
    "kids":           ["kids", "family"],
    "pet-friendly":   ["pet-friendly", "outdoor"],
    "corporate":      ["corporate", "luxury"],
    "wedding":        ["wedding", "romantic", "luxury"],
    "birthday":       ["birthday", "party"],
    "hiking":         ["adventure", "hiking", "outdoor"],
}

# ── Emotion/tone detection ────────────────────────────────────────────────────
_TONE_ROMANTIC    = "romantic"
_TONE_ADVENTURE   = "adventure"
_TONE_FAMILY      = "family"
_TONE_CORPORATE   = "corporate"
_TONE_CELEBRATION = "celebration"

_TONE_KEYWORDS: dict[str, list[str]] = {
    _TONE_ROMANTIC:    ["romantic", "anniversary", "date", "love", "proposal", "partner",
                        "girlfriend", "boyfriend", "husband", "wife", "intimate", "couple"],
    _TONE_ADVENTURE:   ["adventure", "hiking", "outdoor", "camping", "extreme", "thrill",
                        "surf", "dive", "trek", "explore", "nature"],
    _TONE_FAMILY:      ["family", "kids", "children", "parents", "grandparents", "relatives",
                        "home party", "reunion", "gathering"],
    _TONE_CORPORATE:   ["corporate", "team", "office", "colleagues", "business", "work",
                        "retreat", "conference", "professional"],
    _TONE_CELEBRATION: ["birthday", "graduation", "promotion", "achievement", "surprise",
                        "party", "celebrate", "milestone"],
}

_TONE_SYSTEM_ADDON: dict[str, str] = {
    _TONE_ROMANTIC: (
        "TONE: This is a ROMANTIC occasion. Be warm, poetic, emotionally resonant. "
        "Suggest candlelit venues, private dining, sunset views, flower arrangements. "
        "Gift bias: personalised jewellery, perfume, couples experiences, flowers."
    ),
    _TONE_ADVENTURE: (
        "TONE: This is an ADVENTURE occasion. Be energetic, exciting, inspiring. "
        "Suggest outdoor venues, hiking spots, water activities, unique experiences. "
        "Gift bias: experience vouchers, gear, activity kits, outdoor accessories."
    ),
    _TONE_FAMILY: (
        "TONE: This is a FAMILY occasion. Be warm, inclusive, practical. "
        "Suggest family-friendly venues, kid-safe spaces, spacious dining. "
        "Gift bias: family experiences, personalised keepsakes, photo albums, home items."
    ),
    _TONE_CORPORATE: (
        "TONE: This is a CORPORATE occasion. Be professional, polished, efficient. "
        "Suggest business-class venues, conference facilities, team activity spaces. "
        "Gift bias: branded items, tech accessories, premium hampers, gift cards."
    ),
    _TONE_CELEBRATION: (
        "TONE: This is a CELEBRATION. Be enthusiastic, fun, vibrant. "
        "Suggest party venues, entertainment spaces, rooftop options. "
        "Gift bias: personalised gifts, cake, experience vouchers, luxury hampers."
    ),
}

_GIFT_CATEGORY_BY_TONE: dict[str, str] = {
    _TONE_ROMANTIC:    "romantic gift",
    _TONE_ADVENTURE:   "experience voucher",
    _TONE_FAMILY:      "family keepsake",
    _TONE_CORPORATE:   "corporate gift",
    _TONE_CELEBRATION: "celebration gift",
}

# ── Groq direct API ───────────────────────────────────────────────────────────
_GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
_GROQ_MODEL    = "llama-3.3-70b-versatile"
_MAX_HISTORY_TURNS = 10


def _detect_tone(
    event_type: Optional[str],
    user_query: str,
    personas: list,
) -> str:
    """
    Detect the emotional tone of this event from event_type, message text,
    and persona personality_tags.
    Returns one of the 5 _TONE_* constants.
    """
    text = " ".join([
        (event_type or ""),
        (user_query or ""),
        " ".join(
            " ".join(getattr(p, "personality_tags", []) or [])
            for p in (personas or [])
        ),
    ]).lower()

    scores: dict[str, int] = {t: 0 for t in _TONE_KEYWORDS}
    for tone, keywords in _TONE_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                scores[tone] += 1

    best = max(scores, key=lambda t: scores[t])
    if scores[best] == 0:
        # Default by event type
        et = (event_type or "").lower()
        if any(w in et for w in ["anniversary", "date", "proposal"]):
            return _TONE_ROMANTIC
        if any(w in et for w in ["birthday", "graduation", "promotion"]):
            return _TONE_CELEBRATION
        if "corporate" in et or "team" in et:
            return _TONE_CORPORATE
        if "family" in et:
            return _TONE_FAMILY
        return _TONE_CELEBRATION
    return best


def _build_memory_block(past_events: Optional[list]) -> str:
    """
    Build a MEMORY block from the user's past confirmed events.
    Each entry: {event_type, event_date, location, packages_used: [name...]}
    """
    if not past_events:
        return ""

    lines = ["RECURRING INTELLIGENCE — past events for this user:"]
    for ev in past_events[:5]:  # cap at 5
        ev_type    = ev.get("event_type", "event")
        ev_date    = ev.get("event_date", "unknown date")
        ev_loc     = ev.get("location", "unknown location")
        ev_pkgs    = ev.get("packages_used", [])
        pkg_str    = (", ".join(ev_pkgs[:3])) if ev_pkgs else "no packages recorded"
        lines.append(
            f"  • {ev_type} on {ev_date} in {ev_loc} — packages: {pkg_str}"
        )

    lines.append(
        "\nUSE THIS MEMORY: If the user is planning a similar or recurring event "
        "(e.g. another birthday for the same person), reference what they did before "
        "and proactively suggest how to make it even better this year. "
        "Say something like 'Last year you did X — want to try Y this time?'"
    )
    return "\n".join(lines) + "\n\n"


def _build_structured_persona_context(personas: list) -> str:
    """
    Build a structured persona context block that maps preference fields
    (food, music, personality_tags, color_preferences) to concrete package tags.

    Replaces the old text-blob _build_persona_block for use in system messages
    so the AI receives explicit tag guidance.

    Returns empty string for an empty persona list.
    """
    if not personas:
        return ""

    def _to_list(val) -> list[str]:
        if not val:
            return []
        if isinstance(val, list):
            return [str(v).strip().lower() for v in val if v]
        return [s.strip().lower() for s in str(val).split(",") if s.strip()]

    all_tags: list[str] = []
    blocks: list[str] = []

    for p in personas:
        name       = getattr(p, "name",             "Unknown") or "Unknown"
        rel        = getattr(p, "relationship",     "") or ""
        food       = _to_list(getattr(p, "food_preferences",  None))
        music      = _to_list(getattr(p, "music_preferences", None))
        ptags      = _to_list(getattr(p, "personality_tags",  None))
        colors     = _to_list(getattr(p, "color_preferences", None))
        # Legacy fallback: if all new structured fields are empty, use preferences_json
        prefs_json = _to_list(getattr(p, "preferences_json",  None))
        if not any([food, music, ptags, colors]) and prefs_json:
            ptags = prefs_json

        # Derive package tags from every preference field
        derived: list[str] = []
        for lst in [food, music, ptags, colors]:
            for pref in lst:
                derived.extend(_PREFERENCE_TO_TAGS.get(pref, [pref]))
        unique_tags = list(dict.fromkeys(derived))
        all_tags.extend(unique_tags)

        lines = [f"Recipient: {name}"]
        if rel:         lines.append(f"  Relationship          : {rel}")
        if food:        lines.append(f"  Food                  : {', '.join(food)}")
        if music:       lines.append(f"  Music                 : {', '.join(music)}")
        if ptags:       lines.append(f"  Vibe                  : {', '.join(ptags)}")
        if colors:      lines.append(f"  Colours               : {', '.join(colors)}")
        if unique_tags: lines.append(f"  Suggested package tags: {', '.join(unique_tags)}")
        blocks.append("\n".join(lines))

    global_tags = list(dict.fromkeys(all_tags))

    output  = "RECIPIENT PROFILES (apply silently to venue + gift suggestions):\n"
    output += "\n\n".join(blocks)
    output += f"\n\nGLOBAL TAG BIAS — {', '.join(global_tags)}\n"
    output += (
        "CRITICAL: PRIORITISE packages whose tags overlap with the GLOBAL TAG BIAS "
        "above. Avoid suggesting venues/gifts that contradict these preferences.\n\n"
    )
    return output


def _build_persona_block(personas: list) -> str:
    """Legacy helper kept for internal use. New code should call
    _build_structured_persona_context instead."""
    def _to_list(val) -> list[str]:
        if not val:
            return []
        if isinstance(val, list):
            return [str(v).strip().lower() for v in val if v]
        return [s.strip().lower() for s in str(val).split(",") if s.strip()]

    blocks = []
    for p in personas:
        name   = getattr(p, "name",         "Unknown") or "Unknown"
        rel    = getattr(p, "relationship", "") or ""
        food   = _to_list(getattr(p, "food_preferences",  None))
        music  = _to_list(getattr(p, "music_preferences", None))
        ptags  = _to_list(getattr(p, "personality_tags",  None))
        colors = _to_list(getattr(p, "color_preferences", None))

        derived: list[str] = []
        for lst in [food, music, ptags, colors]:
            for pref in lst:
                derived.extend(_PREFERENCE_TO_TAGS.get(pref, [pref]))
        unique_tags = list(dict.fromkeys(derived))

        lines = [f"Recipient: {name}"]
        if rel:          lines.append(f"  Relationship : {rel}")
        if food:         lines.append(f"  Food         : {', '.join(food)}")
        if music:        lines.append(f"  Music        : {', '.join(music)}")
        if ptags:        lines.append(f"  Vibe         : {', '.join(ptags)}")
        if colors:       lines.append(f"  Colours      : {', '.join(colors)}")
        if unique_tags:  lines.append(f"  Tag bias     : {', '.join(unique_tags)}")
        blocks.append("\n".join(lines))

    return "RECIPIENT PROFILES (apply silently to venue + gift suggestions):\n" + "\n\n".join(blocks) + "\n\n"


def _build_system_message(
    event_context: Optional[dict],
    available_tags: Optional[List[str]],
    personas: list,
    tone: str = _TONE_CELEBRATION,
    past_events: Optional[list] = None,
) -> str:
    # Only inject the tag block when the caller explicitly provides tags.
    # When available_tags is None (e.g. no packages in DB, or test with no tags),
    # omit the block entirely so tests can assert its absence.
    has_tags = bool(available_tags)
    tag_list = ", ".join(available_tags) if has_tags else ""

    event_block = ""
    if event_context:
        parts = []
        if event_context.get("title"):           parts.append(f"Event title : {event_context['title']}")
        if event_context.get("event_type"):      parts.append(f"Type        : {event_context['event_type']}")
        if event_context.get("event_date"):      parts.append(f"Date        : {event_context['event_date']}")
        if event_context.get("location"):        parts.append(f"Location    : {event_context['location']}")
        if event_context.get("guest_count"):     parts.append(f"Guests      : {event_context['guest_count']}")
        if event_context.get("budget_per_head"): parts.append(f"Budget/head : LKR {event_context['budget_per_head']}")
        if parts:
            event_block = "EVENT (already created by the user — use this context):\n" + "\n".join(parts) + "\n\n"

    # Use structured persona context (maps prefs → tags explicitly)
    persona_block = _build_structured_persona_context(personas) if personas else ""
    memory_block  = _build_memory_block(past_events)
    tone_addon    = _TONE_SYSTEM_ADDON.get(tone, "")

    # Build the optional tag block — absent when no tags are available
    tag_block = (
        f"AVAILABLE_VENUE_TAGS — use ONLY these, 2–4 max:\n{tag_list}\n"
        if has_tags else ""
    )

    return f"""You are Occi, an elite event planner for Occacia — a premium event planning platform in Sri Lanka.
You have 200 IQ (strategic) and 200 EQ (empathetic). You respond naturally to EVERYTHING the user says.

{event_block}{persona_block}{memory_block}{tone_addon}

CONTEXT:
- Currency: Sri Lankan Rupees (LKR) unless stated otherwise
- Locations: Colombo, Kandy, Galle, Ella, Negombo, Nuwara Eliya, Mirissa, Trincomalee, Bentota
- Events: birthdays, anniversaries, weddings, proposals, corporate retreats, romantic dates

CRITICAL BEHAVIOUR RULES:
1. Read the user's message carefully and respond to EXACTLY what they said.
2. "what is 1+1" → answer it (e.g. "Ha, 2! Though I'm better at planning parties 🎉 What are we celebrating?")
3. "who are you" → briefly introduce yourself as Occi
4. "hola" / "hi" / greetings → greet back warmly and ask how you can help
5. NEVER give a generic "Hello! How can I assist you?" style response — it sounds robotic.
6. NEVER repeat a response you already gave in this conversation. Each reply must be unique.
7. If you already know the event type from context, do NOT ask for it again.
8. To recommend venues you need: location, budget, guest_count, event_date. Ask for ONE at a time.

GIFT RULE (IMPORTANT):
- For intent = planning, date, multi, or gift: you MUST include a gift_suggestion.
- The gift must match the TONE and PERSONA preferences.
- Be specific — not "chocolates" but "Dilmah premium tea gift set with personalised card from The Good Market, Colombo".
- Include gift_category: a short category label like "romantic gift", "experience voucher", "personalised keepsake".

INTENT — pick one per response:
- "planning" : user wants a venue, event, or food destination
- "date"     : romantic date specifically
- "gift"     : gift idea only, no venue
- "multi"    : venue AND gift
- "chat"     : greetings, questions, small talk, math, anything else

{tag_block}
BUDGET: total ÷ guests = budget_per_head. "50k" = 50000. null = unknown, never 0.

PERSONA: if user mentions someone they're planning FOR with preferences, fill save_persona + ask_save_persona=true. Never ask the user yourself.

OUTPUT: respond with ONLY a raw JSON object. No markdown fences. Start with {{ end with }}.

{{
  "intent": "chat | planning | date | gift | multi",
  "reasoning": "one sentence — what you understood and why",
  "personality_profile": "short emotion/personality read or null",
  "chat_response": "REQUIRED — your natural reply. Never null. Never generic.",
  "gift_suggestion": "specific, named gift product/service or null",
  "gift_category": "romantic gift | experience voucher | personalised keepsake | corporate gift | celebration gift | null",
  "event_type": "Birthday/Wedding/etc or null",
  "event_date": "YYYY-MM-DD or null",
  "location": "city or null",
  "budget_per_head": number_or_null,
  "guest_count": number_or_null,
  "venue_tags": [],
  "missing_info": [],
  "save_persona": null,
  "ask_save_persona": false,
  "use_persona_name": null
}}"""


def _build_messages(
    raw_query: str,
    history: list,
    system_message: str,
    missing_info: Optional[List[str]],
) -> list[dict]:
    messages = [{"role": "system", "content": system_message}]

    recent = history[-_MAX_HISTORY_TURNS:] if history else []
    for msg in recent:
        user_text = (getattr(msg, "user_message", None) or "").strip()
        ai_text   = (getattr(msg, "ai_message",   None) or "").strip()
        if user_text:
            messages.append({"role": "user",      "content": user_text})
        if ai_text:
            messages.append({"role": "assistant", "content": ai_text})

    user_content = raw_query
    if missing_info:
        user_content += (
            f"\n\n[Still need before recommending venues: {', '.join(missing_info)}. "
            f"Ask for ONE naturally in your reply.]"
        )

    messages.append({"role": "user", "content": user_content})
    return messages


def _get_redis():
    try:
        import redis
        client = redis.from_url(
            getattr(settings, "REDIS_URL", "redis://redis:6379"),
            decode_responses=True,
            socket_connect_timeout=2,
        )
        client.ping()
        return client
    except Exception:
        return None


class AIService:
    def __init__(self):
        self.groq_api_key = getattr(settings, "GROQ_API_KEY", None)
        self.base_url = getattr(settings, "LANGFLOW_URL", None)
        self.token    = getattr(settings, "LANGFLOW_TOKEN", None)
        self.org_id   = getattr(settings, "LANGFLOW_ORG_ID", None)

        if not self.groq_api_key:
            logger.warning("GROQ_API_KEY not set — chat AI will fail. Add it to your .env file.")

    # ── Offering rank — direct Groq API ──────────────────────────────────────
    async def recommend_offerings_for_task(
        self,
        *,
        event_context: dict[str, Any],
        personas: list[dict[str, Any]],
        task: dict[str, Any],
        offerings: list[dict[str, Any]],
        limit: int = 5,
    ) -> list[str] | None:
        if not self.groq_api_key or not offerings:
            return None

        system_msg = (
            "You are a vendor offering ranking engine for Occacia, a premium event "
            "planning platform in Sri Lanka. Rank the candidate offerings for the given "
            "task. Return ONLY a JSON object — no explanation, no markdown.\n\n"
            "RANKING CRITERIA (in order):\n"
            "1. Category match — offering category matches the task type\n"
            "2. Budget fit — price within or close to task budget range\n"
            "3. Persona match — tags/description match recipient preferences\n"
            "4. Event context fit — suits event type, location, guest count\n"
            "5. Availability — prefer isAvailable=true and isActive=true\n\n"
            "RULES:\n"
            f"- Select up to {limit} offerings maximum\n"
            "- Prefer offerings from different vendors when possible\n"
            "- Only use offering_ids that exist in CANDIDATE_OFFERINGS\n"
            "- Order best-first (index 0 = best match)\n"
            "- If nothing matches, return empty array\n\n"
            'OUTPUT — return ONLY this JSON:\n'
            '{"recommended_offering_ids": ["OFF-001"], "reasoning": "one sentence"}'
        )

        user_msg = (
            f"EVENT_CONTEXT: {json.dumps(event_context, ensure_ascii=True)}\n"
            f"PERSONAS: {json.dumps(personas, ensure_ascii=True)}\n"
            f"TASK: {json.dumps(task, ensure_ascii=True)}\n"
            f"CANDIDATE_OFFERINGS: {json.dumps(offerings, ensure_ascii=True)}"
        )

        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type":  "application/json",
        }
        payload = {
            "model":    _GROQ_MODEL,
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user",   "content": user_msg},
            ],
            "temperature":     0.1,
            "max_tokens":      512,
            "response_format": {"type": "json_object"},
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(_GROQ_CHAT_URL, json=payload, headers=headers)
                resp.raise_for_status()
            data        = resp.json()
            raw         = data["choices"][0]["message"]["content"]
            parsed      = json.loads(raw)
            ordered_ids = parsed.get("recommended_offering_ids") or []
            valid_ids   = {o["offering_id"] for o in offerings}
            shortlist: list[str] = []
            seen: set[str] = set()
            for oid in ordered_ids:
                if oid in valid_ids and oid not in seen:
                    shortlist.append(oid)
                    seen.add(oid)
                if len(shortlist) == limit:
                    break
            logger.info(f"Offering rank: selected {len(shortlist)} of {len(offerings)} candidates")
            return shortlist or None
        except Exception as exc:
            logger.warning("AI offering recommendation failed: %s", exc)
            return None

    # ── Main chat — direct Groq API ───────────────────────────────────────────
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=2, max=5),
        retry=retry_if_exception_type(httpx.HTTPStatusError),
    )
    async def generate_date_plan(
        self,
        raw_query: str,
        history: List = None,
        personas: List = None,
        available_tags: List[str] = None,
        missing_info: List[str] = None,
        session_id: str = "",
        event_context: Optional[dict] = None,
        past_events: Optional[list] = None,   # ← NEW: recurring intelligence
    ):
        history  = history or []
        personas = personas or []

        # ── Detect tone ───────────────────────────────────────────────────────
        event_type_str = (event_context or {}).get("event_type", "")
        tone = _detect_tone(event_type_str, raw_query, personas)
        logger.info(f"Detected tone: {tone} | session={session_id}")

        # ── Build system message (uses _build_structured_persona_context) ─────
        system_msg = _build_system_message(
            event_context,
            available_tags,
            personas,
            tone=tone,
            past_events=past_events,
        )
        messages = _build_messages(raw_query, history, system_msg, missing_info)

        turn_count = len(history)
        logger.info(
            f"Outgoing request to Groq | session={session_id} turn={turn_count} "
            f"tone={tone} messages={len(messages)}"
        )

        # ── Cache check ───────────────────────────────────────────────────────
        cache_seed = f"{session_id}:{turn_count}:{raw_query}:{tone}"
        cache_key  = "ai_cache:" + hashlib.md5(cache_seed.encode(), usedforsecurity=False).hexdigest()
        r = _get_redis()
        if r:
            try:
                cached = r.get(cache_key)
                if cached:
                    logger.info("Cache hit — returning cached AI response.")
                    return json.loads(cached)
            except Exception:
                pass

        # ── Call Groq ─────────────────────────────────────────────────────────
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type":  "application/json",
        }
        payload = {
            "model":           _GROQ_MODEL,
            "messages":        messages,
            "temperature":     0.7,
            "max_tokens":      1024,
            "response_format": {"type": "json_object"},
        }

        async with httpx.AsyncClient(timeout=25.0) as client:
            try:
                response = await client.post(_GROQ_CHAT_URL, json=payload, headers=headers)
                response.raise_for_status()
            except httpx.TimeoutException:
                logger.warning("Groq timeout after 25s — returning fallback.")
                return self._timeout_fallback()
            except Exception as e:
                logger.error(f"Groq error: {type(e).__name__}: {repr(e)}")
                raise

        # ── Parse response ────────────────────────────────────────────────────
        data    = response.json()
        outputs = ""
        try:
            outputs = data["choices"][0]["message"]["content"]
            clean   = outputs.replace("```json", "").replace("```", "").strip()

            if not clean.startswith("{"):
                m = re.search(r"\{.*\}", clean, re.DOTALL)
                if m:
                    clean = m.group(0)
                    logger.warning("JSON buried in text — extracted.")

            parsed_data = json.loads(clean)

            if "intent" not in parsed_data:
                raise ValueError("Missing 'intent' field.")

            if not parsed_data.get("chat_response"):
                parsed_data["chat_response"] = (
                    "I'm here to help you plan something amazing! What are we celebrating?"
                )

            # ── Inject gift_category from tone if AI left it null ─────────────
            intent = parsed_data.get("intent", "chat")
            if intent in ("planning", "date", "multi", "gift"):
                if not parsed_data.get("gift_suggestion"):
                    # AI missed the gift — inject a tone-appropriate fallback
                    fallbacks = {
                        _TONE_ROMANTIC:    "A personalised flower bouquet with a handwritten card",
                        _TONE_ADVENTURE:   "An outdoor experience voucher for two",
                        _TONE_FAMILY:      "A personalised family photo frame or memory book",
                        _TONE_CORPORATE:   "A premium branded gift hamper",
                        _TONE_CELEBRATION: "A custom celebration cake or gift hamper",
                    }
                    parsed_data["gift_suggestion"] = fallbacks.get(tone, "A thoughtful personalised gift")
                    logger.info(f"Gift fallback injected for tone={tone}")

                if not parsed_data.get("gift_category"):
                    parsed_data["gift_category"] = _GIFT_CATEGORY_BY_TONE.get(tone)

            # ── Tag validation ────────────────────────────────────────────────
            if available_tags and parsed_data.get("venue_tags"):
                valid    = set(available_tags)
                original = parsed_data["venue_tags"]
                filtered = [t for t in original if t in valid]
                if filtered != original:
                    logger.warning(f"Stripped invalid tags: {set(original) - valid}")
                parsed_data["venue_tags"] = filtered

            # ── Attach tone to response for planning_service ──────────────────
            parsed_data["detected_tone"] = tone

            if r:
                try:
                    r.setex(cache_key, 7200, json.dumps(parsed_data))
                except Exception:
                    pass

            logger.info(
                f"Success: intent={parsed_data.get('intent')} | tone={tone} | "
                f"gift={bool(parsed_data.get('gift_suggestion'))} | "
                f"tags={parsed_data.get('venue_tags')} | "
                f"missing={parsed_data.get('missing_info')}"
            )
            return parsed_data

        except Exception as e:
            logger.warning(f"Parse failed: {e} | Raw snippet: {outputs[:200]}")
            return self._parse_fallback(outputs)

    def _build_prompt(
        self,
        raw_query: str,
        available_tags: List[str] = None,
        missing_info: List[str] = None,
        personas: List = None,
        event_context: Optional[dict] = None,
        history: List = None,
    ) -> str:
        """
        Build and return the full prompt string for inspection or testing.
        Concatenates system message + all user/assistant turns into one string.
        """
        personas = personas or []
        history  = history or []
        tone = _detect_tone(
            (event_context or {}).get("event_type", ""), raw_query, personas
        )
        system_msg = _build_system_message(
            event_context, available_tags, personas, tone=tone
        )
        messages = _build_messages(raw_query, history, system_msg, missing_info)
        return "\n\n".join(m["content"] for m in messages)

    def _timeout_fallback(self) -> dict:
        return {
            "intent": "chat",
            "reasoning": "Groq did not respond within 25 seconds.",
            "personality_profile": None,
            "chat_response": "I'm having a little trouble right now — could you try again in a moment?",
            "gift_suggestion": None,
            "gift_category": None,
            "detected_tone": _TONE_CELEBRATION,
            "event_type": None,
            "event_date": None,
            "location": None,
            "budget_per_head": None,
            "guest_count": None,
            "venue_tags": [],
            "missing_info": [],
            "save_persona": None,
            "ask_save_persona": False,
            "use_persona_name": None,
        }

    def _parse_fallback(self, raw_output: str) -> dict:
        raw_lower = raw_output.lower()
        is_planning = (
            any(v in raw_lower for v in ["plan", "book", "venue", "find", "need", "want"])
            and any(n in raw_lower for n in ["venue", "event", "party", "dinner", "birthday"])
        )
        return {
            "intent": "planning" if is_planning else "chat",
            "reasoning": "Fallback: AI response was not valid JSON.",
            "personality_profile": None,
            "chat_response": (
                "I'd love to help you plan something special! What are we celebrating?"
            ) if is_planning else (
                "Sorry, I lost my train of thought — could you say that again?"
            ),
            "gift_suggestion": None,
            "gift_category": None,
            "detected_tone": _TONE_CELEBRATION,
            "event_type": None,
            "event_date": None,
            "location": None,
            "budget_per_head": None,
            "guest_count": None,
            "venue_tags": [],
            "missing_info": ["location", "budget", "guest_count", "event_date"],
            "save_persona": None,
            "ask_save_persona": False,
            "use_persona_name": None,
        }


ai_service = AIService()