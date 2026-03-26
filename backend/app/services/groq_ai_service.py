"""
app/services/groq_ai_service.py

Pure Groq API adapter for Occi - Occacia's event planning AI.

Design principles:
  - System prompt is the single source of truth for conversation rules.
  - event_context (built from DB) is injected every turn so Occi never guesses.
  - All facts the user mentions in ANY message are extracted immediately.
  - missingInfo is computed server-side (not trusted from the model) to prevent re-asks.
  - Persona collection is Phase 0 for non-GROUP events without a persona.
  - Scheduling (recurrence/reminders/calendar) is intentionally OUT of scope for chat.
  - Temperature 0.72 balances warmth with reliability.
"""
from __future__ import annotations

import json
import logging
import os
import re

from app.core.config import settings

logger = logging.getLogger(__name__)

_DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


class GroqAIService:
    def __init__(self):
        self.groq_api_key = settings.GROQ_API_KEY

    async def plan_event_chat(self, content, history, personas, event_context, needs_persona):
        import httpx

        api_key = self.groq_api_key or settings.GROQ_API_KEY
        if not api_key:
            logger.warning("GROQ_API_KEY is not configured; Groq calls will fail.")

        system_prompt = _build_system_prompt(event_context or {}, personas or [], needs_persona)
        messages = _build_messages(content=content, history=history or [], system_prompt=system_prompt)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}" if api_key else "",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": _DEFAULT_GROQ_MODEL,
                        "temperature": 0.72,
                        "messages": messages,
                        "response_format": {"type": "json_object"},
                    },
                )
        except httpx.TimeoutException as exc:
            raise RuntimeError("Groq API timed out") from exc

        response.raise_for_status()
        payload = response.json()

        usage = payload.get("usage", {})
        total_tokens = usage.get("total_tokens", 0)
        logger.info(
            "Occi AI Call Success | Event: %s | Tokens Used: %s",
            (event_context or {}).get("eventId", "Unknown"),
            total_tokens,
        )

        try:
            raw_content = payload["choices"][0]["message"]["content"]
        except Exception as exc:
            raise RuntimeError("Invalid Groq response format") from exc

        if not raw_content or not str(raw_content).strip():
            raise RuntimeError("Invalid JSON")

        raw_content = str(raw_content).strip()
        model_output = _parse_json_from_content(raw_content)
        if model_output is None:
            raise RuntimeError("Invalid JSON")

        if "reply" not in model_output:
            logger.warning("Groq JSON missing reply field. Raw content: %s", raw_content)
            allow_missing = os.getenv("ALLOW_GROQ_MISSING_REPLY", "false").lower() == "true"
            if allow_missing:
                model_output = _coerce_model_output(model_output, needs_persona)
            if "reply" not in model_output:
                raise RuntimeError("Missing reply field")

        reply = (model_output.get("reply") or "").strip()
        if not reply:
            raise RuntimeError("Empty reply")

        persona_draft = model_output.get("personaDraft")
        if not isinstance(persona_draft, dict):
            persona_draft = {}

        event_facts = model_output.get("eventFacts")
        if not isinstance(event_facts, dict):
            event_facts = {}

        calendar_intent = model_output.get("calendarIntent")
        if not isinstance(calendar_intent, dict):
            calendar_intent = {}

        suggested_tasks = model_output.get("suggestedTasks")
        if not isinstance(suggested_tasks, list):
            suggested_tasks = []
        else:
            suggested_tasks = [t for t in suggested_tasks if isinstance(t, dict)]

        result = {
            "reply": reply,
            "intent": model_output.get("intent") or "chat",
            "needsPersona": model_output.get("needsPersona", needs_persona),
            "save_persona": model_output.get("save_persona", model_output.get("savePersona", False)),
            "personaDraft": persona_draft,
            "eventFacts": event_facts,
            "calendarIntent": calendar_intent,
            "suggestedTasks": suggested_tasks,
        }

        guest_count = event_facts.get("guestCount")
        budget_total = event_facts.get("budgetTotal")
        if guest_count is not None and budget_total is not None:
            try:
                guest_count_val = float(guest_count)
                budget_total_val = float(budget_total)
                if guest_count_val > 0:
                    event_facts["budgetPerHead"] = budget_total_val / guest_count_val
            except (TypeError, ValueError):
                pass

        ctx = event_context or {}
        known = set()
        if ctx.get("guest_count"):
            known.add("guestCount")
        if ctx.get("budget_total") or ctx.get("budget_per_head"):
            known.add("budget")
        if ctx.get("event_date"):
            known.add("date")
        if ctx.get("expectations"):
            known.add("expectations")

        all_facts = {"guestCount", "budget", "date", "expectations"}
        result["missingInfo"] = (
            sorted(list(all_facts - known))
            if ctx
            else ["budget", "date", "expectations", "guestCount"]
        )

        return result

    async def recommend_offerings_for_task(self, event_context, personas, task, offerings, **kwargs):
        if not getattr(self, "groq_api_key", None) or not offerings:
            return None
        return [o["offering_id"] for o in offerings[:3]]


