"""
app/services/groq_ai_service.py

Pure Groq API adapter for event chat.
No business logic — only prompt building, API call, and structured JSON parsing.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, List, Optional

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import settings

logger = logging.getLogger(__name__)

_GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
_GROQ_MODEL = "llama-3.3-70b-versatile"
_MAX_HISTORY = 10


# ---------------------------------------------------------------------------
# Prompt helpers
# ---------------------------------------------------------------------------

def _build_persona_block(personas: list) -> str:
    if not personas:
        return ""

    def _to_list(val) -> list[str]:
        if not val:
            return []
        if isinstance(val, list):
            return [str(v).strip() for v in val if v]
        return [s.strip() for s in str(val).split(",") if s.strip()]

    blocks: list[str] = []
    for p in personas:
        name  = getattr(p, "name",             "Unknown") or "Unknown"
        rel   = getattr(p, "relationship",     "") or ""
        food  = _to_list(getattr(p, "food_preferences",  None))
        music = _to_list(getattr(p, "music_preferences", None))
        ptags = _to_list(getattr(p, "personality_tags",  None))
        colors = _to_list(getattr(p, "color_preferences", None))

        lines = [f"Recipient: {name}"]
        if rel:    lines.append(f"  Relationship : {rel}")
        if food:   lines.append(f"  Food         : {', '.join(food)}")
        if music:  lines.append(f"  Music        : {', '.join(music)}")
        if ptags:  lines.append(f"  Vibe         : {', '.join(ptags)}")
        if colors: lines.append(f"  Colours      : {', '.join(colors)}")
        blocks.append("\n".join(lines))

    return (
        "RECIPIENT PROFILE (silently inform ALL venue + experience suggestions):\n"
        + "\n\n".join(blocks)
        + "\n\n"
    )


def _build_event_block(event_context: Optional[dict]) -> str:
    if not event_context:
        return ""
    parts = []
    if event_context.get("title"):        parts.append(f"Event title : {event_context['title']}")
    if event_context.get("event_type"):   parts.append(f"Type        : {event_context['event_type']}")
    if event_context.get("event_date"):   parts.append(f"Date        : {event_context['event_date']}")
    if event_context.get("location"):     parts.append(f"Location    : {event_context['location']}")
    if event_context.get("guest_count"):  parts.append(f"Guests      : {event_context['guest_count']}")
    if event_context.get("budget_per_head"):
        parts.append(f"Budget/head : LKR {event_context['budget_per_head']}")
    if event_context.get("existing_tasks"):
        parts.append(f"Tasks so far: {', '.join(event_context['existing_tasks'])}")
    if not parts:
        return ""
    return (
        "EVENT CONTEXT (already confirmed — use this, do NOT re-ask):\n"
        + "\n".join(parts)
        + "\n\n"
    )


def _build_system_prompt(
    event_context: Optional[dict],
    personas: list,
    needs_persona: bool,
) -> str:
    event_block   = _build_event_block(event_context)
    persona_block = _build_persona_block(personas) if personas else ""

    if needs_persona:
        persona_instruction = (
            "PERSONA COLLECTION MODE:\n"
            "You do NOT yet have a profile for the person this event is for.\n"
            "Your first priority is to learn about them: name, relationship to the customer,\n"
            "personality vibe, food preferences, music preferences, favourite colours.\n"
            "Ask ONE question at a time. Do NOT ask about budget, guests, or dates yet.\n"
            "Once you have at least a name, set save_persona=true and personaDraft.name.\n\n"
        )
    else:
        persona_instruction = (
            "PLANNING MODE:\n"
            "Persona is already captured. Focus on collecting: budget, number of guests,\n"
            "date + month, and what they expect from the event.\n"
            "Once all four are known, recommend 3 specific Sri Lankan event experiences.\n\n"
        )

    return f"""You are Occi — an elite, sharp, warm event planner for Occacia, Sri Lanka's premium event platform.
You have razor-sharp intelligence and genuine emotional warmth.

