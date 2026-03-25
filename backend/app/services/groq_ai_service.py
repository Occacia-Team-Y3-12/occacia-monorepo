"""
app/services/groq_ai_service.py

Pure Groq API adapter for Occi — Occacia's event planning AI.

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
import re
from typing import Any, Optional

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from app.core.config import settings

logger = logging.getLogger(__name__)

_GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
_GROQ_MODEL    = "llama-3.3-70b-versatile"
_MAX_HISTORY   = 14   # ~7 turns of context


def _is_retryable(exc: BaseException) -> bool:
    if not isinstance(exc, httpx.HTTPStatusError):
        return False
    return exc.response.status_code == 429 or exc.response.status_code >= 500


# ─────────────────────────────────────────────────────────────────────────────
# Prompt block builders
# ─────────────────────────────────────────────────────────────────────────────

def _persona_block(personas: list) -> str:
    """Build a rich recipient profile block from linked personas."""
    if not personas:
        return ""

    def _list(val) -> list[str]:
        if not val:
            return []
        if isinstance(val, list):
            return [str(v).strip() for v in val if v]
        return [s.strip() for s in str(val).split(",") if s.strip()]

    blocks: list[str] = []
    for p in personas:
        name   = getattr(p, "name",             "Unknown") or "Unknown"
        rel    = getattr(p, "relationship",     "") or ""
        food   = _list(getattr(p, "food_preferences",  None))
        music  = _list(getattr(p, "music_preferences", None))
        tags   = _list(getattr(p, "personality_tags",  None))
        colors = _list(getattr(p, "color_preferences", None))
        bday   = getattr(p, "birthday", None)

        lines = [f"Name         : {name}"]
        if rel:    lines.append(f"Relationship : {rel}")
        if bday:   lines.append(f"Birthday     : {bday}")
        if tags:   lines.append(f"Vibe/Tags    : {', '.join(tags)}")
        if food:   lines.append(f"Food likes   : {', '.join(food)}")
        if music:  lines.append(f"Music likes  : {', '.join(music)}")
        if colors: lines.append(f"Colours      : {', '.join(colors)}")
        blocks.append("\n".join(lines))

    return (
        "╔══════════════════════════════════════╗\n"
        "  RECIPIENT PROFILE\n"
        "  Use this to shape ALL suggestions.\n"
        "╚══════════════════════════════════════╝\n"
        + "\n\n".join(blocks)
        + "\n\n"
    )


def _confirmed_facts_block(ctx: dict) -> str:
    """
    Render only the facts that are genuinely known (non-null/non-empty).
    Occi must treat every line here as FINAL — never re-ask for these.
    """
    parts: list[str] = []
    if ctx.get("title"):
        parts.append(f"Event title    : {ctx['title']}")
    if ctx.get("event_type"):
        parts.append(f"Event type     : {ctx['event_type']}")
    if ctx.get("event_date"):
        parts.append(f"Date           : {ctx['event_date']}")
    if ctx.get("location"):
        parts.append(f"Location       : {ctx['location']}")
    if ctx.get("guest_count"):
        parts.append(f"Guest count    : {ctx['guest_count']}")
    if ctx.get("budget_total"):
        parts.append(f"Total budget   : LKR {ctx['budget_total']}")
    if ctx.get("budget_per_head"):
        parts.append(f"Budget/head    : LKR {ctx['budget_per_head']}")
    if ctx.get("expectations"):
        parts.append(f"Expectations   : {ctx['expectations']}")
    if ctx.get("existing_tasks"):
        parts.append(f"Tasks created  : {', '.join(ctx['existing_tasks'])}")

    if not parts:
        return ""

    return (
        "╔══════════════════════════════════════╗\n"
        "  CONFIRMED FACTS — NEVER RE-ASK THESE\n"
        "╚══════════════════════════════════════╝\n"
        + "\n".join(parts)
        + "\n\n"
    )


def _missing_facts_block(ctx: dict) -> str:
    """
    Compute exactly what is still unknown. Occi asks these ONE AT A TIME.
    This is the authoritative queue — ignore any internal guess from the model.
    """
    missing: list[str] = []

    if not ctx.get("guest_count"):
        missing.append('guest_count   → ask: "How many people are joining?"')
    if not ctx.get("budget_total") and not ctx.get("budget_per_head"):
        missing.append('budget        → ask: "What\'s the budget — total or per person? (LKR)"')
    if not ctx.get("event_date"):
        missing.append('date          → ask: "When is this happening?"')
    if not ctx.get("expectations"):
        missing.append('expectations  → ask: "What kind of vibe or experience are you going for?"')

    if not missing:
        return (
            "╔══════════════════════════════════════╗\n"
            "  ALL 4 FACTS KNOWN\n"
            "  → Trigger Phase 2: show summary + tasks, then ask for confirm.\n"
            "╚══════════════════════════════════════╝\n\n"
        )

    return (
        "╔══════════════════════════════════════╗\n"
        "  STILL MISSING — ask ONE at a time, in this order:\n"
        "╚══════════════════════════════════════╝\n"
        + "\n".join(f"  {i+1}. {item}" for i, item in enumerate(missing))
        + "\n\n"
    )


def _task_suggestions_for_type(event_type: str, title: str) -> str:
    """
    Return a curated task list hint based on event type + title keywords.
    Occi uses this to populate suggestedTasks in the Phase 2 summary.
    """
    text = f"{event_type} {title}".lower()

    task_map = {
        "birthday":    ["Cake & desserts", "Venue / location", "Decorations", "Guest invitations", "Entertainment / activities"],
        "wedding":     ["Venue booking", "Catering & menu", "Photography & video", "Flowers & décor", "Invitations & stationery"],
        "anniversary": ["Special venue / restaurant", "Gift", "Flowers", "Surprise element", "Transportation"],
        "proposal":    ["Proposal venue", "Engagement ring", "Discreet photographer", "Flowers / bouquet", "Celebration dinner"],
        "graduation":  ["Venue", "Graduation cake", "Guest invitations", "Graduation gift", "Photography"],
        "baby shower": ["Venue & décor", "Invitations", "Food & themed cake", "Games & activities", "Gift registry"],
        "corporate":   ["Event venue", "Catering", "AV & tech setup", "Event agenda", "Invitations"],
        "dinner":      ["Restaurant reservation", "Menu / dietary notes", "Flowers or gift", "Transportation"],
        "retreat":     ["Accommodation", "Group transport", "Activities & team-building", "Meals & catering"],
        "meeting":     ["Agenda preparation", "Attendee confirmations", "Presentation materials", "Venue / video call link"],
    }

    for keyword, tasks in task_map.items():
        if keyword in text:
            return "Suggested tasks for this event type:\n" + "\n".join(f"  • {t}" for t in tasks)

    return (
        "Suggested tasks (generic):\n"
        "  • Venue / location\n"
        "  • Catering / food\n"
        "  • Guest list & invitations\n"
        "  • Budget planning\n"
        "  • Transport arrangements"
    )


def _build_system_prompt(
    event_context: Optional[dict],
    personas: list,
    needs_persona: bool,
) -> str:
    ctx            = event_context or {}
    confirmed_block = _confirmed_facts_block(ctx)
    missing_block   = _missing_facts_block(ctx)
    persona_block   = _persona_block(personas) if personas else ""
    task_hint       = _task_suggestions_for_type(
        ctx.get("event_type", ""), ctx.get("title", "")
    )

    event_type_upper = ctx.get("event_type", "").upper()

    # ── Persona instruction ───────────────────────────────────────────────────
    if event_type_upper == "GROUP":
        persona_section = (
            "PERSONA NOTE — GROUP EVENT:\n"
            "  • Do NOT ask 'who is this for?' or any persona questions unprompted.\n"
            "  • If the user mentions a person (name, preferences), extract silently into personaDraft.\n"
            "  • Skip Phase 0 entirely — jump straight to planning facts.\n\n"
        )
    elif needs_persona:
        persona_section = (
            "PHASE 0 — PERSONA COLLECTION (do this FIRST, before any event facts):\n"
            "  You don't have a profile for the person this event is for yet.\n"
            "  Collect in this exact order, ONE question per reply:\n"
            "    Step 1 → Ask their name naturally. E.g.: 'Who's the star of this event? 😊'\n"
            "    Step 2 → Ask your relationship to them. E.g.: 'And how do you know them?'\n"
            "  Rules:\n"
            "    • Once you have a NAME → set save_persona=true.\n"
            "    • Tell the user: 'Perfect, I've saved [Name]'s profile! Now let's plan the event.'\n"
            "    • Then move to Phase 1 (planning facts). Do NOT ask food/music/colour\n"
            "      preferences unless the user volunteers them naturally.\n"
            "    • If the user gives you a name AND other persona details in one message,\n"
            "      extract all of them immediately and move on.\n\n"
        )
    else:
        persona_section = (
            "PERSONA NOTE:\n"
            "  Persona already saved. Do NOT ask any persona questions. Move directly\n"
            "  to planning facts or the next phase.\n\n"
        )

    # ── All-facts-known flag ──────────────────────────────────────────────────
    all_known = (
        ctx.get("guest_count")
        and (ctx.get("budget_total") or ctx.get("budget_per_head"))
        and ctx.get("event_date")
        and ctx.get("expectations")
    )
    phase_directive = ""
    if all_known:
        phase_directive = (
            "⚡ PHASE DIRECTIVE: All 4 planning facts are confirmed.\n"
            "Your NEXT reply MUST be the Phase 2 summary message.\n"
            "Format it exactly as shown in the PLANNING FLOW section below.\n"
            "Include the suggested tasks list in that same message.\n\n"
        )

    return f"""You are Occi — the AI planning brain behind Occacia, Sri Lanka's go-to event platform.

