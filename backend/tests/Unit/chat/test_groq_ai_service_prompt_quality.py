from __future__ import annotations

from app.services.groq_ai_service import _build_system_prompt


def _prompt_without_banned_list(prompt: str) -> str:
    lines = prompt.splitlines()
    cleaned: list[str] = []
    in_banned_block = False
    for line in lines:
        if "BANNED PHRASES" in line:
            in_banned_block = True
            cleaned.append(line)
            continue
        if in_banned_block and line.startswith("3. "):
            in_banned_block = False
        if not in_banned_block:
            cleaned.append(line)
    return "\n".join(cleaned)


def test_prompt_never_contains_banned_phrases():
    prompt = _build_system_prompt(event_context={}, personas=[], needs_persona=True)
    sanitized = _prompt_without_banned_list(prompt)
    banned = [
        "Hello! How can I assist you today?",
        "Great! I'd be happy to help!",
        "Certainly! Here's what I recommend:",
        "As an AI event planner",
    ]
    for phrase in banned:
        assert phrase not in sanitized


def test_prompt_contains_one_question_at_a_time_rule():
    prompt = _build_system_prompt(event_context={}, personas=[], needs_persona=True)
    lower = prompt.lower()
    assert "one question" in lower or "one at a time" in lower


def test_prompt_contains_sri_lanka_venues():
    prompt = _build_system_prompt(event_context={}, personas=[], needs_persona=False)
    venues = ["Heritance", "Galle Face", "Mount Lavinia", "Nihonbashi", "Saffron", "Wallawwa", "OZO", "Marino"]
    found = [v for v in venues if v in prompt]
    assert len(found) >= 3


def test_prompt_output_schema_has_reply_not_chat_response():
    prompt = _build_system_prompt(event_context={}, personas=[], needs_persona=True)
    assert '"reply"' in prompt
    assert "chat_response" not in prompt


def test_prompt_output_schema_has_all_required_fields():
    prompt = _build_system_prompt(event_context={}, personas=[], needs_persona=True)
    for field in [
        "needsPersona",
        "personaDraft",
        "eventFacts",
        "calendarIntent",
        "missingInfo",
        "suggestedTasks",
        "intent",
        "save_persona",
    ]:
        assert field in prompt


def test_prompt_output_schema_has_no_gift_fields():
    prompt = _build_system_prompt(event_context={}, personas=[], needs_persona=True)
    assert "gift_suggestion" not in prompt
    assert "gift_category" not in prompt


def test_prompt_mentions_lkr_currency():
    prompt = _build_system_prompt(event_context={}, personas=[], needs_persona=False)
    assert "LKR" in prompt


def test_prompt_mentions_confirm_tasks():
    prompt = _build_system_prompt(event_context={}, personas=[], needs_persona=False)
    assert "Confirm Tasks" in prompt or "confirm tasks" in prompt


def test_needs_persona_true_prompt_asks_about_person_first():
    prompt = _build_system_prompt(event_context={}, personas=[], needs_persona=True)
    lower = prompt.lower()
    assert "name" in lower
    assert "relationship" in lower
    assert "do not ask about budget" in lower


def test_needs_persona_false_prompt_skips_persona_collection():
    prompt = _build_system_prompt(event_context={}, personas=[], needs_persona=False)
    assert "PERSONA COLLECTION MODE" not in prompt
    assert "PLANNING MODE" in prompt or "planning mode" in prompt.lower()
