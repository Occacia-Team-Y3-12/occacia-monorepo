"""
app/services/ai_service.py

Architecture: Direct Groq API for chat. Langflow removed entirely.
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

# ── Tone detection ─────────────────────────────────────────────────────────────
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

_TONE_ADDON: dict[str, str] = {
    _TONE_ROMANTIC: (
        "TONE — ROMANTIC: Be warm, poetic, emotionally resonant. "
        "Reference candlelit settings, sunset views, private moments. "
        "Gift bias: personalised jewellery, perfume, couples experiences."
    ),
    _TONE_ADVENTURE: (
        "TONE — ADVENTURE: Be energetic, exciting, bold. "
        "Reference outdoor venues, unique experiences, adrenaline. "
        "Gift bias: experience vouchers, gear, activity kits."
    ),
    _TONE_FAMILY: (
        "TONE — FAMILY: Be warm, inclusive, practical. "
        "Reference family-friendly spaces, kid-safe venues, togetherness. "
        "Gift bias: family experiences, personalised keepsakes, photo albums."
    ),
    _TONE_CORPORATE: (
        "TONE — CORPORATE: Be professional, polished, efficient. "
        "Reference business-class venues, conference facilities, team experiences. "
        "Gift bias: branded items, tech accessories, premium hampers."
    ),
    _TONE_CELEBRATION: (
        "TONE — CELEBRATION: Be enthusiastic, fun, vibrant. "
        "Reference party spaces, rooftop venues, entertainment. "
        "Gift bias: personalised gifts, celebration cakes, luxury hampers."
    ),
}

_GIFT_CAT_BY_TONE: dict[str, str] = {
    _TONE_ROMANTIC:    "romantic gift",
    _TONE_ADVENTURE:   "experience voucher",
    _TONE_FAMILY:      "family keepsake",
    _TONE_CORPORATE:   "corporate gift",
    _TONE_CELEBRATION: "celebration gift",
}

_GROQ_CHAT_URL   = "https://api.groq.com/openai/v1/chat/completions"
_GROQ_MODEL      = "llama-3.3-70b-versatile"
_MAX_HISTORY     = 10


def _detect_tone(event_type: Optional[str], user_query: str, personas: list) -> str:
    text = " ".join([
        (event_type or ""), (user_query or ""),
        " ".join(" ".join(getattr(p, "personality_tags", []) or []) for p in (personas or [])),
    ]).lower()
    scores = {t: 0 for t in _TONE_KEYWORDS}
    for tone, kws in _TONE_KEYWORDS.items():
        for kw in kws:
            if kw in text:
                scores[tone] += 1
    best = max(scores, key=lambda t: scores[t])
    if scores[best] == 0:
        et = (event_type or "").lower()
        if any(w in et for w in ["anniversary", "date", "proposal"]): return _TONE_ROMANTIC
        if any(w in et for w in ["birthday", "graduation", "promotion"]): return _TONE_CELEBRATION
        if "corporate" in et or "team" in et: return _TONE_CORPORATE
        if "family" in et: return _TONE_FAMILY
        return _TONE_CELEBRATION
    return best


def _build_memory_block(past_events: Optional[list]) -> str:
    if not past_events:
        return ""
    lines = ["RECURRING INTELLIGENCE — past events for this user:"]
    for ev in past_events[:5]:
        ev_type = ev.get("event_type", "event")
        ev_date = ev.get("event_date", "unknown date")
        ev_loc  = ev.get("location", "unknown location")
        ev_pkgs = ev.get("packages_used", [])
        pkg_str = (", ".join(ev_pkgs[:3])) if ev_pkgs else "no packages recorded"
        lines.append(f"  • {ev_type} on {ev_date} in {ev_loc} — packages: {pkg_str}")
    lines.append(
        "\nMEMORY RULE: If the user is planning something similar to a past event, "
        "proactively say so. Example: 'Last year you did a birthday dinner in Colombo — "
        "want to try something different this time, or raise the bar?' "
        "Be specific. Do NOT be vague."
    )
    return "\n".join(lines) + "\n\n"


def _build_structured_persona_context(personas: list) -> str:
    """
    Build a structured persona context block for injection into AI prompts.
    Named _build_structured_persona_context so tests can patch it by this name.
    """
    if not personas:
        return ""

    def _to_list(val) -> list[str]:
        if not val: return []
        if isinstance(val, list): return [str(v).strip().lower() for v in val if v]
        return [s.strip().lower() for s in str(val).split(",") if s.strip()]

    all_tags: list[str] = []
    blocks: list[str]   = []

    for p in personas:
        name       = getattr(p, "name",             "Unknown") or "Unknown"
        rel        = getattr(p, "relationship",     "") or ""
        food       = _to_list(getattr(p, "food_preferences",  None))
        music      = _to_list(getattr(p, "music_preferences", None))
        ptags      = _to_list(getattr(p, "personality_tags",  None))
        colors     = _to_list(getattr(p, "color_preferences", None))
        prefs_json = _to_list(getattr(p, "preferences_json",  None))
        if not any([food, music, ptags, colors]) and prefs_json:
            ptags = prefs_json

        derived: list[str] = []
        for lst in [food, music, ptags, colors]:
            for pref in lst:
                derived.extend(_PREFERENCE_TO_TAGS.get(pref, [pref]))
        unique_tags = list(dict.fromkeys(derived))
        all_tags.extend(unique_tags)

        lines = [f"Recipient: {name}"]
        if rel:         lines.append(f"  Relationship : {rel}")
        if food:        lines.append(f"  Food         : {', '.join(food)}")
        if music:       lines.append(f"  Music        : {', '.join(music)}")
        if ptags:       lines.append(f"  Vibe         : {', '.join(ptags)}")
        if colors:      lines.append(f"  Colours      : {', '.join(colors)}")
        if unique_tags:
            lines.append(f"  Tag bias     : {', '.join(unique_tags)}")
            lines.append(f"  Suggested package tags: {', '.join(unique_tags)}")
        blocks.append("\n".join(lines))

    global_tags = list(dict.fromkeys(all_tags))
    output  = "RECIPIENT PROFILE (silently inform ALL venue + gift suggestions):\n"
    output += "\n\n".join(blocks)
    if global_tags:
        output += f"\n\nGLOBAL TAG BIAS — {', '.join(global_tags)}\n"
        output += (
            "CRITICAL — PRIORITISE packages whose tags overlap with the global tag bias. "
            "Never suggest something that contradicts these preferences.\n\n"
        )
    return output


# ── Backward-compat alias ─────────────────────────────────────────────────────
_build_persona_context = _build_structured_persona_context


def _build_system_message(
    event_context: Optional[dict],
    available_tags: Optional[List[str]],
    personas: list,
    tone: str = _TONE_CELEBRATION,
    past_events: Optional[list] = None,
) -> str:

    has_tags = bool(available_tags)
    tag_list = ", ".join(available_tags) if has_tags else ""
    tag_block = (
        f"AVAILABLE_VENUE_TAGS — use ONLY these, pick 2–4 max:\n{tag_list}\n"
        if has_tags else ""
    )

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
            event_block = "EVENT CONTEXT (already confirmed — use this, do NOT re-ask):\n" + "\n".join(parts) + "\n\n"

    persona_block = _build_structured_persona_context(personas) if personas else ""
    memory_block  = _build_memory_block(past_events)
    tone_addon    = _TONE_ADDON.get(tone, "")

    return f"""You are Occi — an elite, sharp, warm event planner for Occacia, Sri Lanka's premium event platform.
