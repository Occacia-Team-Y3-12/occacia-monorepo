"""
tests/Integration/test_chat_merged.py

Verifies the merged POST /customers/events/{eventId}/chat endpoint:
- event_planning_service always runs (DB writes, message persistence, suggested tasks)
- planning_service runs and its AI reply wins
- When planning_service fails, falls back to rule-based reply
- Extended ChatSendResponse fields are present in the response
- session_id == event_id (confirmed architecture)
"""
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.database import SessionLocal
from app.models.event_chat_message import EventChatMessage


def _create_event(auth_client, title: str = "Merged Chat Test") -> str:
    r = auth_client.post(
        "/api/v1/customers/events",
        json={"eventType": "Birthday", "title": title},
    )
    assert r.status_code == 201, r.text
    return r.json()["eventId"]


def _chat(auth_client, event_id: str, content: str = "I want to plan a birthday"):
    return auth_client.post(
        f"/api/v1/customers/events/{event_id}/chat",
        json={"content": content},
    )


MOCK_PLAN_RESPONSE_FIELDS = {
    "intent": "planning",
    "chat_response": "Here is the AI reply.",
    "venue_tags": ["romantic"],
    "missing_info": ["location"],
    "gift_suggestion": None,
    "event_type": "birthday",
    "location": None,
    "budget_per_head": 500.0,
    "guest_count": 5,
    "save_persona": None,
    "ask_save_persona": False,
    "use_persona_name": None,
    "reasoning": "AI decided this.",
    "personality_profile": None,
    "venue_match_tier": 2,
    "matched_venues": [],
    "persona_saved": False,
    "persona_confirmed": False,
}


