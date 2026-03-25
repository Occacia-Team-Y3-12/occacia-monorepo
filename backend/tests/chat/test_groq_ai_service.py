from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from tenacity import RetryError

from app.services.groq_ai_service import (
    GroqAIService,
    _build_messages,
    _build_system_prompt,
    groq_ai_service,
)


def _mock_http_response(content_obj: dict | str):
    response = MagicMock()
    response.raise_for_status.return_value = None
    if isinstance(content_obj, str):
        payload = {"choices": [{"message": {"content": content_obj}}]}
    else:
        payload = {"choices": [{"message": {"content": str(content_obj)}}]}
    response.json.return_value = payload
    return response


@pytest.mark.anyio
async def test_plan_event_chat_returns_structured_dict():
    response = _mock_http_response(
        '{"reply":"Hello","intent":"planning","needsPersona":true,"save_persona":false}'
    )
    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=response)):
        result = await groq_ai_service.plan_event_chat(
            content="Plan my event",
            history=[],
            personas=[],
            event_context={},
            needs_persona=True,
        )
    assert isinstance(result, dict)
    assert result["reply"]
    assert "intent" in result
    assert "needsPersona" in result
    assert "save_persona" in result


@pytest.mark.anyio
async def test_plan_event_chat_raises_on_timeout():
    with patch(
        "httpx.AsyncClient.post",
        new=AsyncMock(side_effect=httpx.TimeoutException("timeout")),
    ):
        with pytest.raises(RuntimeError, match="timed out"):
            await groq_ai_service.plan_event_chat(
                content="Plan",
                history=[],
                personas=[],
                event_context={},
                needs_persona=True,
            )


@pytest.mark.anyio
async def test_plan_event_chat_raises_on_empty_reply():
    response = _mock_http_response('{"reply": ""}')
    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=response)):
        with pytest.raises(RuntimeError):
            await groq_ai_service.plan_event_chat(
                content="Plan",
                history=[],
                personas=[],
                event_context={},
                needs_persona=True,
            )


@pytest.mark.anyio
async def test_plan_event_chat_raises_on_missing_reply_field():
    response = _mock_http_response('{"intent":"chat"}')
    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=response)):
        with pytest.raises(RuntimeError):
            await groq_ai_service.plan_event_chat(
                content="Plan",
                history=[],
                personas=[],
                event_context={},
                needs_persona=True,
            )


@pytest.mark.anyio
async def test_plan_event_chat_defaults_missing_optional_fields():
    response = _mock_http_response('{"reply":"Hello"}')
    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=response)):
        result = await groq_ai_service.plan_event_chat(
            content="Plan",
            history=[],
            personas=[],
            event_context={},
            needs_persona=True,
        )
    assert "needsPersona" in result
    assert "personaDraft" in result
    assert "eventFacts" in result
    assert "calendarIntent" in result
    assert result["missingInfo"] == []
    assert result["suggestedTasks"] == []
    assert result["intent"] == "chat"
    assert result["save_persona"] is False


@pytest.mark.anyio
async def test_plan_event_chat_raises_on_invalid_json():
    response = _mock_http_response("not json at all")
    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=response)):
        with pytest.raises(RuntimeError):
            await groq_ai_service.plan_event_chat(
                content="Plan",
                history=[],
                personas=[],
                event_context={},
                needs_persona=True,
            )


@pytest.mark.anyio
async def test_plan_event_chat_raises_on_http_500():
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    response = httpx.Response(500, request=request, text="server error")
    exc = httpx.HTTPStatusError("500", request=request, response=response)
    with patch("httpx.AsyncClient.post", new=AsyncMock(side_effect=exc)):
        with pytest.raises((httpx.HTTPStatusError, RetryError)):
            await groq_ai_service.plan_event_chat(
                content="Plan",
                history=[],
                personas=[],
                event_context={},
                needs_persona=True,
            )


@pytest.mark.anyio
async def test_plan_event_chat_http_401_is_not_retried():
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    response = httpx.Response(401, request=request, text="unauthorized")
    exc = httpx.HTTPStatusError("401", request=request, response=response)
    post_mock = AsyncMock(side_effect=exc)

    with patch("httpx.AsyncClient.post", new=post_mock):
        with pytest.raises(httpx.HTTPStatusError):
            await groq_ai_service.plan_event_chat(
                content="Plan",
                history=[],
                personas=[],
                event_context={},
                needs_persona=True,
            )

    assert post_mock.await_count == 1


def test_system_prompt_contains_persona_collection_when_needs_persona_true():
    prompt = _build_system_prompt(event_context={}, personas=[], needs_persona=True)
    assert "persona" in prompt.lower()
    assert "one question" in prompt.lower()


def test_system_prompt_contains_planning_mode_when_needs_persona_false():
    prompt = _build_system_prompt(event_context={}, personas=[], needs_persona=False)
    lower = prompt.lower()
    assert "planning mode" in lower or "budget" in lower or "guests" in lower


def test_system_prompt_contains_persona_block_when_personas_provided():
    persona = SimpleNamespace(name="Amara", food_preferences=["sushi"])
    prompt = _build_system_prompt(event_context={}, personas=[persona], needs_persona=False)
    assert "Amara" in prompt
    assert "sushi" in prompt


def test_system_prompt_contains_event_context():
    prompt = _build_system_prompt(
        event_context={
            "title": "Birthday Party",
            "event_type": "BIRTHDAY",
            "event_date": "2025-12-25",
        },
        personas=[],
        needs_persona=False,
    )
    assert "Birthday Party" in prompt
    assert "BIRTHDAY" in prompt


def test_build_messages_includes_history():
    history = [
        SimpleNamespace(user_message="u1", ai_message="a1"),
        SimpleNamespace(user_message="u2", ai_message="a2"),
        SimpleNamespace(user_message="u3", ai_message="a3"),
    ]
    messages = _build_messages(content="new message", history=history, system_prompt="system")
    assert len(messages) == 8
    assert messages[0]["role"] == "system"
    assert messages[-1]["role"] == "user"
    assert messages[-1]["content"] == "new message"


def test_build_messages_caps_history_at_10():
    history = [SimpleNamespace(user_message=f"u{i}", ai_message=f"a{i}") for i in range(15)]
    messages = _build_messages(content="new", history=history, system_prompt="system")
    history_messages = messages[1:-1]
    assert len(history_messages) <= 20


@pytest.mark.anyio
async def test_recommend_offerings_for_task_returns_none_when_no_key():
    svc = GroqAIService()
    svc.groq_api_key = None
    result = await svc.recommend_offerings_for_task(
        event_context={},
        personas=[],
        task={},
        offerings=[{"offering_id": "OFF-001"}],
    )
    assert result is None


@pytest.mark.anyio
async def test_recommend_offerings_for_task_returns_none_when_no_offerings():
    svc = GroqAIService()
    svc.groq_api_key = "dummy"
    result = await svc.recommend_offerings_for_task(
        event_context={},
        personas=[],
        task={},
        offerings=[],
    )
    assert result is None