Your personality:
  • Casual, warm, a little witty — like a smart friend who plans great events.
  • You know Sri Lanka well: venues, culture, vibes, pricing in LKR.
  • You use emojis occasionally — not every sentence, just when it feels natural.
  • You acknowledge emotions. If someone says "it's for my mum's 60th", you feel that.
  • You never sound like a corporate chatbot. Ever.

{confirmed_block}{missing_block}{persona_block}{persona_section}{phase_directive}
══════════════════════════════════════════════
ABSOLUTE RULES — NEVER BREAK THESE
══════════════════════════════════════════════

R1. CONFIRMED FACTS block = final truth. Never re-ask for anything listed there.
    If it's in that block, you already have it. Move on.

R2. STILL MISSING block = your only queue. Ask items from it ONE AT A TIME.
    If the block says 0 items missing → you are in Phase 2, not Phase 1.

R3. Multi-fact messages: if the user gives you several facts at once
    ("20 guests, LKR 50k, December 15"), extract ALL of them in eventFacts
    right now. Do NOT ask "how many guests?" after they just told you.

R4. History awareness: scan the full conversation history before every reply.
    If a fact appears anywhere in history → treat it as KNOWN. Do not re-ask.

R5. ONE question per reply. Never stack two planning questions.
    "What's your budget, and how many guests?" → BANNED.

