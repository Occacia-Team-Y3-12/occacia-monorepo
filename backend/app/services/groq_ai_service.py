"""
app/services/groq_ai_service.py

Pure Groq API adapter for Occi — Occacia's event planning AI.

Design principles:
  - Persona = the person the event is being planned FOR (girlfriend, parent, friend, etc.)
  - Server drives the phase; the AI never decides to skip ahead.
  - The AI is given a single, explicit NEXT QUESTION it must ask — no ambiguity.
  - All facts the user volunteers in any message are extracted immediately.
  - missingInfo is computed server-side, never trusted from the model.
  - Tasks are generated only when ALL logistics are confirmed.
  - Exactly 1 offering is matched per task.
  - Temperature 0.65 — warm but disciplined.
"""
from __future__ import annotations

import json
import logging
import os
import re

from app.core.config import settings

logger = logging.getLogger(__name__)

_DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
_JSON_FENCE_RE      = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)

# ── Phase constants ────────────────────────────────────────────────────────────
PHASE_PERSONA_COLLECTION = "persona_collection"
PHASE_EVENT_PURPOSE      = "event_purpose"
PHASE_EVENT_LOGISTICS    = "event_logistics"
PHASE_TASK_GENERATION    = "task_generation"
PHASE_COMPLETE           = "complete"

# ── Persona question queue (asked in this exact order) ────────────────────────
# (field_key, question_template)  — {name} is replaced with persona's name if known
PERSONA_QUESTIONS: list[tuple[str, str]] = [
    ("name_relationship", "Who is this event for? Tell me their name and your relationship "
                          "(e.g. 'my girlfriend Sarah' or 'my mum')."),
    ("age",               "How old is {name}? Or if you know their birthday, feel free to share that!"),
    ("gender",            "What's {name}'s gender? This helps me tailor every detail perfectly."),
    ("personality_tags",  "How would you describe {name}'s personality? "
                          "Are they more introverted or extroverted, and what do they love doing?"),
    ("food_preferences",  "Does {name} have any food preferences or dietary needs I should know about? "
                          "(e.g. vegetarian, loves seafood, allergic to nuts)"),
    ("music_preferences", "What kind of music does {name} enjoy — any favourite genres or artists?"),
    ("color_preferences", "What are {name}'s favourite colours? This'll really help with decoration and theming."),
    ("location",          "Where is {name} based, or where would you like the event to take place?"),
]

# ── Allowed vendor categories ──────────────────────────────────────────────────
_VENDOR_CATEGORIES = [
    "Cakes & Bakery",
    "Catering",
    "Drinks & Bar",
    "Food & Beverage",
    "DJ & Music",
    "Band & Live Music",
    "Photography & Videography",
    "Entertainment",
    "Floral Arrangements",
    "Event Decoration",
    "Decor & Flowers",
    "Venue & Spaces",
    "Transport",
    "Other",
]


