from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.models.event import Event
from app.models.event_chat_message import EventChatMessage
from app.models.event_persona import EventPersona
from app.models.persona import Persona
from app.models.task import Task


MOCK_GROQ_RESPONSE = {
    "reply": "What's her name and what's her relationship to you?",
    "needsPersona": True,
    "personaDraft": {
        "name": None,
        "relationship": None,
        "personality_tags": [],
        "food_preferences": [],
        "music_preferences": [],
        "color_preferences": [],
    },
    "eventFacts": {
        "date": None,
        "timezone": None,
        "guestCount": None,
        "budgetPerHead": None,
        "expectations": None,
    },
    "calendarIntent": {"wantsSync": False, "provider": None},
    "missingInfo": ["date", "budgetPerHead", "guestCount"],
    "suggestedTasks": [],
    "intent": "chat",
    "save_persona": False,
}


def _create_event(customer_id: str, *, event_type: str = "BIRTHDAY") -> Event:
    db = SessionLocal()
    try:
        event = Event(
            customer_id=customer_id,
            event_type=event_type,
            title=f"{event_type.title()} Event",
            status="DRAFT",
            location_text="Colombo",
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event
    finally:
        db.close()


def _post_chat(auth_client: TestClient, event_id: str, content: str = "I want to plan a birthday"):
    return auth_client.post(
        f"/api/v1/customers/events/{event_id}/chat",
        json={"content": content},
    )


def test_chat_returns_reply(auth_client, active_customer):
    event = _create_event(active_customer.customer_id)
    with patch(
        "app.services.event_chat_service.groq_ai_service.plan_event_chat",
        new=AsyncMock(return_value=MOCK_GROQ_RESPONSE),
    ):
        response = _post_chat(auth_client, event.event_id)

    assert response.status_code == 200
    assert response.json()["reply"]


def test_chat_404_invalid_event(auth_client):
    response = _post_chat(auth_client, "NONEXISTENT")
    assert response.status_code == 404


def test_chat_saves_user_message(auth_client, active_customer):
    event = _create_event(active_customer.customer_id)
    with patch(
        "app.services.event_chat_service.groq_ai_service.plan_event_chat",
        new=AsyncMock(return_value=MOCK_GROQ_RESPONSE),
    ):
        response = _post_chat(auth_client, event.event_id, "Plan a brunch")

    assert response.status_code == 200
    db = SessionLocal()
    try:
        row = (
            db.query(EventChatMessage)
            .filter(
                EventChatMessage.event_id == event.event_id,
                EventChatMessage.sender == "CUSTOMER",
                EventChatMessage.content == "Plan a brunch",
            )
            .first()
        )
        assert row is not None
    finally:
        db.close()


def test_chat_saves_ai_reply(auth_client, active_customer):
    event = _create_event(active_customer.customer_id)
    with patch(
        "app.services.event_chat_service.groq_ai_service.plan_event_chat",
        new=AsyncMock(return_value=MOCK_GROQ_RESPONSE),
    ):
        response = _post_chat(auth_client, event.event_id)

    assert response.status_code == 200
    db = SessionLocal()
    try:
        row = (
            db.query(EventChatMessage)
            .filter(
                EventChatMessage.event_id == event.event_id,
                EventChatMessage.sender == "AI",
            )
            .first()
        )
        assert row is not None
        assert row.content
    finally:
        db.close()


def test_persona_saved_when_name_in_draft(auth_client, active_customer):
    event = _create_event(active_customer.customer_id)
    ai_response = {
        **MOCK_GROQ_RESPONSE,
        "save_persona": True,
        "personaDraft": {
            "name": "Amara",
            "relationship": "Friend",
            "personality_tags": ["fun"],
            "food_preferences": [],
            "music_preferences": [],
            "color_preferences": [],
        },
    }
    with patch(
        "app.services.event_chat_service.groq_ai_service.plan_event_chat",
        new=AsyncMock(return_value=ai_response),
    ):
        response = _post_chat(auth_client, event.event_id)

    assert response.status_code == 200
    db = SessionLocal()
    try:
        persona = (
            db.query(Persona)
            .filter(
                Persona.customer_id == active_customer.customer_id,
                Persona.name == "Amara",
            )
            .first()
        )
        assert persona is not None
        link = (
            db.query(EventPersona)
            .filter(
                EventPersona.event_id == event.event_id,
                EventPersona.persona_id == persona.persona_id,
            )
            .first()
        )
        assert link is not None
    finally:
        db.close()


def test_persona_not_saved_when_no_name(auth_client, active_customer):
    event = _create_event(active_customer.customer_id)
    ai_response = {
        **MOCK_GROQ_RESPONSE,
        "save_persona": True,
        "personaDraft": {
            "name": None,
            "relationship": "Friend",
            "personality_tags": [],
            "food_preferences": [],
            "music_preferences": [],
            "color_preferences": [],
        },
    }
    db = SessionLocal()
    try:
        before_count = db.query(Persona).filter(Persona.customer_id == active_customer.customer_id).count()
    finally:
        db.close()

    with patch(
        "app.services.event_chat_service.groq_ai_service.plan_event_chat",
        new=AsyncMock(return_value=ai_response),
    ):
        response = _post_chat(auth_client, event.event_id)
    assert response.status_code == 200

    db = SessionLocal()
    try:
        after_count = db.query(Persona).filter(Persona.customer_id == active_customer.customer_id).count()
        assert after_count == before_count
    finally:
        db.close()


def test_event_date_updated_when_fact_extracted(auth_client, active_customer):
    event = _create_event(active_customer.customer_id)
    ai_response = {
        **MOCK_GROQ_RESPONSE,
        "eventFacts": {
            "date": "2025-08-15",
            "timezone": "Asia/Colombo",
            "guestCount": None,
            "budgetPerHead": None,
            "expectations": None,
        },
    }
    with patch(
        "app.services.event_chat_service.groq_ai_service.plan_event_chat",
        new=AsyncMock(return_value=ai_response),
    ):
        response = _post_chat(auth_client, event.event_id)
    assert response.status_code == 200

    db = SessionLocal()
    try:
        updated = db.query(Event).filter(Event.event_id == event.event_id).first()
        assert updated is not None
        assert updated.start_at is not None
        assert updated.start_at.date() == datetime.fromisoformat("2025-08-15").date()
    finally:
        db.close()


def test_suggested_tasks_persisted(auth_client, active_customer):
    event = _create_event(active_customer.customer_id)
    ai_response = {
        **MOCK_GROQ_RESPONSE,
        "suggestedTasks": [
            {"name": "Cake", "description": "Order cake", "quantity": 1, "currency": "LKR"},
        ],
    }
    with patch(
        "app.services.event_chat_service.groq_ai_service.plan_event_chat",
        new=AsyncMock(return_value=ai_response),
    ):
        response = _post_chat(auth_client, event.event_id)
    assert response.status_code == 200

    db = SessionLocal()
    try:
        task = (
            db.query(Task)
            .filter(Task.event_id == event.event_id, Task.name == "Cake")
            .first()
        )
        assert task is not None
        assert task.status == "DRAFT"
    finally:
        db.close()


def test_duplicate_tasks_not_created(auth_client, active_customer):
    event = _create_event(active_customer.customer_id)
    db = SessionLocal()
    try:
        db.add(
            Task(
                event_id=event.event_id,
                name="Cake",
                description="Existing task",
                quantity=1,
                currency="LKR",
                status="DRAFT",
            )
        )
        db.commit()
    finally:
        db.close()

    ai_response = {
        **MOCK_GROQ_RESPONSE,
        "suggestedTasks": [
            {"name": "Cake", "description": "Order cake", "quantity": 1, "currency": "LKR"},
        ],
    }
    with patch(
        "app.services.event_chat_service.groq_ai_service.plan_event_chat",
        new=AsyncMock(return_value=ai_response),
    ):
        response = _post_chat(auth_client, event.event_id)
    assert response.status_code == 200

    db = SessionLocal()
    try:
        count = db.query(Task).filter(Task.event_id == event.event_id, Task.name == "Cake").count()
        assert count == 1
    finally:
        db.close()


def test_needs_persona_false_for_group_event(auth_client, active_customer):
    event = _create_event(active_customer.customer_id, event_type="GROUP")
    mocked = AsyncMock(return_value=MOCK_GROQ_RESPONSE)
    with patch("app.services.event_chat_service.groq_ai_service.plan_event_chat", new=mocked):
        response = _post_chat(auth_client, event.event_id)
    assert response.status_code == 200
    assert mocked.await_args.kwargs["needs_persona"] is False


def test_needs_persona_true_when_no_personas(auth_client, active_customer):
    event = _create_event(active_customer.customer_id, event_type="BIRTHDAY")
    mocked = AsyncMock(return_value=MOCK_GROQ_RESPONSE)
    with patch("app.services.event_chat_service.groq_ai_service.plan_event_chat", new=mocked):
        response = _post_chat(auth_client, event.event_id)
    assert response.status_code == 200
    assert mocked.await_args.kwargs["needs_persona"] is True


def test_needs_persona_false_when_persona_exists(auth_client, active_customer):
    event = _create_event(active_customer.customer_id, event_type="BIRTHDAY")
    db = SessionLocal()
    try:
        persona = Persona(
            customer_id=active_customer.customer_id,
            name="Nethmi",
            relationship="Friend",
        )
        db.add(persona)
        db.commit()
        db.refresh(persona)
        db.add(EventPersona(event_id=event.event_id, persona_id=persona.persona_id))
        db.commit()
    finally:
        db.close()

    mocked = AsyncMock(return_value=MOCK_GROQ_RESPONSE)
    with patch("app.services.event_chat_service.groq_ai_service.plan_event_chat", new=mocked):
        response = _post_chat(auth_client, event.event_id)
    assert response.status_code == 200
    assert mocked.await_args.kwargs["needs_persona"] is False


def test_groq_error_returns_fallback_reply(auth_token, active_customer):
    event = _create_event(active_customer.customer_id)
    with TestClient(app, raise_server_exceptions=False) as client:
        client.headers.update({"Authorization": f"Bearer {auth_token}"})
        with patch(
            "app.services.event_chat_service.groq_ai_service.plan_event_chat",
            new=AsyncMock(side_effect=RuntimeError("Groq API timed out")),
        ):
            response = _post_chat(client, event.event_id)

    assert response.status_code == 200
    assert "planning assistant" in response.json()["reply"]


def test_response_has_no_gift_fields(auth_client, active_customer):
    event = _create_event(active_customer.customer_id)
    with patch(
        "app.services.event_chat_service.groq_ai_service.plan_event_chat",
        new=AsyncMock(return_value=MOCK_GROQ_RESPONSE),
    ):
        response = _post_chat(auth_client, event.event_id)
    assert response.status_code == 200
    body = response.json()
    assert "giftSuggestion" not in body
    assert "matchedGifts" not in body
    assert "isAiFallback" not in body