R6. Banned openers (instant failure):
    - "Hello! How can I assist you today?"
    - "Great! I'd be happy to help!"
    - "Certainly! Here's what I recommend:"
    - "As an AI language model..."
    - Any opener that ignores what the user just said.

R7. React first. If the user shares something meaningful (a birthday, an anniversary,
    a loved one), acknowledge it warmly BEFORE asking anything.

R8. Off-topic questions: answer briefly and naturally, then continue planning
    in the same reply.

R9. Currency: always LKR. Parse shorthands: 10k=10000, 50k=50000, 1.5m=1500000.
    "LKR 2000 for 2 people" → budgetTotal=2000, budgetPerHead=1000.

R10. Scheduling (recurrence, reminders, calendar sync) is handled in the app UI.
     Do NOT ask about these in chat.

══════════════════════════════════════════════
PLANNING FLOW (phases — follow strictly)
══════════════════════════════════════════════

PHASE 0 — Persona (non-GROUP, needs_persona=true only):
  Collect name → relationship, ONE question at a time.
  Save persona when name is captured. Then proceed to Phase 1.

PHASE 1 — Collect 4 planning facts (skip any already in CONFIRMED FACTS):
  Ask in this order, ONE at a time:
    1. Guest count
    2. Budget (total or per head, LKR)
    3. Date
    4. Expectations / vibe

PHASE 2 — All 4 facts known → show summary + tasks in ONE message:
  Use this EXACT format (adapt values):

  "Here's what I've got so far 🎉

   📅 Date     : [date]
   👥 Guests   : [N] people
   💰 Budget   : LKR [total] (~LKR [per_head]/head)
   ✨ Vibe     : [expectations]

   Here are some tasks to kick things off:
   • [Task 1]
   • [Task 2]
   • [Task 3]
   • [Task 4]
   • [Task 5]

   Ready for me to find you some great options in Sri Lanka? 🙌"

  Wait for user to confirm before giving recommendations.
  Set intent="confirm" in this reply.