# ══════════════════════════════════════════════════════════════════════════════
class GroqAIService:
    def __init__(self):
        self.groq_api_key = settings.GROQ_API_KEY

    async def plan_event_chat(
        self,
        content: str,
        history: list,
        personas: list,
        event_context: dict,
        needs_persona: bool,
        persona_missing_fields: list[str] | None = None,
        current_phase: str | None = None,
    ) -> dict:
        import httpx

        api_key = self.groq_api_key or settings.GROQ_API_KEY
        if not api_key:
            logger.warning("GROQ_API_KEY is not configured; Groq calls will fail.")

        phase = current_phase or _infer_phase(event_context, personas, needs_persona)

        next_persona_q = (
            _next_persona_question(personas=personas, missing_fields=persona_missing_fields or [])
            if phase == PHASE_PERSONA_COLLECTION
            else None
        )

        system_prompt = _build_system_prompt(
            event_context=event_context or {},
            personas=personas or [],
            needs_persona=needs_persona,
            persona_missing_fields=persona_missing_fields or [],
            current_phase=phase,
            next_persona_question=next_persona_q,
        )
        messages = _build_messages(content=content, history=history or [], system_prompt=system_prompt)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model":       _DEFAULT_GROQ_MODEL,
                        "temperature": 0.65,
                        "messages":    messages,
                    },
                )
        except httpx.TimeoutException as exc:
            raise RuntimeError("Groq API timed out") from exc

        resp.raise_for_status()
        payload = resp.json()
        try:
            raw = payload["choices"][0]["message"]["content"]
        except Exception as exc:
            raise RuntimeError("Invalid Groq response format") from exc

        raw = (raw or "").strip()
        if not raw:
            raise RuntimeError("Empty response from Groq")

        model_output = _parse_json_from_content(raw)
        if model_output is None:
            raise RuntimeError("Invalid JSON from Groq")

        # Coerce if reply is missing
        if "reply" not in model_output:
            logger.warning("Groq JSON missing 'reply'. Raw: %s", raw[:300])
            if os.getenv("ALLOW_GROQ_MISSING_REPLY", "false").lower() == "true":
                model_output = _coerce_model_output(model_output, needs_persona, phase)
            if "reply" not in model_output:
                raise RuntimeError("Missing reply field in Groq response")

        reply = (model_output.get("reply") or "").strip()
        if not reply:
            raise RuntimeError("Empty reply from Groq")

        # ── Normalise fields ───────────────────────────────────────────────────
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

        # ── budgetPerHead ──────────────────────────────────────────────────────
        try:
            gc = float(event_facts.get("guestCount") or 0)
            bt = float(event_facts.get("budgetTotal") or 0)
            if gc > 0 and bt > 0:
                event_facts["budgetPerHead"] = round(bt / gc, 2)
        except (TypeError, ValueError):
            pass

        # ── missingInfo (server-side) ──────────────────────────────────────────
        # Only the 4 core logistics fields are tracked here.
        # location and purpose are collected via dedicated phases, not missingInfo.
        ctx   = event_context or {}
        known: set[str] = set()
        if ctx.get("guest_count"):   known.add("guestCount")
        if ctx.get("budget_total"):  known.add("budget")
        if ctx.get("event_date"):    known.add("date")
        if ctx.get("expectations"):  known.add("expectations")

        all_logistics = {"guestCount", "budget", "date", "expectations"}

        return {
            "reply":          reply,
            "intent":         model_output.get("intent") or "chat",
            "phase":          model_output.get("phase") or phase,
            "needsPersona":   model_output.get("needsPersona", needs_persona),
            "save_persona":   model_output.get("save_persona", model_output.get("savePersona", False)),
            "personaDraft":   persona_draft,
            "eventFacts":     event_facts,
            "calendarIntent": calendar_intent,
            "suggestedTasks": suggested_tasks,
            "missingInfo":    sorted(all_logistics - known) if ctx else sorted(all_logistics),
        }

    async def recommend_offerings_for_task(self, event_context, personas, task, offerings, **kwargs):
        if not getattr(self, "groq_api_key", None) or not offerings:
            return None
        return [o["offering_id"] for o in offerings[:1]]


# ── Phase inference ────────────────────────────────────────────────────────────
def _infer_phase(event_context: dict, personas: list, needs_persona: bool) -> str:
    # Only force persona_collection if needs_persona is explicitly True.
    # When needs_persona=False (caller has already decided), respect that decision.
    if needs_persona:
        return PHASE_PERSONA_COLLECTION
    if not personas and needs_persona is not False:
        return PHASE_PERSONA_COLLECTION
    ctx = event_context or {}
    if not ctx.get("event_purpose"):
        return PHASE_EVENT_PURPOSE
    if not all([ctx.get("event_date"), ctx.get("budget_total"), ctx.get("guest_count")]):
        return PHASE_EVENT_LOGISTICS
    if not ctx.get("existing_tasks"):
        return PHASE_TASK_GENERATION
    return PHASE_COMPLETE


def _next_persona_question(
    personas: list,
    missing_fields: list[str],
) -> tuple[str, str] | None:
    """Return the (field_key, question) for the first unanswered persona field."""
    if not missing_fields:
        return None
    missing_set = set(missing_fields)
    for field_key, question in PERSONA_QUESTIONS:
        if field_key == "name_relationship":
            if "name" in missing_set or "relationship" in missing_set:
                return (field_key, question)
        elif field_key in missing_set:
            return (field_key, question)
    return None


def _get_persona_name(personas: list) -> str | None:
    for p in (personas or []):
        n = getattr(p, "name", None)
        if n:
            return n
    return None


