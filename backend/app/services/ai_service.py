import re
import hashlib
import json
import logging
from typing import List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx
from app.core.config import settings
from app.services.chat_service import chat_service

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Persona preference → package tag mapping
# ─────────────────────────────────────────────────────────────────────────────

# Maps freeform preference keywords to known vendor package tags.
# A persona who loves "nature" and "adventure" will bias matches toward
# packages tagged with those exact strings.
_PREFERENCE_TO_TAGS: dict[str, list[str]] = {
    # food preferences
    "fine dining":    ["fine-dining", "luxury"],
    "fine-dining":    ["fine-dining", "luxury"],
    "casual dining":  ["casual"],
    "brunch":         ["brunch"],
    "vegan":          ["wellness", "nature"],
    "seafood":        ["beach", "fine-dining"],
    # color / vibe preferences
    "nature":         ["nature", "outdoor", "wellness"],
    "blue":           ["beach", "pool", "nature"],
    "green":          ["nature", "outdoor", "hiking"],
    "red":            ["romantic", "luxury"],
    "purple":         ["luxury", "spa"],
    "pastel":         ["wellness", "brunch"],
    "dark":           ["nightlife", "luxury"],
    # music preferences
    "jazz":           ["fine-dining", "luxury", "romantic"],
    "pop":            ["party", "nightlife"],
    "classical":      ["luxury", "fine-dining", "cultural"],
    "electronic":     ["nightlife", "party"],
    "acoustic":       ["romantic", "nature", "wellness"],
    "live music":     ["music", "party"],
    # personality / vibe tags (direct passthrough)
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
}


def _build_structured_persona_context(personas: list) -> str:
    """
    Convert persona objects into a structured AI prompt block.

    Reads four preference fields from each persona:
        food_preferences    – list[str] or comma-separated str
        color_preferences   – list[str] or comma-separated str
        music_preferences   – list[str] or comma-separated str
        personality_tags    – list[str] or comma-separated str

    Falls back to legacy `preferences_json` (list of hobby strings) when the
    new fields are absent, so existing personas keep working.

    Returns a single prompt string that instructs the AI to bias tag selection
    toward the derived package tags.
    """
    if not personas:
        return ""

    blocks = []
    all_bias_tags: list[str] = []

    for persona in personas:
        name = getattr(persona, "name", "Unknown") or "Unknown"
        relationship = getattr(persona, "relationship", "") or ""
        personality = getattr(persona, "personality", "") or ""

        # ── Collect raw preferences from new structured fields ────────────
        def _to_list(val) -> list[str]:
            if not val:
                return []
            if isinstance(val, list):
                return [str(v).strip().lower() for v in val if v]
            return [s.strip().lower() for s in str(val).split(",") if s.strip()]

        food   = _to_list(getattr(persona, "food_preferences",  None))
        colors = _to_list(getattr(persona, "color_preferences", None))
        music  = _to_list(getattr(persona, "music_preferences", None))
        ptags  = _to_list(getattr(persona, "personality_tags",  None))

        # ── Legacy fallback: preferences_json (list of hobby strings) ─────
        if not any([food, colors, music, ptags]):
            legacy = getattr(persona, "preferences_json", None) or []
            if isinstance(legacy, str):
                import json as _j
                try:
                    legacy = _j.loads(legacy)
                except Exception:
                    legacy = [s.strip() for s in legacy.split(",") if s.strip()]
            ptags = [str(v).strip().lower() for v in legacy if v]

        # ── Map preferences → package tags ───────────────────────────────
        derived_tags: list[str] = []
        for pref_list in [food, colors, music, ptags]:
            for pref in pref_list:
                mapped = _PREFERENCE_TO_TAGS.get(pref, [pref])  # passthrough if unknown
                derived_tags.extend(mapped)

        # Deduplicate while preserving order
        seen: set[str] = set()
        unique_tags: list[str] = []
        for t in derived_tags:
            if t not in seen:
                seen.add(t)
                unique_tags.append(t)

        all_bias_tags.extend(unique_tags)

        # ── Build per-persona description block ───────────────────────────
        lines = [f"RECIPIENT PROFILE — {name}"]
        if relationship:
            lines.append(f"  Relationship : {relationship}")
        if personality:
            lines.append(f"  Personality  : {personality}")
        if food:
            lines.append(f"  Food prefs   : {', '.join(food)}")
        if colors:
            lines.append(f"  Colour prefs : {', '.join(colors)}")
        if music:
            lines.append(f"  Music prefs  : {', '.join(music)}")
        if ptags:
            lines.append(f"  Vibe / tags  : {', '.join(ptags)}")
        if unique_tags:
            lines.append(f"  → Suggested package tags: {', '.join(unique_tags)}")
        blocks.append("\n".join(lines))

    # De-dup global bias tags
    seen_global: set[str] = set()
    global_bias: list[str] = []
    for t in all_bias_tags:
        if t not in seen_global:
            seen_global.add(t)
            global_bias.append(t)

    header = (
        "RECIPIENT PROFILES — use the details below to personalise venue and gift suggestions.\n"
        "CRITICAL: When selecting venue_tags, PRIORITISE tags from the 'Suggested package tags' "
        "list for each recipient. Do NOT ignore these even if the user did not mention them "
        "explicitly.\n"
    )
    footer = (
        f"\nGLOBAL TAG BIAS (union of all recipient preferences): {', '.join(global_bias)}\n"
        "Blend these into your venue_tags selection wherever they are available in "
        "AVAILABLE_VENUE_TAGS."
    )
    return header + "\n\n".join(blocks) + footer