{task_hint}

PHASE 3 — User confirms → give EXACTLY 3 Sri Lanka recommendations:
  Rules:
    • Name REAL places — no made-up venues.
    • Include estimated LKR price per head for each.
    • Cover different budget tiers / vibes.
    • Format: Name → vibe tag → price → 1-sentence why it fits.
  Real Sri Lanka venues to draw from (use others if appropriate):
    Heritance Ahungalla, Galle Face Hotel, Saffron, Nihonbashi Colombo,
    Mount Lavinia Hotel, Colombo Rowing Club, The Long Bar at Galle Face,
    Marino Beach Colombo, OZO Colombo, Wallawwa, The Gallery Cafe,
    Smoke & Bitters, Cinnamon Grand Colombo, The Kingsbury Colombo,
    Aditya Resort Negombo, Heaven's Edge Kandy, Brief Garden Beruwela,
    Cape Weligama, Earl's Regency Kandy, Clique by Cinnamon,
    The Cricket Club Cafe, Nuga Gama at Cinnamon Grand,
    Park Street Mews, Tintagel Colombo, Mandarina by Cinnamon.
  Set intent="recommend" in this reply.

PHASE 4 — User wants changes:
  Ask what to tweak, re-recommend with updated options.

PHASE 5 — User selects:
  Tell them: "Tap 'Confirm Tasks & View Recommendations' to lock this in! 🎯"

══════════════════════════════════════════════
PERSONA EXTRACTION (every turn, silently)
══════════════════════════════════════════════
Whenever the user mentions ANYTHING about the recipient — name, food, music,
hobbies, personality, colours, relationship — extract it into personaDraft.
Even passing mentions count. Never wait for "enough" data.

══════════════════════════════════════════════
TONE EXAMPLES
══════════════════════════════════════════════
✓ "Oh, your mum's 60th — that's a big deal! 🎂 How many people are you thinking?"
✓ "Nice, LKR 50k for 15 gives us about LKR 3,333/head — that's a solid Colombo budget."
✓ "Got it! And what kind of vibe are you going for — fancy sit-down, garden party, beach?"
✓ "October's actually a great time in Sri Lanka ☀️ When exactly in October?"
✗ "Great choice! I will now proceed to collect your budget information."
✗ "How many guests will be attending the event today?"
✗ "As your AI event planning assistant, I recommend the following options:"

══════════════════════════════════════════════
OUTPUT — raw JSON ONLY. No markdown fences.
Must start with {{ and end with }}.
══════════════════════════════════════════════
{{
  "reply": "REQUIRED. Warm, specific, reacts to what user said. Never a template.",
  "intent": "chat | planning | confirm | recommend",
  "needsPersona": false,
  "save_persona": false,
  "personaDraft": {{
    "name": null,
    "relationship": null,
    "personality_tags": [],
    "food_preferences": [],
    "music_preferences": [],
    "color_preferences": []
  }},
  "eventFacts": {{
    "date": "YYYY-MM-DD or null",
    "timezone": "Asia/Colombo",
    "location": null,
    "guestCount": null,
    "budgetTotal": null,
    "budgetPerHead": null,
    "expectations": null
  }},
  "missingInfo": [],
  "suggestedTasks": [
    {{"name": "string", "description": "string or null", "quantity": 1, "currency": "LKR"}}
  ],
  "calendarIntent": {{"wantsSync": false, "provider": null}}
}}

JSON RULES:
• reply: must be warm, casual, conversation-specific. If the user gave you data,
  confirm it naturally ("Nice, 15 guests — got it!") before asking the next question.
• intent: "planning" while collecting facts, "confirm" at Phase 2 summary,
  "recommend" when giving venue options, "chat" for everything else.
• eventFacts: populate ALL facts the user mentioned in THIS message.
  If user said "20 guests, 50k, October 15" → guestCount=20, budgetTotal=50000, date="2026-10-15".
  Compute budgetPerHead = budgetTotal / guestCount automatically when both known.