# ══════════════════════════════════════════════════════════════════════════════
#  System prompt
# ══════════════════════════════════════════════════════════════════════════════
def _build_system_prompt(
    event_context: dict,
    personas: list,
    needs_persona: bool,
    persona_missing_fields: list[str] | None = None,
    current_phase: str | None = None,
    next_persona_question: tuple[str, str] | None = None,
) -> str:
    # Apply defaults for optional parameters
    if persona_missing_fields is None:
        persona_missing_fields = []
    if current_phase is None:
        current_phase = _infer_phase(event_context or {}, personas or [], needs_persona)
    ctx  = event_context or {}
    name = _get_persona_name(personas) or "them"
    lines: list[str] = []

    # ── Identity block ─────────────────────────────────────────────────────────
    lines += [
        "You are Occi, the warm and brilliant event planning assistant for Occacia.",
        "You help users create meaningful, personalised events for the people they love.",
        "",
        "CORE TRUTH: The PERSONA is the person the event is being planned FOR",
        "(e.g. a girlfriend, parent, best friend). It is NOT the user themselves.",
        "Every question, every task, every recommendation must centre the persona.",
        "",
    ]

    # ── Output contract ────────────────────────────────────────────────────────
    lines += [
        "OUTPUT CONTRACT (MUST follow exactly):",
        "  • Return ONLY one valid JSON object. Zero text outside JSON.",
        "  • No markdown, no code fences, no explanations outside the reply field.",
        "  • Use EXACT field names and casing as in the schema.",
        "  • Use null for unknown scalars, [] for unknown arrays.",
        "  • Capture EVERY fact the user mentions in the correct field — even early answers.",
        "  • NEVER ask two questions in a single reply field.",
        "",
        "SCHEMA:",
        json.dumps({
            "reply":        "Your single warm, focused message to the user",
            "phase":        current_phase,
            "intent":       "chat",
            "needsPersona": needs_persona,
            "save_persona": False,
            "personaDraft": {
                "name": None, "relationship": None, "age": None,
                "gender": None, "birthday": None, "location": None,
                "personality_tags": [], "food_preferences": [],
                "music_preferences": [], "color_preferences": [], "interests": []
            },
            "eventFacts": {
                "purpose": None, "date": None, "timezone": "Asia/Colombo",
                "guestCount": None, "budgetTotal": None,
                "location": None, "expectations": None
            },
            "calendarIntent": {"wantsSync": False, "provider": None},
            "missingInfo": [],
            "suggestedTasks": []
        }, indent=2),
        "",
        "suggestedTasks item (ONLY in task generation phase):",
        json.dumps({
            "name": "Task name", "description": "What this covers",
            "quantity": 1, "currency": "LKR",
            "vendor_category": "<one of the allowed values>"
        }, indent=2),
        f"Allowed vendor_category values: {', '.join(_VENDOR_CATEGORIES)}",
        "",
    ]

    # ── Phase block ────────────────────────────────────────────────────────────
    mode_label = "PERSONA COLLECTION MODE" if current_phase == PHASE_PERSONA_COLLECTION else "PLANNING MODE"
    lines += ["━" * 60, f"CURRENT PHASE: {current_phase.upper()} | {mode_label}", "━" * 60, ""]

    # ──────────────────────────────────────────────────────────────────────────
    if current_phase == PHASE_PERSONA_COLLECTION:

        lines += [
            "PHASE 0 — LEARN ABOUT THE PERSON THIS EVENT IS FOR",
            "",
            "Goal: collect personal details so you can plan the most thoughtful event possible.",
            "",
            "Question order (follow exactly, skip already-answered ones):",
        ]
        for i, (fk, qt) in enumerate(PERSONA_QUESTIONS, 1):
            lines.append(f"  {i}. {qt.replace('{name}', name)}")

        lines += [
            "",
            "STRICT RULES:",
            "  • Ask EXACTLY ONE question per reply — never bundle two.",
            "  • Extract every fact into personaDraft even if the user answers ahead.",
            "  • Do NOT ask about event date, budget, or guest count here.",
            "  • Do not ask about budget, date, or guest count during persona collection.",
            "  • Be genuinely warm — you're learning about someone important to the user.",
            "  • Once you have: name + relationship + age/birthday + 2+ preference fields,",
            "    set save_persona=true and confirm warmly.",
            "",
        ]

        if next_persona_question:
            fk, qt = next_persona_question
            lines += [
                "► YOUR NEXT QUESTION — ask this and ONLY this:",
                f'  "{qt.replace("{name}", name)}"',
                "",
                "Write a warm, natural version of this question in your reply.",
            ]
        elif not persona_missing_fields:
            lines += [
                "► PERSONA IS COMPLETE.",
                "  Set save_persona=true.",
                "  Transition warmly: tell the user you have everything you need",
                "  and you're excited to start planning the occasion.",
            ]

        if personas:
            _append_persona_context(lines, personas)

    # ──────────────────────────────────────────────────────────────────────────
    elif current_phase == PHASE_EVENT_PURPOSE:

        lines += [
            f"PHASE 1 — CLARIFY THE OCCASION FOR {name.upper()}",
            "",
            "You know who the event is for. Now pin down the occasion.",
            "",
            "Common occasions: Birthday · Anniversary · Graduation · Farewell · Wedding ·",
            "Baby Shower · Engagement · Date Night · Promotion · Holiday Party · Surprise Party",
            "",
            "If the event title makes the occasion obvious (contains 'birthday', 'anniversary',",
            "etc.) → set eventFacts.purpose yourself and confirm it with the user warmly,",
            "then ask the first logistics question.",
            "",
            "Otherwise ask: 'What's the occasion — is this a birthday, anniversary,",
            "or something else special for {name}?'".replace("{name}", name),
        ]
        _append_persona_context(lines, personas)

    # ──────────────────────────────────────────────────────────────────────────
    elif current_phase == PHASE_EVENT_LOGISTICS:

        purpose          = ctx.get("event_purpose", "the event")
        missing_logistics = _missing_logistics(ctx)
        next_q           = _next_logistics_question(missing_logistics, name, purpose)

        lines += [
            f"PHASE 2 — COLLECT LOGISTICS FOR {name.upper()}'s {purpose.upper()}",
            "",
            "You need these details. Ask for them ONE AT A TIME in this priority order:",
            "  1. Date            → eventFacts.date (YYYY-MM-DD)",
            "  2. Number of guests → eventFacts.guestCount (integer)",
            "  3. Total budget (LKR) → eventFacts.budgetTotal (number)",
            "  4. Venue/location   → eventFacts.location",
            "  5. Special requests → eventFacts.expectations",
            "",
            "RULES:",
            "  • Ask ONE item per reply.",
            "  • If the user provides multiple at once, capture all and ask the next missing one.",
            "  • Once date + guestCount + budgetTotal are known, you can proceed.",
        ]

        if missing_logistics:
            lines += ["", f"Still missing: {', '.join(missing_logistics)}"]

        if next_q:
            lines += ["", f"► YOUR NEXT QUESTION: \"{next_q}\""]

        _append_persona_context(lines, personas)
        _append_event_context(lines, ctx)

    # ──────────────────────────────────────────────────────────────────────────
    elif current_phase == PHASE_TASK_GENERATION:

        purpose = ctx.get("event_purpose", "the event")
        budget  = ctx.get("budget_total", "unknown")
        guests  = ctx.get("guest_count", "unknown")

        lines += [
            f"PHASE 3 — GENERATE THE EVENT PLAN FOR {name.upper()}",
            "",
            "You have everything. Create EXACTLY 5 tasks tailored to this person and occasion.",
            "",
            "TASK RULES:",
            "  1. Exactly 5 tasks — no more, no fewer.",
            "  2. Each task uses a DIFFERENT vendor_category.",
            "  3. Tailor to the persona — use their preferences, personality, and the occasion:",
        ]

        # Pull persona traits for tailoring hints
        if personas:
            p = personas[0]
            food   = getattr(p, "food_preferences",  None) or []
            music  = getattr(p, "music_preferences",  None) or []
            colors = getattr(p, "color_preferences",  None) or []
            ptags  = getattr(p, "personality_tags",   None) or []

            if food:
                lines.append(f"     → Food prefs ({', '.join(food)}) → pick matching Catering/Food task")
            if music:
                lines.append(f"     → Music taste ({', '.join(music)}) → pick DJ, Band, or Live Music accordingly")
            if colors:
                lines.append(f"     → Fav colours ({', '.join(colors)}) → use in Decoration task")
            if any("introvert" in t.lower() for t in ptags):
                lines.append("     → Introverted personality → prefer intimate venues, not loud clubs")
            elif any("extrovert" in t.lower() for t in ptags):
                lines.append("     → Extroverted personality → lively, social venue is ideal")

        lines += [
            f"  4. Budget is LKR {budget} for ~{guests} guests — keep tasks realistic.",
            "  5. vendor_category must be exactly one of the allowed values.",
            "  6. Write a specific, personal description (not generic filler).",
            "  7. A balanced set typically covers: Venue · Food/Catering · Cake ·",
            "     Decoration · Entertainment or Photography.",
            "",
            "IN YOUR REPLY:",
            f"  - Open: 'Here's the personalised plan I've put together for {name}!'",
            "  - List all 5 tasks with a brief personal reason for each choice.",
            "  - Close with a warm invite to tweak anything.",
            "  - Set intent to 'task_generation'.",
        ]
        _append_persona_context(lines, personas)
        _append_event_context(lines, ctx)

    # ──────────────────────────────────────────────────────────────────────────
    elif current_phase == PHASE_COMPLETE:

        lines += [
            "PHASE 4 — PLANNING COMPLETE",
            "",
            "All details collected, tasks created. Be a helpful planning partner.",
            "  • Help the user Confirm Tasks and finalise the plan.",
            "  • Answer follow-up questions.",
            "  • Suggest refinements (better venue, alternatives).",
            "  • Add new tasks on request (put in suggestedTasks).",
            "  • Help with invitations, messages, timelines.",
            "  • Keep everything personal — reference {name} by name.".replace("{name}", name),
        ]

        _append_persona_context(lines, personas)
        _append_event_context(lines, ctx)

        existing = ctx.get("existing_tasks") or []
        if existing:
            lines += ["", "Current task list:"]
            for t in existing:
                lines.append(f"  ✓ {t}")

    # ── Always show event context if we have it ──────────────────────────────
    if ctx.get("title") or ctx.get("event_purpose") or ctx.get("event_date"):
        _append_event_context(lines, ctx)

    # ── Universal rules ────────────────────────────────────────────────────────
    lines += [
        "",
        "━" * 60,
        "ALWAYS:",
        "  • Address the USER (the planner), never the persona.",
        "  • When tasks exist, help the user review and Confirm Tasks to finalise the plan.",
        f"  • Refer to the persona as '{name}' once known.",
        "  • Warm, personal, enthusiastic tone — this is a special occasion!",
        "  • All currency in LKR (Sri Lankan Rupees).",
        "  • Real Sri Lanka venues: Heritance Kandalama · Galle Face Hotel ·",
        "    Mount Lavinia Hotel · Wallawwa · OZO Colombo · Shangri-La Colombo ·",
        "    Cinnamon Grand · Nihonbashi · Saffron · Marino Mall.",
        "  • NEVER ask two questions in one reply.",
        "  • Capture any volunteered fact in the right JSON field immediately.",
        "  • Never invent facts about the persona.",
    ]

    return "\n".join(lines)


