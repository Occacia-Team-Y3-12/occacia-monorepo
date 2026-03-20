"""
app/services/ai_service.py

Fixes applied
─────────────
#1  Cache key now includes session_id + turn count — prevents stale cached
    replies being returned mid-conversation.
#2  event_date added to AI schema — Langflow now returns it and the planning
    service uses it directly instead of relying solely on regex.
#3  task_type field injected into every Langflow payload so the flow can
    route 'planning' vs 'offering_rank' tasks internally.
#5  personality_profile added to the required AI response schema.
#6  recommend_offerings_for_task made fully async (httpx.AsyncClient).
"""
import re
import hashlib
import json
import logging
from typing import Any, List

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings
from app.services.chat_service import chat_service

logger = logging.getLogger(__name__)

# --- Persona preference → package tag mapping ---
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
}


def _build_structured_persona_context(personas: list) -> str:
    """Convert persona objects into a structured AI prompt block."""
    if not personas:
        return ""

    def _to_list(val) -> list[str]:
        if not val:
            return []
        if isinstance(val, list):
            return [str(v).strip().lower() for v in val if v]
        return [s.strip().lower() for s in str(val).split(",") if s.strip()]

    blocks = []
    all_bias_tags: list[str] = []

    for persona in personas:
        name         = getattr(persona, "name",         "Unknown") or "Unknown"
        relationship = getattr(persona, "relationship", "") or ""
        personality  = getattr(persona, "personality",  "") or ""

        food   = _to_list(getattr(persona, "food_preferences",  None))
        colors = _to_list(getattr(persona, "color_preferences", None))
        music  = _to_list(getattr(persona, "music_preferences", None))
        ptags  = _to_list(getattr(persona, "personality_tags",  None))

        # Legacy fallback
        if not any([food, colors, music, ptags]):
            legacy = getattr(persona, "preferences_json", None) or []
            if isinstance(legacy, str):
                try:
                    legacy = json.loads(legacy)
                except Exception:
                    legacy = [s.strip() for s in legacy.split(",") if s.strip()]
            ptags = [str(v).strip().lower() for v in legacy if v]

        derived_tags: list[str] = []
        for pref_list in [food, colors, music, ptags]:
            for pref in pref_list:
                mapped = _PREFERENCE_TO_TAGS.get(pref, [pref])
                derived_tags.extend(mapped)

        seen: set[str] = set()
        unique_tags: list[str] = []
        for t in derived_tags:
            if t not in seen:
                seen.add(t)
                unique_tags.append(t)

        all_bias_tags.extend(unique_tags)

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
            lines.append(f"  -> Suggested package tags: {', '.join(unique_tags)}")
        blocks.append("\n".join(lines))

    seen_global: set[str] = set()
    global_bias: list[str] = []
    for t in all_bias_tags:
        if t not in seen_global:
            seen_global.add(t)
            global_bias.append(t)

    header = (
        "RECIPIENT PROFILES — use the details below to personalise venue and gift suggestions.\n"
        "CRITICAL: When selecting venue_tags, PRIORITISE tags from the 'Suggested package tags' "
        "list for each recipient. Do NOT ignore these even if the user did not mention them explicitly.\n"
    )
    footer = (
        f"\nGLOBAL TAG BIAS (union of all recipient preferences): {', '.join(global_bias)}\n"
        "Blend these into your venue_tags selection wherever they are available in AVAILABLE_VENUE_TAGS."
    )
    return header + "\n\n".join(blocks) + footer


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
        self.base_url = settings.LANGFLOW_URL
        self.token    = settings.LANGFLOW_TOKEN
        self.org_id   = settings.LANGFLOW_ORG_ID

        if not self.token or not self.base_url or not self.org_id:
            logger.warning(
                "Langflow is not configured (missing LANGFLOW_URL/LANGFLOW_TOKEN/LANGFLOW_ORG_ID). "
                "AI endpoints will fail until these are set."
            )

    # ── FIX #6: fully async — no longer blocks the event loop ─────────────────
    async def recommend_offerings_for_task(
        self,
        *,
        event_context: dict[str, Any],
        personas: list[dict[str, Any]],
        task: dict[str, Any],
        offerings: list[dict[str, Any]],
        limit: int = 5,
    ) -> list[str] | None:
        if (
            not self.base_url
            or not self.token
            or not self.org_id
            or not offerings
            or "test-flow" in self.base_url
        ):
            return None

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "X-DataStax-Current-Org": self.org_id,
        }

        prompt = (
            "SYSTEM: Rank candidate vendor offerings for a single event task.\n"
            "Return JSON only with the shape {\"recommended_offering_ids\": [\"OFF-...\"], \"reasoning\": \"...\"}.\n"
            f"Choose up to {limit} offerings from different vendors when possible.\n"
            "Prioritize event context, persona preferences, task constraints, budget, and suitability.\n\n"
            f"EVENT_CONTEXT: {json.dumps(event_context, ensure_ascii=True)}\n"
            f"PERSONAS: {json.dumps(personas, ensure_ascii=True)}\n"
            f"TASK: {json.dumps(task, ensure_ascii=True)}\n"
            f"CANDIDATE_OFFERINGS: {json.dumps(offerings, ensure_ascii=True)}"
        )

        # FIX #3: task_type tells Langflow which routing branch to use
        payload = {
            "input_value": prompt,
            "inputType":   "chat",
            "outputType":  "chat",
            "tweaks":      {"task_type": "offering_rank"},
        }

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.post(self.base_url, json=payload, headers=headers)
                response.raise_for_status()
            data = response.json()
            raw  = data["outputs"][0]["outputs"][0]["results"]["message"]["text"]
            clean = raw.replace("```json", "").replace("```", "").strip()
            if not clean.startswith("{"):
                match = re.search(r"\{.*\}", clean, re.DOTALL)
                if match:
                    clean = match.group(0)
            parsed      = json.loads(clean)
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
        session_id: str = "",       # FIX #1: needed for correct cache key
    ):
        if not self.base_url or not self.token or not self.org_id:
            raise RuntimeError(
                "Langflow is not configured. "
                "Set LANGFLOW_URL, LANGFLOW_TOKEN, and LANGFLOW_ORG_ID."
            )

        headers = {
            "Authorization":          f"Bearer {self.token}",
            "Content-Type":           "application/json",
            "X-DataStax-Current-Org": self.org_id,
        }

        context_string = ""
        if history:
            context_string = chat_service.build_context_string(history)
            if context_string:
                logger.info(f"Memory loaded: {len(history)} turns processed.")

        persona_context = ""
        if personas:
            persona_context = _build_structured_persona_context(personas)
            logger.info(f"Personas loaded: {len(personas)} profiles injected.")

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
            logger.info(f"Tag constraint injected: {len(available_tags)} real tags sent to AI.")

        missing_block = ""
        if missing_info:
            missing_block = (
                f"\n\nPRIORITY — MISSING INFORMATION:\n"
                f"The following details are still needed before a venue recommendation "
                f"can be made. Ask the user specifically for these (one at a time, naturally):\n"
                f"{', '.join(missing_info)}\n"
                f"Do not attempt venue_tags or planning intent until these are known.\n"
            )
            logger.info(f"Missing info injected: {missing_info}")

        # ── FIX #2 + #5: event_date and personality_profile added to schema ───
        system_prefix = (
            "SYSTEM: You are Occi, a stateful event and date planning assistant for Occacia — "
            "a premium event planning platform based in Sri Lanka.\n"
            "CONTEXT: You help customers in Sri Lanka plan events, dates, and gifts. "
            "All prices are in Sri Lankan Rupees (LKR). "
            "Popular locations include Colombo, Kandy, Galle, Ella, Negombo, Nuwara Eliya, "
            "Mirissa, Trincomalee, and Bentota. "
            "Common events include birthdays, anniversaries, weddings, proposals, "
            "corporate retreats, and romantic dates. "
            "Always suggest venues and packages available on Occacia. "
            "When a user mentions a budget, treat it as LKR unless they specify otherwise.\n"
            "You MUST always respond with a single JSON object and nothing else.\n"
            "Required fields in every response:\n"
            "  intent             : one of 'chat' | 'planning' | 'date' | 'gift' | 'multi'\n"
            "  chat_response      : string — your conversational reply to the user\n"
            "  venue_tags         : list[str] — tags from AVAILABLE_VENUE_TAGS only, empty if unknown\n"
            "  missing_info       : list[str] — fields still needed before planning, empty if none\n"
            "  event_type         : string | null\n"
            "  event_date         : string | null — ISO date YYYY-MM-DD if mentioned, else null\n"
            "  location           : string | null\n"
            "  budget_per_head    : number | null\n"
            "  guest_count        : number | null\n"
            "  gift_suggestion    : string | null\n"
            "  personality_profile: string | null — a short summary of the recipient's personality "
            "and preferences inferred from this conversation, or null if unknown\n"
            "  reasoning          : string | null — brief internal note on your decision\n"
            "  save_persona       : object | null — only when new recipient details are available\n"
            "  ask_save_persona   : boolean — true only when save_persona is set\n"
            "  use_persona_name   : string | null — name of saved profile to activate\n"
            "Example minimal response: "
            '{{"intent":"chat","chat_response":"Tell me more!","venue_tags":[],'
            '"missing_info":[],"event_type":null,"event_date":null,"location":null,'
            '"budget_per_head":null,"guest_count":null,"gift_suggestion":null,'
            '"personality_profile":null,"reasoning":null,'
            '"save_persona":null,"ask_save_persona":false,"use_persona_name":null}}'
        )
        parts = [system_prefix]

        if persona_context:
            parts.append(persona_context)
            parts.append(
                "ACTIVE RECIPIENT PROFILE INSTRUCTIONS:\n"
                "The recipient profile above has already been confirmed by the user "
                "in this session. Do NOT ask 'would you like to use this profile?' — "
                "that step is done.\n"
                "1. Silently apply the preferences above when choosing venue_tags and "
                "gift_suggestion.\n"
                "2. Do NOT mention the profile unless the user asks.\n"
                "3. If the user introduces a DIFFERENT person (different name), extract "
                "their details and set save_persona in your JSON with fields: "
                "name, relationship, age, food_preferences, music_preferences, "
                "personality_tags, color_preferences. Also set ask_save_persona=true.\n"
                "4. Never expose the profile data back to the user verbatim."
            )
        else:
            parts.append(
                "NEW RECIPIENT DETECTION:\n"
                "If the user mentions a specific person they are planning for "
                "(e.g. 'my girlfriend Sarah', 'my wife', 'my mum') along with ANY "
                "preferences (food, music, personality, age, relationship), extract "
                "those details and set save_persona in your JSON response with fields: "
                "name, relationship, age, food_preferences, music_preferences, "
                "personality_tags, color_preferences.\n"
                "Also set ask_save_persona=true so the system can prompt the user "
                "to confirm saving — do NOT ask the user yourself.\n"
                "Only extract details when the user has actually provided them. "
                "Do not invent or assume preferences."
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

        # ── FIX #1: cache key includes session + turn count ───────────────────
        # Two different turns in the same session for the same question must
        # get different cache entries because the conversation context differs.
        turn_count = len(history) if history else 0
        cache_seed = (
            f"{session_id}:{turn_count}:{raw_query}"
            f"{tag_block or ''}{missing_block or ''}"
        )
        cache_key = (
            f"ai_cache:"
            f"{hashlib.md5(cache_seed.encode(), usedforsecurity=False).hexdigest()}"
        )
        r = _get_redis()

        if r:
            try:
                cached = r.get(cache_key)
                if cached:
                    logger.info("Cache hit — returning cached AI response.")
                    return json.loads(cached)
            except Exception:
                pass

        # ── FIX #3: task_type tells Langflow this is a planning call ─────────
        payload = {
            "input_value": full_input,
            "inputType":   "chat",
            "outputType":  "chat",
            "tweaks":      {"task_type": "planning"},
        }

        logger.info(
            f"Outgoing request to Langflow | session={session_id} turn={turn_count} "
            f"payload_length={len(full_input)} chars"
        )

        async with httpx.AsyncClient(timeout=25.0) as client:
            try:
                response = await client.post(
                    self.base_url, json=payload, headers=headers
                )
                response.raise_for_status()
            except httpx.TimeoutException:
                logger.warning("Langflow timeout — returning fallback after 25s.")
                return {
                    "intent":              "chat",
                    "reasoning":           "Langflow did not respond within 25 seconds.",
                    "personality_profile": None,
                    "chat_response": (
                        "I'm having a little trouble reaching my planning brain right now. "
                        "Could you try again in a moment? In the meantime, tell me more about "
                        "what you're celebrating!"
                    ),
                    "gift_suggestion":  None,
                    "event_type":       None,
                    "event_date":       None,
                    "location":         None,
                    "budget_per_head":  None,
                    "guest_count":      None,
                    "venue_tags":       [],
                    "missing_info":     [],
                    "save_persona":     None,
                    "ask_save_persona": False,
                }
            except Exception as e:
                logger.error(f"Langflow connection error: {type(e).__name__}: {repr(e)}")
                raise

        data    = response.json()
        outputs = ""
        try:
            outputs = data["outputs"][0]["outputs"][0]["results"]["message"]["text"]
            clean   = outputs.replace("```json", "").replace("```", "").strip()

            if not clean.startswith("{"):
                match = re.search(r'\{.*\}', clean, re.DOTALL)
                if match:
                    clean = match.group(0)
                    logger.warning("JSON buried in text — extracted successfully.")

            parsed_data = json.loads(clean)

            if "intent" not in parsed_data:
                raise ValueError("Missing intent field in parsed JSON")

            if available_tags and parsed_data.get("venue_tags"):
                valid    = set(available_tags)
                original = parsed_data["venue_tags"]
                filtered = [t for t in original if t in valid]
                if filtered != original:
                    logger.warning(
                        f"Tag validation: AI returned invalid tags "
                        f"{set(original) - valid}. Stripped to {filtered}."
                    )
                parsed_data["venue_tags"] = filtered

            if r:
                try:
                    r.setex(cache_key, 7200, json.dumps(parsed_data))
                    logger.info("AI response cached for 2 hours.")
                except Exception:
                    pass

            logger.info(
                f"Success: intent={parsed_data.get('intent')} | "
                f"event_date={parsed_data.get('event_date')} | "
                f"tags={parsed_data.get('venue_tags')} | "
                f"missing={parsed_data.get('missing_info')}"
            )
            return parsed_data

        except Exception as e:
            logger.warning(
                f"Parse failed: {str(e)} | Raw output snippet: {outputs[:200]}"
            )

            raw_lower = outputs.lower()
            PLANNING_VERBS = [
                "plan", "book", "arrange", "find", "need", "want",
                "looking for", "help me", "suggest", "recommend",
            ]
            PLANNING_NOUNS = [
                "venue", "event", "party", "dinner", "wedding",
                "birthday", "celebration", "anniversary", "retreat", "proposal",
            ]
            has_verb    = any(v in raw_lower for v in PLANNING_VERBS)
            has_noun    = any(n in raw_lower for n in PLANNING_NOUNS)
            is_planning = has_verb and has_noun

            return {
                "intent":              "planning" if is_planning else "chat",
                "reasoning":           "Fallback: AI response was not valid JSON.",
                "personality_profile": None,
                "chat_response": (
                    "I'd love to help you plan something special! "
                    "Could you tell me what you're celebrating and how many guests?"
                ) if is_planning else (
                    "My memory is a bit foggy right now — could you try again?"
                ),
                "gift_suggestion":  None,
                "event_type":       None,
                "event_date":       None,
                "location":         None,
                "budget_per_head":  None,
                "guest_count":      None,
                "venue_tags":       [],
                "missing_info":     ["location", "budget", "guest_count", "event_date"],
                "save_persona":     None,
                "ask_save_persona": False,
            }


ai_service = AIService()