You have razor-sharp intelligence and genuine emotional warmth. You are NEVER generic or robotic.

{event_block}{persona_block}{memory_block}{tone_addon}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CORE PERSONALITY RULES — NEVER BREAK THESE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. RESPOND TO EXACTLY WHAT THE USER SAID. Read their message. React to it specifically.
2. BANNED PHRASES (instant disqualifier — never use these):
   - "Hello! How can I assist you today?"
   - "Great! I'd be happy to help!"
   - "Certainly! Here's what I recommend:"
   - "As an AI event planner..."
   - "How can I make your day special?"
   - Any opening that doesn't directly engage with what the user said.
3. If the user says something funny → be playful back. If emotional → be warm. If direct → be crisp.
4. Reference SPECIFIC details the user mentioned. Never give a generic answer.
5. Do NOT repeat yourself. Every reply must advance the conversation.
6. Do NOT re-ask for information already confirmed (see ALREADY CONFIRMED block if present).
7. Ask for ONE missing thing at a time — never fire 3 questions in a row.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PERSONA EXTRACTION RULE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
When the user mentions ANYTHING about the recipient (name, food, music, hobbies, personality,
colours, relationship), extract it immediately into save_persona.
Do this EVERY TURN — even if the user only mentioned one detail.
Never wait until you have "enough" data. Extract what you have NOW.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INTENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- "planning" : user wants a venue / event / food destination
- "date"     : specifically a romantic date
- "gift"     : gift idea only, no venue
- "multi"    : venue AND gift
- "chat"     : anything else — questions, greetings, math, small talk

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GIFT RULE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
For planning / date / multi / gift intent: ALWAYS include gift_suggestion.
Be specific — not "chocolates" but "Dilmah premium tea gift set with a handwritten card,
available at The Good Market, Colombo".

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONTEXT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Currency: LKR. "50k" = 50000. budget_per_head = total ÷ guests. null ≠ 0.
- Sri Lanka locations: Colombo, Kandy, Galle, Ella, Negombo, Nuwara Eliya,
  Mirissa, Trincomalee, Bentota