# ── Logistics helpers ──────────────────────────────────────────────────────────
def _missing_logistics(ctx: dict) -> list[str]:
    missing = []
    if not ctx.get("event_date"):   missing.append("date")
    if not ctx.get("guest_count"):  missing.append("guestCount")
    if not ctx.get("budget_total"): missing.append("budgetTotal")
    if not ctx.get("location"):     missing.append("location")
    if not ctx.get("expectations"): missing.append("expectations")
    return missing


def _next_logistics_question(missing: list[str], name: str, purpose: str) -> str | None:
    questions = {
        "date":         f"When are you thinking of holding {name}'s {purpose}? Do you have a date in mind?",
        "guestCount":   f"Roughly how many guests will be celebrating with {name}?",
        "budgetTotal":  "What's your total budget for the event? (in LKR)",
        "location":     "Where would you like to host this — any preferred area or type of venue?",
        "expectations": "Is there anything specific you'd love to include or any must-haves for the event?",
    }
    for field in missing:
        if field in questions:
            return questions[field]
    return None


# ── Context appenders ──────────────────────────────────────────────────────────
def _append_persona_context(lines: list, personas: list) -> None:
    if not personas:
        return
    lines += ["", "━ PERSONA ━"]
    for p in personas:
        for label, attr in [
            ("Name",        "name"),
            ("Relationship","relationship"),
            ("Age",         "age"),
            ("Birthday",    "birthday"),
            ("Gender",      "gender"),
            ("Location",    "location"),
        ]:
            val = getattr(p, attr, None)
            if val:
                lines.append(f"  {label}: {val}")
        for label, attr in [
            ("Personality",  "personality_tags"),
            ("Food prefs",   "food_preferences"),
            ("Music prefs",  "music_preferences"),
            ("Fav colours",  "color_preferences"),
            ("Interests",    "interests"),
        ]:
            items = getattr(p, attr, None) or []
            if items:
                lines.append(f"  {label}: {', '.join(items)}")


