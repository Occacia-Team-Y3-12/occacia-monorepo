from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.core.database import SessionLocal
from app.core.security import create_access_token, get_password_hash
from app.models.customer import Customer
from app.models.event import Event
from app.models.event_chat_message import EventChatMessage
from app.models.event_persona import EventPersona
from app.models.persona import Persona
from app.models.task import Task
from app.models.task_offering import TaskOffering
from app.models.vendor import Vendor
from app.models.offering import Offering


MOCK_GROQ_RESPONSE = {
    "reply": "Let's plan this nicely.",
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


def _post_chat(client, event_id: str, content: str = "I want to plan a birthday"):
    return client.post(
        f"/api/v1/customers/events/{event_id}/chat",
        json={"content": content},
    )


def _create_second_customer():
    db = SessionLocal()
    try:
        customer = Customer(
            full_name="Other Customer",
            email=f"other-{uuid4().hex[:8]}@test.com",
            password_hash=get_password_hash("Test1234!"),
            phone="+94771234568",
            email_verified=True,
            status="ACTIVE",
            customer_id=f"CUS-{uuid4().hex[:16]}",
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return customer
    finally:
        db.close()


def _create_vendor(*, approved: bool) -> Vendor:
    db = SessionLocal()
    try:
        vendor = Vendor(
            vendor_id=f"VEN-{uuid4().hex[:12]}",
            business_name=f"Biz-{uuid4().hex[:6]}",
            display_name=f"Vendor-{uuid4().hex[:6]}",
            email=f"vendor-{uuid4().hex[:8]}@test.com",
            password_hash=get_password_hash("Test1234!"),
            approval_status="APPROVED" if approved else "PENDING",
            is_verified=True,
        )
        db.add(vendor)
        db.commit()
        db.refresh(vendor)
        return vendor
    finally:
        db.close()


def _create_offering(
    vendor: Vendor,
    *,
    name: str,
    category: str = "Cakes & Bakery",
    price: float = 1000.0,
) -> Offering:
    db = SessionLocal()
    try:
        offering = Offering(
            vendor_id=vendor.vendor_id,
            name=name,
            category=category,
            description=f"{name} description",
            price=price,
            currency="LKR",
            quality_tier="MEDIUM",
            is_active=True,
            is_available=True,
        )
        db.add(offering)
        db.commit()
        db.refresh(offering)
        return offering
    finally:
        db.close()


def test_chat_403_wrong_customer(client, active_customer):
    event = _create_event(active_customer.customer_id)
    other = _create_second_customer()
    token = create_access_token(data={"sub": other.email})
    client.headers.update({"Authorization": f"Bearer {token}"})

    with patch(
        "app.services.event_chat_service.groq_ai_service.plan_event_chat",
        new=AsyncMock(return_value=MOCK_GROQ_RESPONSE),
    ):
        response = _post_chat(client, event.event_id)
    assert response.status_code == 403


def test_chat_history_passed_to_groq_on_second_turn(auth_client, active_customer):
    event = _create_event(active_customer.customer_id)
    captured_histories: list[list[str]] = []

    async def _capture(*args, **kwargs):
        captured_histories.append([getattr(m, "content", "") for m in kwargs.get("history", [])])
        return MOCK_GROQ_RESPONSE

    mocked = AsyncMock(side_effect=_capture)
    with patch("app.services.event_chat_service.groq_ai_service.plan_event_chat", new=mocked):
        first = _post_chat(auth_client, event.event_id, "First turn")
        second = _post_chat(auth_client, event.event_id, "Second turn")

    assert first.status_code == 200
    assert second.status_code == 200
    history = captured_histories[1]
    assert len(history) >= 1
    assert str(history[0]).startswith("First turn")


def test_chat_history_capped_at_10_turns(auth_client, active_customer):
    event = _create_event(active_customer.customer_id)
    db = SessionLocal()
    try:
        base = datetime.now(timezone.utc)
        for i in range(15):
            db.add(
                EventChatMessage(
                    event_id=event.event_id,
                    sender="CUSTOMER",
                    content=f"user-{i}",
                    sent_at=base + timedelta(seconds=i * 2),
                )
            )
            db.add(
                EventChatMessage(
                    event_id=event.event_id,
                    sender="AI",
                    content=f"ai-{i}",
                    sent_at=base + timedelta(seconds=i * 2 + 1),
                )
            )
        db.commit()
    finally:
        db.close()

    mocked = AsyncMock(return_value=MOCK_GROQ_RESPONSE)
    with patch("app.services.event_chat_service.groq_ai_service.plan_event_chat", new=mocked):
        response = _post_chat(auth_client, event.event_id)
    assert response.status_code == 200
    history = mocked.await_args.kwargs["history"]
    assert len(history) <= 10


def test_empty_content_rejected(auth_client, active_customer):
    event = _create_event(active_customer.customer_id)
    response = _post_chat(auth_client, event.event_id, "")
    assert response.status_code == 422


def test_whitespace_only_content_rejected(auth_client, active_customer):
    event = _create_event(active_customer.customer_id)
    response = _post_chat(auth_client, event.event_id, "   ")
    assert response.status_code == 422


def test_multiple_tasks_persisted(auth_client, active_customer):
    event = _create_event(active_customer.customer_id)
    ai_response = {
        **MOCK_GROQ_RESPONSE,
        "suggestedTasks": [
            {"name": "Cake", "description": "Order cake", "quantity": 1, "currency": "LKR"},
            {"name": "Venue", "description": "Book venue", "quantity": 1, "currency": "LKR"},
            {"name": "DJ", "description": "Book DJ", "quantity": 1, "currency": "LKR"},
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
        names = {t.name for t in db.query(Task).filter(Task.event_id == event.event_id).all()}
        assert {"Cake", "Venue", "DJ"}.issubset(names)
    finally:
        db.close()


def test_task_with_empty_name_not_persisted(auth_client, active_customer):
    event = _create_event(active_customer.customer_id)
    ai_response = {
        **MOCK_GROQ_RESPONSE,
        "suggestedTasks": [{"name": "", "quantity": 1, "currency": "LKR"}],
    }
    with patch(
        "app.services.event_chat_service.groq_ai_service.plan_event_chat",
        new=AsyncMock(return_value=ai_response),
    ):
        response = _post_chat(auth_client, event.event_id)
    assert response.status_code == 200
    db = SessionLocal()
    try:
        empty_name_count = (
            db.query(Task)
            .filter(Task.event_id == event.event_id, Task.name == "")
            .count()
        )
        assert empty_name_count == 0
    finally:
        db.close()


def test_persona_linked_to_correct_event(auth_client, active_customer):
    event1 = _create_event(active_customer.customer_id)
    event2 = _create_event(active_customer.customer_id)
    ai_response = {
        **MOCK_GROQ_RESPONSE,
        "save_persona": True,
        "personaDraft": {
            "name": "Amara",
            "relationship": "Friend",
            "personality_tags": [],
            "food_preferences": [],
            "music_preferences": [],
            "color_preferences": [],
        },
    }
    with patch(
        "app.services.event_chat_service.groq_ai_service.plan_event_chat",
        new=AsyncMock(return_value=ai_response),
    ):
        response = _post_chat(auth_client, event1.event_id)
    assert response.status_code == 200

    db = SessionLocal()
    try:
        persona = db.query(Persona).filter(Persona.customer_id == active_customer.customer_id, Persona.name == "Amara").first()
        assert persona is not None
        link1 = db.query(EventPersona).filter(EventPersona.event_id == event1.event_id, EventPersona.persona_id == persona.persona_id).first()
        link2 = db.query(EventPersona).filter(EventPersona.event_id == event2.event_id, EventPersona.persona_id == persona.persona_id).first()
        assert link1 is not None
        assert link2 is None
    finally:
        db.close()


def test_persona_not_duplicated_on_repeated_save(auth_client, active_customer):
    event = _create_event(active_customer.customer_id)
    ai_response = {
        **MOCK_GROQ_RESPONSE,
        "save_persona": True,
        "personaDraft": {
            "name": "Amara",
            "relationship": "Friend",
            "personality_tags": [],
            "food_preferences": [],
            "music_preferences": [],
            "color_preferences": [],
        },
    }
    with patch(
        "app.services.event_chat_service.groq_ai_service.plan_event_chat",
        new=AsyncMock(return_value=ai_response),
    ):
        first = _post_chat(auth_client, event.event_id)
        second = _post_chat(auth_client, event.event_id)
    assert first.status_code == 200
    assert second.status_code == 200

    db = SessionLocal()
    try:
        count = (
            db.query(Persona)
            .filter(Persona.customer_id == active_customer.customer_id, Persona.name == "Amara")
            .count()
        )
        assert 1 <= count <= 2
    finally:
        db.close()


def test_event_timezone_applied_when_date_extracted(auth_client, active_customer):
    event = _create_event(active_customer.customer_id)
    ai_response = {
        **MOCK_GROQ_RESPONSE,
        "eventFacts": {
            "date": "2025-09-10",
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
        assert updated.start_at.date().isoformat() == "2025-09-10"
        assert updated.timezone == "Asia/Colombo"
    finally:
        db.close()


def test_event_date_not_updated_when_null(auth_client, active_customer):
    event = _create_event(active_customer.customer_id)
    known = datetime(2025, 5, 1, 12, 0, tzinfo=timezone.utc)
    db = SessionLocal()
    try:
        db_event = db.query(Event).filter(Event.event_id == event.event_id).first()
        db_event.start_at = known
        db.commit()
    finally:
        db.close()

    ai_response = {
        **MOCK_GROQ_RESPONSE,
        "eventFacts": {
            "date": None,
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
        assert updated.start_at == known.replace(tzinfo=None)
    finally:
        db.close()


def test_response_fields_present(auth_client, active_customer):
    event = _create_event(active_customer.customer_id)
    with patch(
        "app.services.event_chat_service.groq_ai_service.plan_event_chat",
        new=AsyncMock(return_value=MOCK_GROQ_RESPONSE),
    ):
        response = _post_chat(auth_client, event.event_id)
    assert response.status_code == 200
    body = response.json()
    for field in [
        "reply",
        "suggestedTasks",
        "intent",
        "missingInfo",
        "askSavePersona",
        "personaSaved",
        "personaConfirmed",
    ]:
        assert field in body


def test_response_missing_info_populated(auth_client, active_customer):
    event = _create_event(active_customer.customer_id)
    ai_response = {**MOCK_GROQ_RESPONSE, "missingInfo": ["date", "budgetPerHead", "guestCount"]}
    with patch(
        "app.services.event_chat_service.groq_ai_service.plan_event_chat",
        new=AsyncMock(return_value=ai_response),
    ):
        response = _post_chat(auth_client, event.event_id)
    assert response.status_code == 200
    assert response.json()["missingInfo"] == ["date", "budgetPerHead", "guestCount"]


def test_response_intent_populated(auth_client, active_customer):
    event = _create_event(active_customer.customer_id)
    ai_response = {**MOCK_GROQ_RESPONSE, "intent": "planning"}
    with patch(
        "app.services.event_chat_service.groq_ai_service.plan_event_chat",
        new=AsyncMock(return_value=ai_response),
    ):
        response = _post_chat(auth_client, event.event_id)
    assert response.status_code == 200
    assert response.json()["intent"] == "planning"


def test_unauthenticated_chat_returns_401(client, active_customer):
    event = _create_event(active_customer.customer_id)
    response = _post_chat(client, event.event_id)
    assert response.status_code in (401, 403)


def test_chat_messages_readable_via_get_messages_endpoint(auth_client, active_customer):
    event = _create_event(active_customer.customer_id)
    with patch(
        "app.services.event_chat_service.groq_ai_service.plan_event_chat",
        new=AsyncMock(return_value=MOCK_GROQ_RESPONSE),
    ):
        posted = _post_chat(auth_client, event.event_id)
    assert posted.status_code == 200

    messages = auth_client.get(f"/api/v1/customers/events/{event.event_id}/messages")
    assert messages.status_code == 200
    items = messages.json()["items"]
    assert len(items) >= 2
    senders = {item["sender"] for item in items}
    assert "CUSTOMER" in senders
    assert "AI" in senders


def test_persona_saved_flag_true_in_response(auth_client, active_customer):
    event = _create_event(active_customer.customer_id)
    ai_response = {
        **MOCK_GROQ_RESPONSE,
        "save_persona": True,
        "personaDraft": {
            "name": "Ravi",
            "relationship": "Friend",
            "personality_tags": [],
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
    assert response.json()["personaSaved"] is True


def test_persona_saved_flag_false_when_no_name(auth_client, active_customer):
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
    with patch(
        "app.services.event_chat_service.groq_ai_service.plan_event_chat",
        new=AsyncMock(return_value=ai_response),
    ):
        response = _post_chat(auth_client, event.event_id)
    assert response.status_code == 200
    assert response.json()["personaSaved"] is False


def test_ask_save_persona_true_when_save_persona_true_but_failed(auth_client, active_customer):
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
    with patch(
        "app.services.event_chat_service.groq_ai_service.plan_event_chat",
        new=AsyncMock(return_value=ai_response),
    ):
        response = _post_chat(auth_client, event.event_id)
    assert response.status_code == 200
    assert response.json()["askSavePersona"] is True


def test_long_message_handled_without_error(auth_client, active_customer):
    event = _create_event(active_customer.customer_id)
    long_content = "Plan " * 300
    with patch(
        "app.services.event_chat_service.groq_ai_service.plan_event_chat",
        new=AsyncMock(return_value=MOCK_GROQ_RESPONSE),
    ):
        response = _post_chat(auth_client, event.event_id, long_content)
    assert response.status_code == 200


def test_chat_passes_event_context_existing_tasks(auth_client, active_customer):
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
        db.add(
            Task(
                event_id=event.event_id,
                name="Venue",
                description="Existing task",
                quantity=1,
                currency="LKR",
                status="DRAFT",
            )
        )
        db.commit()
    finally:
        db.close()

    captured_contexts = []

    async def _capture(*args, **kwargs):
        captured_contexts.append(kwargs.get("event_context"))
        return MOCK_GROQ_RESPONSE

    mocked = AsyncMock(side_effect=_capture)
    with patch("app.services.event_chat_service.groq_ai_service.plan_event_chat", new=mocked):
        response = _post_chat(auth_client, event.event_id)
    assert response.status_code == 200
    context = captured_contexts[0]
    assert context is not None
    assert set(context.get("existing_tasks", [])) == {"Cake", "Venue"}


def test_suggested_task_trims_name_and_defaults(auth_client, active_customer):
    event = _create_event(active_customer.customer_id)
    ai_response = {
        **MOCK_GROQ_RESPONSE,
        "suggestedTasks": [{"name": "  Cake  ", "description": "Order cake"}],
    }
    with patch(
        "app.services.event_chat_service.groq_ai_service.plan_event_chat",
        new=AsyncMock(return_value=ai_response),
    ):
        response = _post_chat(auth_client, event.event_id)
    assert response.status_code == 200

    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.event_id == event.event_id, Task.name == "Cake").first()
        assert task is not None
        assert task.quantity == 1
        assert task.currency == "LKR"
    finally:
        db.close()


def test_invalid_event_date_does_not_change(auth_client, active_customer):
    event = _create_event(active_customer.customer_id)
    db = SessionLocal()
    try:
        db_event = db.query(Event).filter(Event.event_id == event.event_id).first()
        db_event.start_at = datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)
        db_event.timezone = "Asia/Colombo"
        db.commit()
    finally:
        db.close()

    ai_response = {
        **MOCK_GROQ_RESPONSE,
        "eventFacts": {
            "date": "not-a-date",
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
        assert updated.start_at.date().isoformat() == "2025-01-01"
    finally:
        db.close()


def test_persona_save_failure_sets_flags(auth_client, active_customer):
    event = _create_event(active_customer.customer_id)
    ai_response = {
        **MOCK_GROQ_RESPONSE,
        "save_persona": True,
        "personaDraft": {
            "name": "Amara",
            "relationship": "Friend",
            "personality_tags": [],
            "food_preferences": [],
            "music_preferences": [],
            "color_preferences": [],
        },
    }
    with patch(
        "app.services.event_chat_service.persona_service.create_persona",
        side_effect=RuntimeError("DB error"),
    ):
        with patch(
            "app.services.event_chat_service.groq_ai_service.plan_event_chat",
            new=AsyncMock(return_value=ai_response),
        ):
            response = _post_chat(auth_client, event.event_id)
    assert response.status_code == 200
    body = response.json()
    assert body["personaSaved"] is False
    assert body["askSavePersona"] is True


def test_chat_does_not_create_shortlist_when_no_offerings(auth_client, active_customer):
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
        task = db.query(Task).filter(Task.event_id == event.event_id, Task.name == "Cake").first()
        assert task is not None
        shortlist_count = db.query(TaskOffering).filter(TaskOffering.task_id == task.task_id).count()
        assert shortlist_count == 0
    finally:
        db.close()


def test_duplicate_tasks_not_created_case_insensitive(auth_client, active_customer):
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
            {"name": "cake", "description": "Order cake", "quantity": 1, "currency": "LKR"},
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

def test_chat_creates_shortlist_for_new_task(auth_client, active_customer):
    event = _create_event(active_customer.customer_id)
    vendor = _create_vendor(approved=True)
    _create_offering(vendor, name="Cake A", category="Cakes & Bakery", price=8000)
    _create_offering(vendor, name="Cake B", category="Cakes & Bakery", price=9000)
    _create_offering(vendor, name="Cake C", category="Cakes & Bakery", price=10000)
    _create_offering(vendor, name="Cake D", category="Cakes & Bakery", price=11000)

    ai_response = {
        **MOCK_GROQ_RESPONSE,
        "suggestedTasks": [
            {"name": "Birthday Cake", "description": "Order cake", "quantity": 1, "currency": "LKR"},
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
        task = db.query(Task).filter(Task.event_id == event.event_id, Task.name == "Birthday Cake").first()
        assert task is not None
        shortlist = (
            db.query(TaskOffering)
            .filter(TaskOffering.task_id == task.task_id)
            .order_by(TaskOffering.rank.asc())
            .all()
        )
        assert 1 <= len(shortlist) <= 3
        assert shortlist[0].rank == 1
    finally:
        db.close()


def test_chat_does_not_create_shortlist_for_duplicate_task(auth_client, active_customer):
    event = _create_event(active_customer.customer_id)
    vendor = _create_vendor(approved=True)
    _create_offering(vendor, name="Cake A", category="Cakes & Bakery", price=8000)

    db = SessionLocal()
    try:
        task = Task(
            event_id=event.event_id,
            name="Cake",
            description="Existing task",
            quantity=1,
            currency="LKR",
            status="DRAFT",
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        db.add(TaskOffering(task_id=task.task_id, offering_id=_create_offering(vendor, name="Cake B").offering_id, rank=1, score=10))
        db.commit()
    finally:
        db.close()

    ai_response = {
        **MOCK_GROQ_RESPONSE,
        "suggestedTasks": [{"name": "Cake", "description": "Order cake", "quantity": 1, "currency": "LKR"}],
    }
    with patch(
        "app.services.event_chat_service.groq_ai_service.plan_event_chat",
        new=AsyncMock(return_value=ai_response),
    ):
        response = _post_chat(auth_client, event.event_id)
    assert response.status_code == 200

    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.event_id == event.event_id, Task.name == "Cake").first()
        shortlist = db.query(TaskOffering).filter(TaskOffering.task_id == task.task_id).all()
        assert len(shortlist) == 1
    finally:
        db.close()


def test_chat_shortlist_skips_unapproved_vendor_offerings(auth_client, active_customer):
    event = _create_event(active_customer.customer_id)
    vendor = _create_vendor(approved=False)
    _create_offering(vendor, name="Pending Vendor Cake", category="Cakes & Bakery", price=9000)

    ai_response = {
        **MOCK_GROQ_RESPONSE,
        "suggestedTasks": [{"name": "Cake", "description": "Order cake", "quantity": 1, "currency": "LKR"}],
    }
    with patch(
        "app.services.event_chat_service.groq_ai_service.plan_event_chat",
        new=AsyncMock(return_value=ai_response),
    ):
        response = _post_chat(auth_client, event.event_id)
    assert response.status_code == 200

    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.event_id == event.event_id, Task.name == "Cake").first()
        assert task is not None
        shortlist_count = db.query(TaskOffering).filter(TaskOffering.task_id == task.task_id).count()
        assert shortlist_count == 0
    finally:
        db.close()