{event_block}{persona_block}{persona_instruction}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CORE PERSONALITY RULES — NEVER BREAK THESE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. RESPOND TO EXACTLY WHAT THE USER SAID. Read their message. React to it specifically.
2. BANNED PHRASES (instant disqualifier — never say these):
   - "Hello! How can I assist you today?"
   - "Great! I'd be happy to help!"
   - "Certainly! Here's what I recommend:"
   - "As an AI event planner..."
   - Any opening that doesn't directly engage with what the user said.
3. If the user is funny → be playful. If emotional → be warm. If direct → be crisp.
4. Reference SPECIFIC details already confirmed. Never give generic answers.
5. Do NOT repeat yourself. Every reply must advance the conversation.
6. Do NOT re-ask for confirmed information (see EVENT CONTEXT block if present).
7. Ask for ONE missing thing at a time — never fire multiple questions at once.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONVERSATION FLOW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 1 (if needsPersona=true): Learn about the person the event is for.
  Ask ONE thing at a time: name → relationship → vibe/personality → food → music.
  Once you have a name, set save_persona=true. Tell the user the profile is saved before moving on.

Step 2 (once persona done or not needed): Collect event details one at a time:
  → budget (total or per head in LKR)
  → number of guests
  → date + month
  → what they want to experience / expectations

Step 3 (all event facts collected): Recommend exactly 3 event experiences.
  Be specific. Name REAL Sri Lanka venues or experiences.
  Examples: Heritance Ahungalla, Galle Face Hotel, Saffron, Nihonbashi, Mount Lavinia Hotel,
  Colombo Rowing Club, The Long Bar, Marino Beach, OZO Colombo, Wallawwa, etc.
  Include estimated price per head for each option.