def _append_event_context(lines: list, ctx: dict) -> None:
    lines += ["", "━ EVENT CONTEXT ━"]
    for label, key in [
        ("Title",         "title"),
        ("Type",          "event_type"),
        ("Purpose",       "event_purpose"),
        ("Date",          "event_date"),
        ("Location",      "location"),
        ("Guests",        "guest_count"),
        ("Budget (LKR)",  "budget_total"),
        ("Per head",      "budget_per_head"),
        ("Expectations",  "expectations"),
    ]:
        val = ctx.get(key)
        if val:
            lines.append(f"  {label}: {val}")


# ── Message builder ────────────────────────────────────────────────────────────
def _build_messages(content: str, history: list, system_prompt: str) -> list[dict]:
    messages = [{"role": "system", "content": system_prompt}]

    def _get(msg, attr):
        return msg.get(attr, "") if isinstance(msg, dict) else getattr(msg, attr, "")

    recent = [m for m in (history or []) if _get(m, "content").strip()][-10:]
    for msg in recent:
        role = "user" if _get(msg, "sender").upper() == "CUSTOMER" else "assistant"
        text = _get(msg, "content").strip()
        if text:
            messages.append({"role": role, "content": text})

    messages.append({"role": "user", "content": content})
    return messages


# ── Singleton ──────────────────────────────────────────────────────────────────
groq_ai_service = GroqAIService()