- Events: birthdays, anniversaries, weddings, proposals, corporate retreats, dates

{tag_block}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT — raw JSON ONLY. No markdown. Start with {{ end with }}.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{{
  "intent": "chat | planning | date | gift | multi",
  "reasoning": "one sentence — what you understood",
  "personality_profile": "short read of user emotion/personality or null",
  "chat_response": "REQUIRED. Your actual reply. Never null. Never generic. Never robotic.",
  "gift_suggestion": "specific named gift or null",
  "gift_category": "romantic gift | experience voucher | personalised keepsake | corporate gift | celebration gift | null",
  "event_type": "Birthday/Wedding/etc or null",
  "event_date": "YYYY-MM-DD or null",
  "location": "city or null",
  "budget_per_head": number_or_null,
  "guest_count": number_or_null,
  "venue_tags": [],
  "missing_info": [],
  "save_persona": {{
    "name": "string or null",
    "relationship": "string or null",
    "personality": "string or null",
    "food_preferences": [],
    "music_preferences": [],
    "personality_tags": [],
    "color_preferences": []
  }},
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
    recent = history[-_MAX_HISTORY:] if history else []
    for msg in recent:
        user_text = (getattr(msg, "user_message", None) or "").strip()
        ai_text   = (getattr(msg, "ai_message",   None) or "").strip()
        if user_text: messages.append({"role": "user",      "content": user_text})
        if ai_text:   messages.append({"role": "assistant", "content": ai_text})
    user_content = raw_query
    if missing_info:
        user_content += (
            f"\n\n[Still needed before recommending venues: {', '.join(missing_info)}. "
            f"Ask for ONE naturally in your reply.]"
        )
    messages.append({"role": "user", "content": user_content})
    return messages


def _get_redis():
    try:
        import redis
        client = redis.from_url(
            getattr(settings, "REDIS_URL", "redis://redis:6379"),
            decode_responses=True, socket_connect_timeout=2,
        )
        client.ping()
        return client
    except Exception:
        return None


class AIService:
    def __init__(self):
        self.groq_api_key = getattr(settings, "GROQ_API_KEY", None)
        self.base_url     = getattr(settings, "LANGFLOW_URL", None)
        self.token        = getattr(settings, "LANGFLOW_TOKEN", None)
        self.org_id       = getattr(settings, "LANGFLOW_ORG_ID", None)

        if not self.groq_api_key:
            logger.warning("GROQ_API_KEY not set — chat AI will fail. Add it to your .env file.")

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
            "You are a vendor offering ranking engine for Occacia. "
            "Rank candidate offerings for the given task. "
            "Return ONLY a JSON object — no explanation, no markdown.\n\n"
            "RANKING CRITERIA:\n"
            "1. Category match\n2. Budget fit\n3. Persona match\n"
            "4. Event context fit\n5. Availability\n\n"
            f"- Select up to {limit} offerings maximum\n"  # nosec B608
            "- Prefer offerings from different vendors\n"
            "- Only use offering_ids from CANDIDATE_OFFERINGS\n"
            "- Order best-first\n"
            "- If nothing matches, return empty array\n\n"
            'OUTPUT: {{"recommended_offering_ids": ["OFF-001"], "reasoning": "one sentence"}}'
        )

        user_msg = (
            f"EVENT_CONTEXT: {json.dumps(event_context, ensure_ascii=True)}\n"
            f"PERSONAS: {json.dumps(personas, ensure_ascii=True)}\n"
            f"TASK: {json.dumps(task, ensure_ascii=True)}\n"
            f"CANDIDATE_OFFERINGS: {json.dumps(offerings, ensure_ascii=True)}"
        )

        headers = {"Authorization": f"Bearer {self.groq_api_key}", "Content-Type": "application/json"}
        payload = {
            "model": _GROQ_MODEL,
            "messages": [{"role": "system", "content": system_msg},
                         {"role": "user",   "content": user_msg}],
            "temperature": 0.1, "max_tokens": 512,
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
            return shortlist or None
        except Exception as exc:
            logger.warning("AI offering recommendation failed: %s", exc)
            return None

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
        past_events: Optional[list] = None,
    ):
        history  = history or []
        personas = personas or []

        event_type_str = (event_context or {}).get("event_type", "")
        tone = _detect_tone(event_type_str, raw_query, personas)

        system_msg = _build_system_message(
            event_context, available_tags, personas,
            tone=tone, past_events=past_events,
        )
        messages = _build_messages(raw_query, history, system_msg, missing_info)

        turn_count = len(history)
        logger.info(f"Groq request | session={session_id} turn={turn_count} tone={tone}")

        cache_seed = f"{session_id}:{turn_count}:{raw_query}:{tone}"
        cache_key  = "ai_cache:" + hashlib.md5(cache_seed.encode(), usedforsecurity=False).hexdigest()
        r = _get_redis()
        if r:
            try:
                cached = r.get(cache_key)
                if cached:
                    logger.info("Cache hit.")
                    return json.loads(cached)
            except Exception:
                pass

        headers = {"Authorization": f"Bearer {self.groq_api_key}", "Content-Type": "application/json"}
        payload = {
            "model":           _GROQ_MODEL,
            "messages":        messages,
            "temperature":     0.75,
            "max_tokens":      1024,
            "response_format": {"type": "json_object"},
        }

        async with httpx.AsyncClient(timeout=25.0) as client:
            try:
                response = await client.post(_GROQ_CHAT_URL, json=payload, headers=headers)
                response.raise_for_status()
            except httpx.TimeoutException:
                logger.warning("Groq timeout after 25s.")
                return self._timeout_fallback()
            except Exception as e:
                logger.error(f"Groq error: {type(e).__name__}: {repr(e)}")
                raise

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

            intent = parsed_data.get("intent", "chat")
            if intent in ("planning", "date", "multi", "gift"):
                if not parsed_data.get("gift_suggestion"):
                    fallbacks = {
                        _TONE_ROMANTIC:    "A personalised flower bouquet with a handwritten card",
                        _TONE_ADVENTURE:   "An outdoor experience voucher for two",
                        _TONE_FAMILY:      "A personalised family photo frame or memory book",
                        _TONE_CORPORATE:   "A premium branded gift hamper",
                        _TONE_CELEBRATION: "A custom celebration cake or luxury gift hamper",
                    }
                    parsed_data["gift_suggestion"] = fallbacks.get(tone, "A thoughtful personalised gift")
                if not parsed_data.get("gift_category"):
                    parsed_data["gift_category"] = _GIFT_CAT_BY_TONE.get(tone)

            if available_tags and parsed_data.get("venue_tags"):
                valid    = set(available_tags)
                original = parsed_data["venue_tags"]
                filtered = [t for t in original if t in valid]
                if filtered != original:
                    logger.warning(f"Stripped invalid tags: {set(original) - valid}")
                parsed_data["venue_tags"] = filtered

            parsed_data["detected_tone"] = tone

            if r:
                try:
                    r.setex(cache_key, 7200, json.dumps(parsed_data))
                except Exception:
                    pass

            logger.info(
                f"Success: intent={parsed_data.get('intent')} tone={tone} "
                f"gift={bool(parsed_data.get('gift_suggestion'))} "
                f"tags={parsed_data.get('venue_tags')} "
                f"missing={parsed_data.get('missing_info')}"
            )
            return parsed_data

        except Exception as e:
            logger.warning(f"Parse failed: {e} | Raw: {outputs[:200]}")
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
        personas = personas or []
        history  = history or []
        tone = _detect_tone(
            (event_context or {}).get("event_type", ""), raw_query, personas
        )
        system_msg = _build_system_message(event_context, available_tags, personas, tone=tone)
        messages   = _build_messages(raw_query, history, system_msg, missing_info)
        return "\n\n".join(m["content"] for m in messages)

    def _timeout_fallback(self) -> dict:
        return {
            "intent": "chat", "reasoning": "Groq timed out.",
            "personality_profile": None,
            "chat_response": "I'm having a little trouble right now — try again in a moment?",
            "gift_suggestion": None, "gift_category": None,
            "detected_tone": _TONE_CELEBRATION,
            "event_type": None, "event_date": None, "location": None,
            "budget_per_head": None, "guest_count": None,
            "venue_tags": [], "missing_info": [],
            "save_persona": None, "ask_save_persona": False, "use_persona_name": None,
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
            "gift_suggestion": None, "gift_category": None,
            "detected_tone": _TONE_CELEBRATION,
            "event_type": None, "event_date": None, "location": None,
            "budget_per_head": None, "guest_count": None,
            "venue_tags": [],
            "missing_info": ["location", "budget", "guest_count", "event_date"],
            "save_persona": None, "ask_save_persona": False, "use_persona_name": None,
        }


ai_service = AIService()