• missingInfo: list only keys NOT yet in CONFIRMED FACTS. Valid keys:
  "guestCount", "budget", "date", "expectations"
• suggestedTasks: populate during Phase 2 (all facts known). Use the event type
  and title to pick relevant tasks — 4 to 6 tasks, specific to this event.
• save_persona: true only when you have captured the recipient's name.
• personaDraft: fill incrementally — any mention of the recipient counts."""


def _build_messages(content: str, history: list, system_prompt: str) -> list[dict]:
    """
    Build the Groq messages array.
    EventChatMessage has: sender ("CUSTOMER"|"AI"), content, sent_at.
    History arrives oldest-first from event_chat_service.
    """
    messages = [{"role": "system", "content": system_prompt}]

    for msg in (history[-_MAX_HISTORY:] if history else []):
        sender = getattr(msg, "sender", "").upper()
        text   = (getattr(msg, "content", "") or "").strip()
        if not text:
            continue
        if sender == "CUSTOMER":
            messages.append({"role": "user",      "content": text})
        elif sender == "AI":
            messages.append({"role": "assistant", "content": text})

    messages.append({"role": "user", "content": content})
    return messages


# ─────────────────────────────────────────────────────────────────────────────
# Server-side missingInfo computation (never trust model's own list)
# ─────────────────────────────────────────────────────────────────────────────

def _compute_missing(ctx: dict, ef: dict) -> list[str]:
    """
    Authoritative missing-info list computed from DB context + current turn facts.
    This prevents the model from hallucinating re-asks.
    """
    missing: list[str] = []

    guest_known = ctx.get("guest_count") or ef.get("guestCount")
    if not guest_known:
        missing.append("guestCount")

    budget_known = (
        ctx.get("budget_total") or ctx.get("budget_per_head")
        or ef.get("budgetTotal") or ef.get("budgetPerHead")
    )
    if not budget_known:
        missing.append("budget")

    date_known = ctx.get("event_date") or ef.get("date")
    if not date_known:
        missing.append("date")

    expectations_known = ctx.get("expectations") or ef.get("expectations")
    if not expectations_known:
        missing.append("expectations")

    return missing


# ─────────────────────────────────────────────────────────────────────────────
# Service
# ─────────────────────────────────────────────────────────────────────────────

class GroqAIService:

    def __init__(self):
        self.groq_api_key: str | None = getattr(settings, "GROQ_API_KEY", None)
        if not self.groq_api_key:
            logger.warning("GROQ_API_KEY not set — event chat AI will fail.")

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=2, max=5),
        retry=retry_if_exception(_is_retryable),
    )
    async def plan_event_chat(
        self,
        content: str,
        history: list,
        personas: list,
        event_context: Optional[dict],
        needs_persona: bool,
    ) -> dict[str, Any]:
        ctx           = event_context or {}
        system_prompt = _build_system_prompt(ctx, personas, needs_persona)
        messages      = _build_messages(content, history, system_prompt)

        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type":  "application/json",
        }
        payload = {
            "model":           _GROQ_MODEL,
            "messages":        messages,
            "temperature":     0.72,
            "max_tokens":      1500,
            "response_format": {"type": "json_object"},
        }

        logger.info(
            "Groq request | needs_persona=%s history=%d missing=%s",
            needs_persona, len(history),
            [k for k, v in ctx.items() if not v],
        )

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.post(_GROQ_CHAT_URL, json=payload, headers=headers)
                resp.raise_for_status()
            except httpx.TimeoutException as exc:
                logger.error("Groq timeout after 30s.")
                raise RuntimeError("Groq API timed out") from exc
            except httpx.HTTPStatusError as exc:
                logger.error("Groq HTTP %s: %s", exc.response.status_code, exc.response.text[:300])
                raise

        raw = ""
        try:
            data = resp.json()
            raw  = data["choices"][0]["message"]["content"]
            clean = raw.replace("```json", "").replace("```", "").strip()

            if not clean.startswith("{"):
                m = re.search(r"\{.*\}", clean, re.DOTALL)
                if m:
                    clean = m.group(0)
                    logger.warning("Extracted JSON from mixed-text Groq response.")

            parsed = json.loads(clean)

            if not parsed.get("reply"):
                raise ValueError("'reply' field is missing or empty.")

            # ── Defaults ──────────────────────────────────────────────────────
            parsed.setdefault("intent",        "chat")
            parsed.setdefault("needsPersona",  needs_persona)
            parsed.setdefault("save_persona",  False)
            parsed.setdefault("suggestedTasks", [])
            parsed.setdefault("calendarIntent", {"wantsSync": False, "provider": None})
            parsed.setdefault("personaDraft", {
                "name": None, "relationship": None,
                "personality_tags": [], "food_preferences": [],
                "music_preferences": [], "color_preferences": [],
            })

            ef = parsed.setdefault("eventFacts", {})
            ef.setdefault("date",          None)
            ef.setdefault("timezone",      "Asia/Colombo")
            ef.setdefault("location",      None)
            ef.setdefault("guestCount",    None)
            ef.setdefault("budgetTotal",   None)
            ef.setdefault("budgetPerHead", None)
            ef.setdefault("expectations",  None)

            # Auto-compute budgetPerHead
            if ef.get("budgetTotal") and ef.get("guestCount") and not ef.get("budgetPerHead"):
                try:
                    ef["budgetPerHead"] = round(
                        float(ef["budgetTotal"]) / float(ef["guestCount"]), 2
                    )
                except (TypeError, ZeroDivisionError):
                    pass

            # ── Override missingInfo with server-authoritative list ────────────
            # Never trust the model's self-reported missingInfo.
            parsed["missingInfo"] = _compute_missing(ctx, ef)

            # ── Validate suggestedTasks structure ─────────────────────────────
            clean_tasks = []
            for t in parsed.get("suggestedTasks") or []:
                if isinstance(t, dict) and t.get("name", "").strip():
                    clean_tasks.append({
                        "name":        t["name"].strip(),
                        "description": t.get("description"),
                        "quantity":    int(t.get("quantity") or 1),
                        "currency":    t.get("currency", "LKR"),
                    })
            parsed["suggestedTasks"] = clean_tasks

            logger.info(
                "Groq OK | intent=%s save_persona=%s missing=%s tasks=%d",
                parsed.get("intent"),
                parsed.get("save_persona"),
                parsed["missingInfo"],
                len(parsed["suggestedTasks"]),
            )
            return parsed

        except Exception as exc:
            logger.error("Groq parse error: %s | raw: %.400s", exc, raw)
            raise RuntimeError(f"Groq response unparseable: {exc}") from exc

    # ── Offering ranking ──────────────────────────────────────────────────────

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
            "You are a vendor offering ranking engine for Occacia, Sri Lanka. "
            "Rank candidate offerings for the given task. "
            "Return ONLY a JSON object — no explanation, no markdown.\n\n"
            "RANKING CRITERIA (in priority order):\n"
            "  1. Category match to the task\n"
            "  2. Budget fit (prefer offerings within event budget)\n"
            "  3. Persona preference match (food, music, colour, vibe)\n"
            "  4. Event context fit (type, expectations, guest count)\n"
            "  5. Quality tier suitability\n\n"
            f"Select up to {limit} offerings. Prefer different vendors.\n"
            "Only use offering_ids from CANDIDATE_OFFERINGS. Order best-first.\n"
            "Return empty array if nothing fits.\n\n"
            '{"recommended_offering_ids": ["OFF-001"], "reasoning": "one sentence"}'
        )
        user_msg = "\n".join([
            f"EVENT_CONTEXT: {json.dumps(event_context, ensure_ascii=True)}",
            f"PERSONAS: {json.dumps(personas, ensure_ascii=True)}",
            f"TASK: {json.dumps(task, ensure_ascii=True)}",
            f"CANDIDATE_OFFERINGS: {json.dumps(offerings, ensure_ascii=True)}",
        ])

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
            result     = resp.json()
            raw        = result["choices"][0]["message"]["content"]
            parsed     = json.loads(raw)
            ids        = parsed.get("recommended_offering_ids") or []
            valid_ids  = {o["offering_id"] for o in offerings}
            shortlist: list[str] = []
            seen:      set[str]  = set()
            for oid in ids:
                if oid in valid_ids and oid not in seen:
                    shortlist.append(oid)
                    seen.add(oid)
                if len(shortlist) == limit:
                    break
            return shortlist or None
        except Exception as exc:
            logger.warning("Offering ranking failed: %s", exc)
            return None


groq_ai_service = GroqAIService()