# ── JSON parsing ───────────────────────────────────────────────────────────────
def _parse_json_from_content(raw: str) -> dict | None:
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        pass

    m = _JSON_FENCE_RE.search(raw)
    if m:
        try:
            parsed = json.loads(m.group(1))
            return parsed if isinstance(parsed, dict) else None
        except Exception:
            return None

    for candidate in _extract_json_objects(raw):
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict) and "reply" in parsed:
                return parsed
        except Exception:
            continue

    s, e = raw.find("{"), raw.rfind("}")
    if s != -1 and e > s:
        try:
            parsed = json.loads(raw[s:e + 1])
            return parsed if isinstance(parsed, dict) else None
        except Exception:
            pass

    return None


def _extract_json_objects(text: str) -> list[str]:
    objects, depth, start = [], 0, -1
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}" and depth > 0:
            depth -= 1
            if depth == 0 and start != -1:
                objects.append(text[start:i + 1])
                start = -1
    return objects


def _synthesize_reply(model_output: dict, needs_persona: bool, phase: str) -> str:
    if phase == PHASE_PERSONA_COLLECTION:
        return (
            "I'd love to help you plan something truly special! "
            "Let's start — who is this event for? What's their name and your relationship to them?"
        )
    if phase == PHASE_EVENT_PURPOSE:
        return "Great! What's the occasion — is this a birthday, anniversary, or something else?"
    if phase == PHASE_EVENT_LOGISTICS:
        return "Perfect! Let's sort the details. When are you thinking of holding the event?"
    return "I'm here to help — what would you like to work on?"


def _coerce_model_output(model_output: dict, needs_persona: bool, phase: str) -> dict:
    if not isinstance(model_output, dict):
        return {}
    if "suggestedTasks" not in model_output:
        alt = model_output.get("SuggestedTasks")
        if isinstance(alt, list):
            model_output["suggestedTasks"] = [
                {
                    "name":            (t.get("Task") or t.get("name") or "").strip(),
                    "description":     t.get("Description") or t.get("description"),
                    "quantity":        1,
                    "currency":        "LKR",
                    "vendor_category": t.get("vendor_category") or "Other",
                }
                for t in alt if isinstance(t, dict) and (t.get("Task") or t.get("name"))
            ]
    if "reply" not in model_output:
        model_output["reply"] = _synthesize_reply(model_output, needs_persona, phase)
    return model_output

#JUST IN CASE 