def _get_redis():
    try:
        import redis
        client = redis.from_url(
            getattr(settings, "REDIS_URL", "redis://redis:6379"),
            decode_responses=True,
            socket_connect_timeout=2
        )
        client.ping()
        return client
    except Exception:
        return None


class AIService:
    def __init__(self):
        self.base_url = settings.LANGFLOW_URL
        self.token = settings.LANGFLOW_TOKEN
        self.org_id = settings.LANGFLOW_ORG_ID

        if not self.token or not self.base_url or not self.org_id:
            logger.warning(
                "Langflow is not configured (missing LANGFLOW_URL/LANGFLOW_TOKEN/LANGFLOW_ORG_ID). "
                "AI endpoints will fail until these are set."
            )

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=2, max=5),
        retry=retry_if_exception_type(httpx.HTTPStatusError)
    )
    async def generate_date_plan(
        self,
        raw_query: str,
        history: List = None,
        personas: List = None,
        available_tags: List[str] = None,
        missing_info: List[str] = None,
    ):
        if not self.base_url or not self.token or not self.org_id:
            raise RuntimeError(
                "Langflow is not configured. Set LANGFLOW_URL, LANGFLOW_TOKEN, and LANGFLOW_ORG_ID."
            )

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "X-DataStax-Current-Org": self.org_id
        }

        context_string = ""
        if history:
            context_string = chat_service.build_context_string(history)
            if context_string:
                logger.info(f"🧠 MEMORY LOADED: {len(history)} turns processed into context.")

        persona_context = ""
        if personas:
            persona_context = _build_structured_persona_context(personas)
            logger.info(f"👤 PERSONAS LOADED: {len(personas)} profiles injected into prompt.")

        tag_block = ""
        if available_tags:
            tag_block = (
                f"\n\nAVAILABLE_VENUE_TAGS — CRITICAL INSTRUCTION:\n"
                f"You MUST only use tags from this exact list in the venue_tags field.\n"
                f"Do NOT invent, combine, or modify tags. Pick the closest matches only:\n"
                f"{', '.join(available_tags)}\n"
                f"Example: if user wants 'romantic outdoor dinner', use ['romantic', 'nature'] "
                f"not 'romantic-outdoor-dinner'.\n"
            )
            logger.info(f"🏷️ TAG CONSTRAINT INJECTED: {len(available_tags)} real tags sent to AI.")

        missing_block = ""
        if missing_info:
            missing_block = (
                f"\n\nPRIORITY — MISSING INFORMATION:\n"
                f"The following details are still needed before a venue recommendation "
                f"can be made. Ask the user specifically for these (one at a time, naturally):\n"
                f"{', '.join(missing_info)}\n"
                f"Do not attempt venue_tags or planning intent until these are known.\n"
            )
            logger.info(f"❓ MISSING INFO INJECTED: {missing_info}")

        system_prefix = "SYSTEM: You are a stateful event and gift planning assistant."
        parts = [system_prefix]

        if persona_context:
            parts.append(persona_context)
            parts.append(
                "IMPORTANT: If the user's request involves a gift, ask them: "
                "'Would you like me to use one of your saved profiles to personalize this?' "
                "Then use their choice to tailor suggestions."
            )

        if tag_block:
            parts.append(tag_block)
        if missing_block:
            parts.append(missing_block)
        if context_string:
            parts.append(context_string)

        parts.append(f"CURRENT_USER_INPUT: {raw_query}")
        full_input = "\n\n".join(parts)

        if not persona_context and not context_string and not tag_block and not missing_block:
            full_input = raw_query

        cache_seed = full_input + (tag_block or "")
        cache_key = f"ai_cache:{hashlib.md5(cache_seed.encode(), usedforsecurity=False).hexdigest()}"
        r = _get_redis()
        if r:
            try:
                cached = r.get(cache_key)
                if cached:
                    logger.info("⚡ CACHE HIT — returning cached AI response.")
                    return json.loads(cached)
            except Exception:
                pass

        payload = {
            "input_value": full_input,
            "inputType": "chat",
            "outputType": "chat",
            "tweaks": {}
        }

        logger.info(f"📡 OUTGOING TO LANGFLOW | Payload length: {len(full_input)} chars")

        async with httpx.AsyncClient(timeout=25.0) as client:
            try:
                response = await client.post(
                    self.base_url, json=payload, headers=headers
                )
                response.raise_for_status()
            except httpx.TimeoutException:
                logger.warning("⏱️ LANGFLOW TIMEOUT — returning immediate fallback after 25 s.")
                return {
                    "intent": "chat",
                    "reasoning": "Langflow did not respond within 25 seconds.",
                    "personality_profile": None,
                    "chat_response": (
                        "I'm having a little trouble reaching my planning brain right now 🙈 "
                        "Could you try again in a moment? In the meantime, tell me more about "
                        "what you're celebrating!"
                    ),
                    "gift_suggestion": None,
                    "event_type": None,
                    "location": None,
                    "budget_per_head": None,
                    "guest_count": None,
                    "venue_tags": [],
                    "missing_info": [],
                }
            except Exception as e:
                logger.error(f"🔥 LANGFLOW CONNECTION ERROR: {type(e).__name__}: {repr(e)}")
                raise

            data = response.json()
            outputs = ""
            try:
                outputs = data["outputs"][0]["outputs"][0]["results"]["message"]["text"]
                clean = outputs.replace("```json", "").replace("```", "").strip()

                if not clean.startswith("{"):
                    match = re.search(r'\{.*\}', clean, re.DOTALL)
                    if match:
                        clean = match.group(0)
                        logger.warning("⚠️ JSON buried in text — extracted successfully.")

                parsed_data = json.loads(clean)

                if "intent" not in parsed_data:
                    raise ValueError("Missing intent field in parsed JSON")

                if available_tags and parsed_data.get("venue_tags"):
                    valid = set(available_tags)
                    original = parsed_data["venue_tags"]
                    filtered = [t for t in original if t in valid]
                    if filtered != original:
                        logger.warning(
                            f"⚠️ TAG VALIDATION: AI returned invalid tags {set(original) - valid}. "
                            f"Stripped to {filtered}."
                        )
                    parsed_data["venue_tags"] = filtered

                if r:
                    try:
                        r.setex(cache_key, 7200, json.dumps(parsed_data))
                        logger.info("💾 AI response cached for 2 hours.")
                    except Exception:
                        pass

                logger.info(
                    f"✅ SUCCESS: intent={parsed_data.get('intent')} | "
                    f"tags={parsed_data.get('venue_tags')} | "
                    f"missing={parsed_data.get('missing_info')}"
                )
                return parsed_data

            except Exception as e:
                logger.warning(f"⚠️ PARSE FAILED: {str(e)} | Raw: {outputs[:200]}")

                raw_lower = outputs.lower()
                PLANNING_VERBS = [
                    "plan", "book", "arrange", "find", "need", "want",
                    "looking for", "help me", "suggest", "recommend"
                ]
                PLANNING_NOUNS = [
                    "venue", "event", "party", "dinner", "wedding",
                    "birthday", "celebration", "anniversary", "retreat", "proposal"
                ]
                has_verb = any(v in raw_lower for v in PLANNING_VERBS)
                has_noun = any(n in raw_lower for n in PLANNING_NOUNS)
                is_planning = has_verb and has_noun

                return {
                    "intent": "planning" if is_planning else "chat",
                    "reasoning": "Fallback: AI response was not valid JSON.",
                    "personality_profile": None,
                    "chat_response": (
                        "I'd love to help you plan something special! "
                        "Could you tell me what you're celebrating and how many guests?"
                    ) if is_planning else (
                        "My memory is a bit foggy right now — could you try again?"
                    ),
                    "gift_suggestion": None,
                    "event_type": None,
                    "location": None,
                    "budget_per_head": None,
                    "guest_count": None,
                    "venue_tags": [],
                    "missing_info": ["location", "budget", "guest_count", "event_date"]
                }


ai_service = AIService()