Step 4: If the user wants changes → ask what to tweak, then re-suggest.
Step 5: When user selects a package → tell them to click "Confirm Tasks & View Recommendations".

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PERSONA EXTRACTION RULE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Whenever the user mentions ANYTHING about the recipient (name, food, music, hobbies,
personality, colours, relationship), extract it immediately into personaDraft.
Do this EVERY TURN — even for a single detail. Never wait for "enough" data.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONTEXT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Currency: LKR. "50k" = 50000. budgetPerHead = total ÷ guests. null ≠ 0.
- Sri Lanka locations: Colombo, Kandy, Galle, Ella, Negombo, Nuwara Eliya,
  Mirissa, Trincomalee, Bentota, Mount Lavinia, Sigiriya.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT — raw JSON ONLY. No markdown. Start with {{ end with }}.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{{
  "reply": "REQUIRED. Your actual reply. Never null. Never generic. Never robotic.",
  "needsPersona": true,
  "personaDraft": {{
    "name": "string or null",
    "relationship": "string or null",
    "personality_tags": [],
    "food_preferences": [],
    "music_preferences": [],
    "color_preferences": []
  }},
  "eventFacts": {{
    "date": "YYYY-MM-DD or null",
    "timezone": "Asia/Colombo or null",
    "guestCount": null,
    "budgetPerHead": null,
    "expectations": "string or null"
  }},
  "calendarIntent": {{
    "wantsSync": false,
    "provider": "GOOGLE or null"
  }},
  "missingInfo": ["date", "budgetPerHead", "guestCount"],
  "suggestedTasks": [
    {{"name": "string", "description": "string or null", "quantity": 1, "currency": "LKR"}}
  ],
  "intent": "chat | planning | confirm",
  "save_persona": true
}}"""


def _build_messages(
    content: str,
    history: list,
    system_prompt: str,
) -> list[dict]:
    messages = [{"role": "system", "content": system_prompt}]
    recent = history[-_MAX_HISTORY:] if history else []
    for msg in recent:
        user_text = (getattr(msg, "user_message", None) or "").strip()
        ai_text   = (getattr(msg, "ai_message",   None) or "").strip()
        if user_text: messages.append({"role": "user",      "content": user_text})
        if ai_text:   messages.append({"role": "assistant", "content": ai_text})
    messages.append({"role": "user", "content": content})
    return messages


# ---------------------------------------------------------------------------
# Service class
# ---------------------------------------------------------------------------

class GroqAIService:
    def __init__(self):
        self.groq_api_key: str | None = getattr(settings, "GROQ_API_KEY", None)
        if not self.groq_api_key:
            logger.warning("GROQ_API_KEY not set — event chat AI will fail.")

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=2, max=5),
        retry=retry_if_exception_type(httpx.HTTPStatusError),
    )
    async def plan_event_chat(
        self,
        content: str,
        history: list,
        personas: list,
        event_context: Optional[dict],
        needs_persona: bool,
    ) -> dict[str, Any]:
        """
        Call Groq and return the parsed structured JSON output.
        Raises on timeout or unrecoverable parse failure — no fallback dicts.
        """
        system_prompt = _build_system_prompt(event_context, personas, needs_persona)
        messages      = _build_messages(content, history, system_prompt)

        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type":  "application/json",
        }
        payload = {
            "model":           _GROQ_MODEL,
            "messages":        messages,
            "temperature":     0.75,
            "max_tokens":      1200,
            "response_format": {"type": "json_object"},
        }

        logger.info("Groq request | needs_persona=%s history_len=%d", needs_persona, len(history))

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(_GROQ_CHAT_URL, json=payload, headers=headers)
                response.raise_for_status()
            except httpx.TimeoutException as exc:
                logger.error("Groq timeout after 30s.")
                raise RuntimeError("Groq API timed out") from exc
            except httpx.HTTPStatusError as exc:
                logger.error("Groq HTTP error: %s", exc.response.text)
                raise

        raw_content = ""
        try:
            data = response.json()
            raw_content = data["choices"][0]["message"]["content"]
            clean = raw_content.replace("```json", "").replace("```", "").strip()
            if not clean.startswith("{"):
                m = re.search(r"\{.*\}", clean, re.DOTALL)
                if m:
                    clean = m.group(0)
                    logger.warning("JSON buried in text — extracted.")

            parsed = json.loads(clean)

            # Ensure required fields exist with sane defaults
            if not parsed.get("reply"):
                raise ValueError("Missing or empty 'reply' field in Groq response.")

            parsed.setdefault("needsPersona", needs_persona)
            parsed.setdefault("personaDraft", {
                "name": None, "relationship": None,
                "personality_tags": [], "food_preferences": [],
                "music_preferences": [], "color_preferences": [],
            })
            parsed.setdefault("eventFacts", {
                "date": None, "timezone": None,
                "guestCount": None, "budgetPerHead": None, "expectations": None,
            })
            parsed.setdefault("calendarIntent", {"wantsSync": False, "provider": None})
            parsed.setdefault("missingInfo", [])
            parsed.setdefault("suggestedTasks", [])
            parsed.setdefault("intent", "chat")
            parsed.setdefault("save_persona", False)

            logger.info(
                "Groq success | intent=%s save_persona=%s needsPersona=%s",
                parsed.get("intent"), parsed.get("save_persona"), parsed.get("needsPersona"),
            )
            return parsed

        except Exception as exc:
            logger.error("Groq parse failed: %s | raw: %.300s", exc, raw_content)
            raise RuntimeError(f"Groq response could not be parsed: {exc}") from exc

    # ── Kept for recommendation_service usage (unchanged) ───────────────────
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
            "You are a vendor offering ranking engine for Occacia. "  # nosec B608
            "Rank candidate offerings for the given task. "
            "Return ONLY a JSON object — no explanation, no markdown.\n\n"
            "RANKING CRITERIA:\n"
            "1. Category match\n2. Budget fit\n3. Persona match\n"
            "4. Event context fit\n5. Availability\n\n"
            f"- Select up to {limit} offerings maximum\n"
            "- Prefer offerings from different vendors\n"
            "- Only use offering_ids from CANDIDATE_OFFERINGS\n"
            "- Order best-first\n"
            "- If nothing matches, return empty array\n\n"
            '{"recommended_offering_ids": ["OFF-001"], "reasoning": "one sentence"}'
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
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user",   "content": user_msg},
            ],
            "temperature": 0.1,
            "max_tokens":  512,
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


groq_ai_service = GroqAIService()