class TestChatEndpointMerged:

    def test_chat_returns_200(self, auth_client):
        event_id = _create_event(auth_client)
        r = _chat(auth_client, event_id)
        assert r.status_code == 200

    def test_chat_response_has_spec_fields(self, auth_client):
        """reply and suggestedTasks are always present (spec-required fields)."""
        event_id = _create_event(auth_client)
        r = _chat(auth_client, event_id)
        body = r.json()
        assert "reply" in body
        assert "suggestedTasks" in body
        assert isinstance(body["suggestedTasks"], list)

    def test_chat_response_has_extended_fields(self, auth_client):
        """Extended planning fields are present (may be null/empty but must exist)."""
        event_id = _create_event(auth_client)
        r = _chat(auth_client, event_id)
        body = r.json()
        for field in (
            "intent", "matchedVenues", "venueTags", "missingInfo",
            "askSavePersona", "personaSaved", "personaConfirmed",
        ):
            assert field in body, f"Extended field '{field}' missing from response"

    def test_ai_reply_wins_over_rule_based_reply(self, auth_client):
        """When planning_service succeeds, its chat_response is used as reply."""
        event_id = _create_event(auth_client)
        ai_reply = "This is the definitive AI reply."
        with patch(
            "app.routers.v1.customer_router.planning_service.process_plan",
            new_callable=AsyncMock,
        ) as mock_plan:
            from app.schemas.planning_schema import PlanResponse
            mock_plan.return_value = PlanResponse(
                intent="chat",
                chat_response=ai_reply,
                venue_tags=[],
                missing_info=[],
            )
            r = _chat(auth_client, event_id, "Hello")
        assert r.status_code == 200
        assert r.json()["reply"] == ai_reply

    def test_fallback_to_rule_reply_when_planning_service_fails(self, auth_client):
        """When planning_service raises, reply comes from event_planning_service."""
        event_id = _create_event(auth_client)
        with patch(
            "app.routers.v1.customer_router.planning_service.process_plan",
            new_callable=AsyncMock,
            side_effect=Exception("AI service down"),
        ):
            r = _chat(auth_client, event_id, "Hello")
        assert r.status_code == 200
        body = r.json()
        assert body["reply"]  # rule-based reply is never empty

    def test_fallback_response_still_has_all_fields(self, auth_client):
        """Even on fallback, extended fields are present with safe defaults."""
        event_id = _create_event(auth_client)
        with patch(
            "app.routers.v1.customer_router.planning_service.process_plan",
            new_callable=AsyncMock,
            side_effect=Exception("AI down"),
        ):
            r = _chat(auth_client, event_id, "Hello")
        body = r.json()
        assert body.get("matchedVenues") == []
        assert body.get("venueTags") == []
        assert body.get("missingInfo") == []
        assert body.get("askSavePersona") is False
        assert body.get("personaSaved") is False
        assert body.get("personaConfirmed") is False

    def test_messages_persisted_to_db(self, auth_client):
        """event_planning_service always saves CUSTOMER + AI messages."""
        event_id = _create_event(auth_client)
        _chat(auth_client, event_id, "Test message persistence")
        db = SessionLocal()
        try:
            msgs = (
                db.query(EventChatMessage)
                .filter(EventChatMessage.event_id == event_id)
                .order_by(EventChatMessage.sent_at)
                .all()
            )
        finally:
            db.close()
        assert len(msgs) == 2
        assert msgs[0].sender == "CUSTOMER"
        assert msgs[1].sender == "AI"

    def test_messages_readable_via_get_messages_endpoint(self, auth_client):
        """After chatting, GET /messages returns both CUSTOMER and AI messages."""
        event_id = _create_event(auth_client)
        _chat(auth_client, event_id, "Check message list")
        r = auth_client.get(f"/api/v1/customers/events/{event_id}/messages")
        assert r.status_code == 200
        senders = [m["sender"] for m in r.json()["items"]]
        assert "CUSTOMER" in senders
        assert "AI" in senders

    def test_event_id_used_as_session_id(self, auth_client):
        """planning_service.process_plan is called with session_id == event_id."""
        event_id = _create_event(auth_client)
        captured = {}
        original = __import__(
            "app.services.planning_service", fromlist=["planning_service"]
        ).planning_service.process_plan

        async def capture_process_plan(*args, **kwargs):
            captured["session_id"] = kwargs.get("session_id")
            from app.schemas.planning_schema import PlanResponse
            return PlanResponse(intent="chat", chat_response="ok", venue_tags=[], missing_info=[])

        with patch(
            "app.routers.v1.customer_router.planning_service.process_plan",
            side_effect=capture_process_plan,
        ):
            _chat(auth_client, event_id, "test session_id binding")

        assert captured.get("session_id") == event_id

    def test_suggested_tasks_come_from_event_planning_service(self, auth_client):
        """suggestedTasks are template-driven from event_planning_service."""
        event_id = _create_event(auth_client)  # Birthday event
        r = _chat(auth_client, event_id, "Help me plan")
        body = r.json()
        assert isinstance(body["suggestedTasks"], list)
        task_names = [t.get("name", "") for t in body["suggestedTasks"]]
        # Birthday template includes Cake, Decorations, Guest invitations
        assert any(name for name in task_names)

    def test_chat_nonexistent_event_returns_404(self, auth_client):
        r = _chat(auth_client, "EVT-doesnotexist", "Hello")
        assert r.status_code == 404

    def test_chat_returns_planning_intent_fields(self, auth_client):
        """Planning-specific fields flow through from planning_service."""
        event_id = _create_event(auth_client)
        with patch(
            "app.routers.v1.customer_router.planning_service.process_plan",
            new_callable=AsyncMock,
        ) as mock_plan:
            from app.schemas.planning_schema import PlanResponse
            mock_plan.return_value = PlanResponse(
                intent="planning",
                chat_response="Found venues!",
                venue_tags=["romantic", "luxury"],
                missing_info=["date"],
                event_type="dinner",
                location="Colombo",
                budget_per_head=200.0,
                guest_count=4,
                venue_match_tier=1,
            )
            r = _chat(auth_client, event_id, "Romantic dinner for 4")
        body = r.json()
        assert body["intent"] == "planning"
        assert body["venueTags"] == ["romantic", "luxury"]
        assert body["missingInfo"] == ["date"]
        assert body["eventType"] == "dinner"
        assert body["location"] == "Colombo"
        assert body["budgetPerHead"] == 200.0
        assert body["guestCount"] == 4
        assert body["venueMatchTier"] == 1

    def test_chat_returns_persona_flags(self, auth_client):
        """Persona flow flags from planning_service are forwarded."""
        event_id = _create_event(auth_client)
        with patch(
            "app.routers.v1.customer_router.planning_service.process_plan",
            new_callable=AsyncMock,
        ) as mock_plan:
            from app.schemas.planning_schema import PlanResponse
            mock_plan.return_value = PlanResponse(
                intent="chat",
                chat_response="Should I save Sarah?",
                venue_tags=[],
                missing_info=[],
                ask_save_persona=True,
                persona_saved=False,
                persona_confirmed=False,
            )
            r = _chat(auth_client, event_id, "Plan for Sarah")
        body = r.json()
        assert body["askSavePersona"] is True
        assert body["personaSaved"] is False
        assert body["personaConfirmed"] is False