def _build_system_prompt(event_context: dict, personas: list, needs_persona: bool) -> str:
    ctx = event_context or {}
    prompt = []
    prompt.append("Return ONLY a single JSON object. No markdown. No code fences.")
    prompt.append("Use EXACT field names and casing as specified. Do NOT add extra top-level keys.")
    prompt.append("If a value is unknown, use null or empty arrays.")
    prompt.append("If user asks for tasks, you MUST populate suggestedTasks with name, description, quantity, currency.")
    prompt.append("JSON TEMPLATE:")
    prompt.append(
        "{"
        '"reply":"...",'
        '"intent":"chat",'
        '"needsPersona":false,'
        '"save_persona":false,'
        '"personaDraft":{"name":null,"relationship":null,"personality_tags":[],"food_preferences":[],"music_preferences":[],"color_preferences":[]},'
        '"eventFacts":{"date":null,"timezone":null,"guestCount":null,"budgetTotal":null,"budgetPerHead":null,"expectations":null},'
        '"calendarIntent":{"wantsSync":false,"provider":null},'
        '"missingInfo":[],'
        '"suggestedTasks":[{"name":"Cake","description":"Order cake","quantity":1,"currency":"LKR"}]'
        "}"
    )

    if ctx.get("title"):
        prompt.append(f"Event: {ctx['title']}")
    if ctx.get("event_type"):
        prompt.append(f"Type: {ctx['event_type']}")
    if ctx.get("event_date"):
        prompt.append(f"Date: {ctx['event_date']}")
    if ctx.get("budget_total"):
        prompt.append(f"Budget: LKR {ctx['budget_total']}")
    if ctx.get("expectations"):
        prompt.append(f"Expectations: {ctx['expectations']}")

    if personas:
        for p in personas:
            name = getattr(p, "name", None) or "Someone"
            food = getattr(p, "food_preferences", None) or []
            music = getattr(p, "music_preferences", None) or []
            traits = getattr(p, "personality_tags", None) or []
            prompt.append(
                "Persona: "
                f"{name} | Traits: {', '.join(traits)} | Food: {', '.join(food)} | Music: {', '.join(music)}"
            )

    venues = [
        "Heritance",
        "Galle Face",
        "Mount Lavinia",
        "Nihonbashi",
        "Saffron",
        "Wallawwa",
        "OZO",
        "Marino",
    ]
    prompt.append("Sri Lanka venues: " + ", ".join(venues[:4]))

    if needs_persona:
        prompt.append("PHASE 0 PERSONA COLLECTION: Ask ONE question to get name and relationship.")
        prompt.append("Do not ask about budget until persona is collected.")
    else:
        prompt.append("PLANNING MODE: Confirm Tasks and ask ONE lightweight planning question if needed.")

    prompt.append('"reply": "..."')
    prompt.append("LKR")
    return "\n".join(prompt)


def _build_messages(content: str, history: list, system_prompt: str) -> list[dict]:
    messages = [{"role": "system", "content": system_prompt}]

    def _get_msg_attr(msg, attr):
        if isinstance(msg, dict):
            return msg.get(attr, "")
        return getattr(msg, attr, "")

    filtered = [m for m in (history or []) if _get_msg_attr(m, "content").strip()]
    filtered = filtered[-10:]
    for msg in filtered:
        sender = _get_msg_attr(msg, "sender").upper()
        text = _get_msg_attr(msg, "content").strip()
        if not text:
            continue
        if sender == "CUSTOMER":
            messages.append({"role": "user", "content": text})
        elif sender == "AI":
            messages.append({"role": "assistant", "content": text})

    safe_content = content.strip()[:1500]
    messages.append({"role": "user", "content": safe_content})
    return messages


def _parse_json_from_content(raw_content: str) -> dict | None:
    try:
        parsed = json.loads(raw_content)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        pass

    fenced = _JSON_FENCE_RE.search(raw_content)
    if fenced:
        try:
            parsed = json.loads(fenced.group(1))
            return parsed if isinstance(parsed, dict) else None
        except Exception:
            return None

    candidates = _extract_json_objects(raw_content)
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict) and "reply" in parsed:
                return parsed
        except Exception:
            continue

    start = raw_content.find("{")
    end = raw_content.rfind("}")
    if start != -1 and end != -1 and end > start:
        snippet = raw_content[start : end + 1]
        try:
            parsed = json.loads(snippet)
            return parsed if isinstance(parsed, dict) else None
        except Exception:
            return None

    return None


def _extract_json_objects(text: str) -> list[str]:
    objects: list[str] = []
    depth = 0
    start = -1
    for idx, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = idx
            depth += 1
        elif ch == "}":
            if depth > 0:
                depth -= 1
                if depth == 0 and start != -1:
                    objects.append(text[start : idx + 1])
                    start = -1
    return objects


def _synthesize_reply(model_output: dict, needs_persona: bool) -> str:
    next_step = model_output.get("nextStep")
    if isinstance(next_step, str) and next_step.strip():
        return next_step.strip()
    if needs_persona:
        return "Please share the person's name and relationship so I can personalize the plan."
    return "Got it. What date are you targeting and what budget range should I plan for?"


def _coerce_model_output(model_output: dict, needs_persona: bool) -> dict:
    if not isinstance(model_output, dict):
        return {}

    if "suggestedTasks" not in model_output:
        alt_tasks = model_output.get("SuggestedTasks")
        if isinstance(alt_tasks, list):
            coerced: list[dict] = []
            for item in alt_tasks:
                if not isinstance(item, dict):
                    continue
                name = item.get("Task") or item.get("name")
                if not isinstance(name, str) or not name.strip():
                    continue
                coerced.append(
                    {
                        "name": name.strip(),
                        "description": item.get("Description") or item.get("description"),
                        "quantity": 1,
                        "currency": "LKR",
                    }
                )
            model_output["suggestedTasks"] = coerced

    if "reply" not in model_output:
        model_output["reply"] = _synthesize_reply(model_output, needs_persona)

    return model_output


groq_ai_service = GroqAIService()
