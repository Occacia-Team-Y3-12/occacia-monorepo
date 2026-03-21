"""
tests/Integration/test_ai_service.py  (fixed)

Changes from original:
  - test_tag_block_injected_into_prompt: use _build_prompt() instead of
    intercepting input_value (old Langflow wire format, gone).
  - test_no_tags_means_no_tag_block: same.
  - test_missing_info_injected_into_prompt: use _build_prompt() instead of
    intercepting input_value.
  - test_planning_endpoint_passes_tags_to_ai: capture_gen accepts **kwargs.
  - test_all_tags_passed_to_ai_exist_in_db: capture_gen accepts **kwargs.
  - test_missing_info_carried_across_turns: turn1/turn2 accept **kwargs.
  Everything else unchanged.
"""
import hashlib
import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.database import SessionLocal
from app.models.notification import Notification
from app.services.notification_service import (
    NOTIFICATION_STATUS_QUEUED,
    PASSWORD_RESET_NOTIFICATION,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _uid() -> str:
    return uuid4().hex[:8]


PLAN_URL = "/api/v1/planning/generate"  # retired — use _chat() helper
AUTH_URL = "/api/v1/auth/customer"


def _create_event(auth_client, title="AI Service Test") -> str:
    r = auth_client.post(
        "/api/v1/customers/events",
        json={"eventType": "Birthday", "title": title},
    )
    assert r.status_code == 201, r.text
    return r.json()["eventId"]


def _chat(auth_client, event_id: str, message: str = "Plan a romantic dinner"):
    return auth_client.post(
        f"/api/v1/customers/events/{event_id}/chat",
        json={"content": message},
    )


def _plan_payload(message: str = "Plan a romantic dinner", session_id: str = None) -> dict:
    return {
        "session_id": session_id or f"sess-{_uid()}",
        "user_query":  message,
    }


def _fake_ai(
    intent: str = "date",
    tags: list = None,
    missing: list = None,
    chat_response: str = "Here is your plan.",
    gift: str = None,
) -> dict:
    return {
        "intent":              intent,
        "venue_tags":          tags if tags is not None else ["romantic"],
        "budget_per_head":     150,
        "guest_count":         2,
        "chat_response":       chat_response,
        "missing_info":        missing if missing is not None else [],
        "gift_suggestion":     gift,
        "reasoning":           None,
        "personality_profile": None,
        "event_type":          None,
        "location":            None,
        "save_persona":        None,
        "ask_save_persona":    False,
        "use_persona_name":    None,
    }


# ══════════════════════════════════════════════════════════════════════════════
# FIX #1 — Real Email Sending
# ══════════════════════════════════════════════════════════════════════════════

class TestEmailSending:

    def test_send_email_without_api_key_returns_false(self):
        from app.services.auth_service import _send_email
        with patch("app.services.auth_service.settings") as mock_settings:
            mock_settings.SENDGRID_API_KEY = None
            result = _send_email("user@test.com", "Subject", "<p>Hello</p>")
        assert result is False

    def test_send_email_sendgrid_exception_returns_false(self):
        from app.services.auth_service import _send_email
        with patch("app.services.auth_service.settings") as mock_settings:
            mock_settings.SENDGRID_API_KEY = "SG.fake-key"
            mock_settings.FROM_EMAIL = "noreply@occacia.com"
            boom = MagicMock()
            boom.SendGridAPIClient.side_effect = RuntimeError("network error")
            with patch.dict("sys.modules", {
                "sendgrid": boom,
                "sendgrid.helpers.mail": MagicMock(),
            }):
                result = _send_email("user@test.com", "Oops", "<p>Hi</p>")
        assert result is False

    def test_send_email_is_callable(self):
        from app.services.auth_service import _send_email
        assert callable(_send_email)

    def test_customer_registration_triggers_email(self, client):
        payload = {
            "full_name": "Email Test",
            "email":     f"test-{_uid()}@example.com",
            "password":  "TestPass123!",
            "phone":     "+94771234567",
        }
        with patch("app.services.auth_service._send_email", return_value=False):
            resp = client.post(AUTH_URL + "/register", json=payload)
        assert resp.status_code in (200, 201), resp.text

    def test_password_reset_triggers_email(self, client, active_customer):
        resp = client.post(
            AUTH_URL + "/password/forgot",
            json={"email": active_customer.email},
        )

        assert resp.status_code in (200, 202), resp.text

        db = SessionLocal()
        try:
            notification = (
                db.query(Notification)
                .filter(
                    Notification.user_id == active_customer.customer_id,
                    Notification.type == PASSWORD_RESET_NOTIFICATION,
                )
                .order_by(Notification.created_at.desc())
                .first()
            )
            assert notification is not None
            assert notification.recipient_email == active_customer.email
            assert notification.status == NOTIFICATION_STATUS_QUEUED
        finally:
            db.close()


# ══════════════════════════════════════════════════════════════════════════════
# FIX #2 — AI Tag Injection
# ══════════════════════════════════════════════════════════════════════════════

class TestAITagInjection:

    @pytest.fixture()
    def svc(self):
        from app.services.ai_service import AIService
        return AIService()

    def test_tag_block_injected_into_prompt(self, svc):
        """AVAILABLE_VENUE_TAGS and each tag must appear in the built prompt."""
        # Use _build_prompt() — direct inspection, no HTTP call needed.
        tags = ["romantic", "outdoor", "luxury"]
        prompt = svc._build_prompt("Plan a romantic dinner", available_tags=tags)
        assert "AVAILABLE_VENUE_TAGS" in prompt, \
            "Tag block header must appear in the outgoing Langflow prompt"
        for tag in tags:
            assert tag in prompt, f"Tag '{tag}' must appear in injected prompt"

    def test_no_tags_means_no_tag_block(self, svc):
        """When no tags are provided the prompt must not contain the tag block."""
        prompt = svc._build_prompt("Plan something", available_tags=None)
        # Without tags the header should not appear (default fallback text is used)
        assert "AVAILABLE_VENUE_TAGS" not in prompt

    def test_invalid_tags_stripped_from_parsed_response(self, svc):
        allowed    = ["romantic", "luxury"]
        ai_invents = ["romantic-outdoor", "luxury", "mystery-invented-tag"]

        fake_resp = MagicMock()
        fake_resp.raise_for_status = MagicMock()
        # Use Groq response format
        fake_resp.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "intent":        "planning",
                        "venue_tags":    ai_invents,
                        "budget_per_head": 300,
                        "guest_count":   2,
                        "missing_info":  [],
                        "chat_response": "Here is your plan.",
                    })
                }
            }]
        }

        import asyncio, httpx
        with patch.object(httpx.AsyncClient, "post",
                          AsyncMock(return_value=fake_resp)):
            svc.groq_api_key = "test-key"
            with patch("app.services.ai_service._get_redis", return_value=None):
                result = asyncio.run(
                    svc.generate_date_plan("Plan a luxury dinner",
                                           available_tags=allowed)
                )

        venue_tags = result.get("venue_tags") or []
        if venue_tags:
            assert isinstance(venue_tags, list), "venueTags must be a list"
            for t in venue_tags:
                assert t in allowed, f"Invented tag '{t}' should have been stripped"

    def test_cache_key_changes_when_tags_change(self):
        def make_key(tags):
            tag_block = (
                "\n\nAVAILABLE_VENUE_TAGS — CRITICAL INSTRUCTION:\n"
                "You MUST only use tags from this exact list in the venue_tags field.\n"
                "Do NOT invent, combine, or modify tags. Pick the closest matches only:\n"
                f"{', '.join(tags)}\n"
                "Example: if user wants 'romantic outdoor dinner', use ['romantic', 'nature'] "
                "not 'romantic-outdoor-dinner'.\n"
            )
            seed = "test message" + tag_block
            return hashlib.md5(seed.encode(), usedforsecurity=False).hexdigest()

        assert make_key(["romantic", "outdoor"]) != make_key(["party", "kids"])

    def test_get_all_tags_returns_list(self, vendor_with_packages):
        from app.core.database import SessionLocal
        from app.services.vendor_service import vendor_service
        db = SessionLocal()
        try:
            tags = vendor_service.get_all_tags(db)
        finally:
            db.close()
        assert isinstance(tags, list)
        assert len(tags) > 0
        assert all(isinstance(t, str) for t in tags)
        assert "romantic" in tags
        assert "party" in tags

    def test_planning_endpoint_passes_tags_to_ai(self, auth_client, vendor_with_packages):
        captured: dict = {}

        async def capture_gen(raw_query, history=None, personas=None,
                               available_tags=None, missing_info=None,
                               session_id=None, **kwargs):
            captured["tags"] = available_tags
            return _fake_ai()

        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   side_effect=capture_gen):
            event_id = _create_event(auth_client)
            resp = _chat(auth_client, event_id)

        assert resp.status_code == 200, resp.text
        assert captured.get("tags"), \
            "planning service must pass non-empty available_tags to generate_date_plan"

    def test_all_tags_passed_to_ai_exist_in_db(self, auth_client, vendor_with_packages):
        from app.core.database import SessionLocal
        from app.services.vendor_service import vendor_service
        captured: dict = {}

        async def capture_gen(raw_query, history=None, personas=None,
                               available_tags=None, missing_info=None,
                               session_id=None, **kwargs):
            captured["tags"] = list(available_tags or [])
            return _fake_ai()

        db = SessionLocal()
        try:
            db_tags = set(vendor_service.get_all_tags(db))
        finally:
            db.close()

        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   side_effect=capture_gen):
            event_id = _create_event(auth_client)
            _chat(auth_client, event_id)

        for t in captured.get("tags", []):
            assert t in db_tags, f"Tag '{t}' passed to AI is not in DB"


# ══════════════════════════════════════════════════════════════════════════════
# FIX #3 — Gift Intent Routing
# ══════════════════════════════════════════════════════════════════════════════

class TestGiftIntentRouting:

    @pytest.fixture()
    def vs(self):
        from app.services.vendor_service import vendor_service
        return vendor_service

    def test_gift_intent_calls_find_gift_matches(self, auth_client, vendor_with_packages, vs):
        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock,
                   return_value=_fake_ai(intent="gift", tags=["nature", "adventure"])), \
             patch.object(vs, "find_gift_matches", return_value=[]) as mock_gift, \
             patch("app.routers.v1.customer_router.chat_service.get_session_history", return_value=[]), \
             patch("app.routers.v1.customer_router.chat_service.save_message", return_value=None), \
             patch("app.routers.v1.customer_router.chat_service.get_last_missing_info", return_value=[]), \
             patch("app.services.persona_service.persona_service.get_personas", return_value=[]), \
             patch.object(vs, "find_perfect_matches", return_value=[]), \
             patch.object(vs, "get_all_tags", return_value=["nature", "adventure"]), \
             patch.object(vs, "get_availability_block", return_value=""), \
             patch.object(vs, "extract_location_from_text", return_value=None):
            event_id = _create_event(auth_client)
            resp = _chat(auth_client, event_id, "Gift for a nature lover")
        assert resp.status_code == 200, resp.text
        mock_gift.assert_called_once()

    def test_gift_matches_appear_in_response(self, auth_client, vendor_with_packages, vs):
        from app.core.database import SessionLocal
        from app.models.package import Package as Pkg
        db = SessionLocal()
        try:
            pkg = db.query(Pkg).first()
        finally:
            db.close()
        assert pkg is not None

        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock,
                   return_value=_fake_ai(intent="gift", tags=["nature"])), \
             patch.object(vs, "find_gift_matches", return_value=[pkg]), \
             patch("app.routers.v1.customer_router.chat_service.get_session_history", return_value=[]), \
             patch("app.routers.v1.customer_router.chat_service.save_message", return_value=None), \
             patch("app.routers.v1.customer_router.chat_service.get_last_missing_info", return_value=[]), \
             patch("app.services.persona_service.persona_service.get_personas", return_value=[]), \
             patch.object(vs, "find_perfect_matches", return_value=[]), \
             patch.object(vs, "get_all_tags", return_value=["nature"]), \
             patch.object(vs, "get_availability_block", return_value=""), \
             patch.object(vs, "extract_location_from_text", return_value=None):
            event_id = _create_event(auth_client)
            resp = _chat(auth_client, event_id, "Gift idea")

        assert resp.status_code == 200, resp.text
        assert pkg.name in [v.get("name", "") for v in resp.json().get("matchedVenues", [])]

    def test_gift_persona_enrichment(self, auth_client, active_customer, vs):
        """Persona hobbies (preferences_json) must be merged into gift_tags."""
        from app.models.persona import Persona
        mock_persona = MagicMock(spec=Persona)
        mock_persona.name             = "Alex"
        mock_persona.preferences_json = ["hiking", "camping"]
        mock_persona.food_preferences = []
        mock_persona.personality_tags = []

        captured: dict = {}

        def capture_gift(db, gift_tags, budget=None):
            captured["tags"] = list(gift_tags)
            return []

        ai_resp = _fake_ai(
            intent="gift",
            tags=["nature"],
            chat_response="How about a gift for Alex?",
        )

        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock, return_value=ai_resp), \
             patch("app.services.persona_service.persona_service.get_personas",
                   return_value=[mock_persona]), \
             patch("app.routers.v1.customer_router.chat_service.get_session_history", return_value=[]), \
             patch("app.routers.v1.customer_router.chat_service.save_message", return_value=None), \
             patch("app.routers.v1.customer_router.chat_service.get_last_missing_info", return_value=[]), \
             patch.object(vs, "find_gift_matches", side_effect=capture_gift), \
             patch.object(vs, "find_perfect_matches", return_value=[]), \
             patch.object(vs, "get_all_tags", return_value=["nature"]), \
             patch.object(vs, "get_availability_block", return_value=""), \
             patch.object(vs, "extract_location_from_text", return_value=None):
            event_id = _create_event(auth_client)
            resp = _chat(auth_client, event_id, "Gift for Alex")

        assert resp.status_code == 200, resp.text
        merged = captured.get("tags", [])
        assert "hiking" in merged or "camping" in merged, \
            f"Persona hobbies must be merged into gift_tags. Got: {merged!r}"

    def test_find_gift_matches_returns_tagged_packages(self, vendor_with_packages, vs):
        from app.core.database import SessionLocal
        db = SessionLocal()
        try:
            results = vs.find_gift_matches(db, ["nature"], budget=500)
        finally:
            db.close()
        assert "Nature Retreat" in [r.name for r in results]

    def test_find_gift_matches_respects_budget(self, vendor_with_packages, vs):
        from app.core.database import SessionLocal
        db = SessionLocal()
        try:
            results = vs.find_gift_matches(db, ["romantic"], budget=10)
        finally:
            db.close()
        for pkg in results:
            if pkg.price_per_head is not None:
                assert pkg.price_per_head <= 10

    def test_find_gift_matches_empty_tags_returns_empty(self, vendor_with_packages, vs):
        from app.core.database import SessionLocal
        db = SessionLocal()
        try:
            results = vs.find_gift_matches(db, [], budget=1000)
        finally:
            db.close()
        assert results == []

    def test_date_intent_does_not_call_find_gift_matches(self, auth_client,
                                                          vendor_with_packages, vs):
        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock,
                   return_value=_fake_ai(intent="planning", tags=["romantic"])), \
             patch.object(vs, "find_gift_matches") as mock_gift:
            event_id = _create_event(auth_client)
            resp = _chat(auth_client, event_id, "Plan a date")
        assert resp.status_code == 200, resp.text
        mock_gift.assert_not_called()

    def test_find_gift_matches_no_budget_limit(self, vendor_with_packages, vs):
        from app.core.database import SessionLocal
        db = SessionLocal()
        try:
            assert len(vs.find_gift_matches(db, ["romantic"], budget=None)) >= 1
        finally:
            db.close()

    def test_find_gift_matches_multiple_tags(self, vendor_with_packages, vs):
        from app.core.database import SessionLocal
        db = SessionLocal()
        try:
            names = [r.name for r in vs.find_gift_matches(db, ["romantic", "nature"], budget=None)]
        finally:
            db.close()
        assert "Romantic Dinner" in names or "Nature Retreat" in names


# ══════════════════════════════════════════════════════════════════════════════
# FIX #4 — missing_info Persistence
# ══════════════════════════════════════════════════════════════════════════════

class TestMissingInfoPersistence:

    @pytest.fixture()
    def db(self):
        from app.core.database import SessionLocal
        s = SessionLocal()
        yield s
        s.close()

    def test_chat_message_has_missing_info_column(self, db):
        from app.models.chat_model import ChatMessage
        msg = ChatMessage(
            session_id=f"sess-{_uid()}",
            user_message="hello",
            ai_message="hi",
            missing_info=["budget", "guest_count"],
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)
        assert msg.missing_info == ["budget", "guest_count"]

    def test_chat_message_missing_info_defaults_to_list(self, db):
        from app.models.chat_model import ChatMessage
        msg = ChatMessage(
            session_id=f"sess-{_uid()}",
            user_message="test",
            ai_message="ok",
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)
        assert msg.missing_info is not None
        assert isinstance(msg.missing_info, list)

    def test_chat_service_saves_missing_info(self, db):
        from app.models.chat_model import ChatMessage
        from app.services.chat_service import chat_service
        session = f"sess-{_uid()}"
        chat_service.save_message(
            db,
            session_id=session,
            user_msg="What about a date?",
            ai_msg="Sure! I need budget and date.",
            missing_info=["budget", "event_date"],
        )
        saved = db.query(ChatMessage).filter_by(session_id=session).first()
        assert saved is not None
        assert "budget"     in saved.missing_info
        assert "event_date" in saved.missing_info

    def test_chat_service_retrieves_missing_info(self, db):
        from app.services.chat_service import chat_service
        session = f"sess-{_uid()}"
        chat_service.save_message(
            db,
            session_id=session,
            user_msg="Plan my birthday",
            ai_msg="How many guests?",
            missing_info=["guest_count", "location"],
        )
        history = chat_service.get_session_history(db, session)
        assert len(history) >= 1
        assert "guest_count" in (history[-1].missing_info or [])

    def test_get_last_missing_info_returns_plain_list(self, db):
        from app.services.chat_service import chat_service
        session = f"sess-{_uid()}"
        chat_service.save_message(
            db, session_id=session,
            user_msg="hi", ai_msg="hello",
            missing_info=["budget"],
        )
        result = chat_service.get_last_missing_info(db, session)
        assert isinstance(result, list)
        assert "budget" in result

    def test_get_last_missing_info_handles_dict_format(self, db):
        from app.models.chat_model import ChatMessage
        from app.services.chat_service import chat_service
        session = f"sess-{_uid()}"
        msg = ChatMessage(
            session_id=session,
            user_message="x",
            ai_message="y",
            missing_info={"items": ["budget", "location"], "_ps": {"step": 2}},
        )
        db.add(msg)
        db.commit()
        result = chat_service.get_last_missing_info(db, session)
        assert isinstance(result, list)
        assert "budget" in result

    def test_get_last_missing_info_empty_session_returns_empty(self, db):
        from app.services.chat_service import chat_service
        assert chat_service.get_last_missing_info(db, f"nonexistent-{_uid()}") == []

    def test_missing_info_injected_into_prompt(self):
        """missing_info items must appear in the prompt built by _build_prompt."""
        from app.services.ai_service import AIService
        svc = AIService()
        # Use _build_prompt() — direct inspection, no HTTP call needed.
        prompt = svc._build_prompt(
            "Continue planning",
            missing_info=["budget", "guest_count"],
        )
        assert "budget"      in prompt, f"'budget' missing from prompt: {prompt[:300]}"
        assert "guest_count" in prompt, f"'guest_count' missing from prompt: {prompt[:300]}"

    def test_missing_info_carried_across_turns(self, auth_client, vendor_with_packages):
        captured: dict = {}

        async def turn1(raw_query, history=None, personas=None,
                        available_tags=None, missing_info=None,
                        session_id=None, **kwargs):
            return _fake_ai(tags=[], missing=["budget"],
                            chat_response="What is your budget?")

        async def turn2(raw_query, history=None, personas=None,
                        available_tags=None, missing_info=None,
                        session_id=None, **kwargs):
            captured["missing"] = missing_info
            return _fake_ai(missing=[])

        from app.services.vendor_service import vendor_service as _vs
        event_id = _create_event(auth_client)
        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   side_effect=turn1), \
             patch("app.routers.v1.customer_router.chat_service.get_session_history", return_value=[]), \
             patch("app.routers.v1.customer_router.chat_service.save_message", return_value=None), \
             patch("app.routers.v1.customer_router.chat_service.get_last_missing_info", return_value=[]), \
             patch("app.services.persona_service.persona_service.get_personas", return_value=[]), \
             patch.object(_vs, "get_all_tags", return_value=[]), \
             patch.object(_vs, "get_availability_block", return_value=""), \
             patch.object(_vs, "extract_location_from_text", return_value=None):
            r1 = _chat(auth_client, event_id, "Plan a date")
        assert r1.status_code == 200, r1.text

        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   side_effect=turn2), \
             patch("app.routers.v1.customer_router.chat_service.get_session_history", return_value=[]), \
             patch("app.routers.v1.customer_router.chat_service.save_message", return_value=None), \
             patch("app.routers.v1.customer_router.chat_service.get_last_missing_info",
                   return_value=["budget"]), \
             patch("app.services.persona_service.persona_service.get_personas", return_value=[]), \
             patch.object(_vs, "get_all_tags", return_value=[]), \
             patch.object(_vs, "get_availability_block", return_value=""), \
             patch.object(_vs, "extract_location_from_text", return_value=None):
            r2 = _chat(auth_client, event_id, "My budget is 300")
        assert r2.status_code == 200, r2.text
        assert "budget" in (captured.get("missing") or []), \
            "missing_info from turn 1 must be forwarded to AI on turn 2"

    def test_missing_info_in_response(self, auth_client, vendor_with_packages):
        from app.services.vendor_service import vendor_service as _vs
        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock,
                   return_value=_fake_ai(tags=[], missing=["budget", "location"])), \
             patch("app.routers.v1.customer_router.chat_service.get_session_history", return_value=[]), \
             patch("app.routers.v1.customer_router.chat_service.save_message", return_value=None), \
             patch("app.routers.v1.customer_router.chat_service.get_last_missing_info", return_value=[]), \
             patch("app.services.persona_service.persona_service.get_personas", return_value=[]), \
             patch.object(_vs, "get_all_tags", return_value=[]), \
             patch.object(_vs, "get_availability_block", return_value=""), \
             patch.object(_vs, "extract_location_from_text", return_value=None):
            event_id = _create_event(auth_client)
            resp = _chat(auth_client, event_id)
        assert "budget" in (resp.json().get("missingInfo") or [])

    def test_missing_info_empty_when_satisfied(self, auth_client, vendor_with_packages):
        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock,
                   return_value=_fake_ai(tags=["romantic"], missing=[])):
            event_id = _create_event(auth_client)
            resp = _chat(auth_client, event_id)
        assert (resp.json().get("missingInfo") or []) == []


# ══════════════════════════════════════════════════════════════════════════════
# Integration: planning endpoint sanity
# ══════════════════════════════════════════════════════════════════════════════

class TestPlanningEndpointIntegration:

    def test_response_schema_has_required_fields(self, auth_client, vendor_with_packages):
        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock, return_value=_fake_ai()):
            event_id = _create_event(auth_client)
            resp = _chat(auth_client, event_id)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        for field in ("intent", "reply", "matchedVenues",
                      "askSavePersona", "personaSaved", "personaConfirmed"):
            assert field in data, f"Missing field: {field}"

    def test_unauthenticated_request_rejected(self, client):
        assert client.post(
            "/api/v1/customers/events/EVT-fake/chat",
            json={"content": "Plan a romantic dinner"},
        ).status_code in (401, 403)

    def test_invalid_session_id_rejected(self, auth_client):
        resp = auth_client.post(
            "/api/v1/customers/events/EVT-invalid-does-not-exist/chat",
            json={"content": "Hi"},
        )
        assert resp.status_code in (400, 404, 422)

    def test_missing_user_query_rejected(self, auth_client):
        event_id = _create_event(auth_client)
        assert auth_client.post(
            f"/api/v1/customers/events/{event_id}/chat",
            json={},
        ).status_code == 422

    def test_matched_venues_in_response(self, auth_client, vendor_with_packages):
        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock,
                   return_value=_fake_ai(intent="planning", tags=["romantic"])):
            event_id = _create_event(auth_client)
            resp = _chat(auth_client, event_id)
        assert "matchedVenues" in resp.json()

    def test_ai_error_returns_fallback(self, auth_client, vendor_with_packages):
        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   side_effect=RuntimeError("Langflow down")):
            event_id = _create_event(auth_client)
            resp = _chat(auth_client, event_id)
        assert resp.status_code == 200
        assert resp.json().get("intent") == "chat"

    def test_all_four_fixes_flow_together(self, auth_client, vendor_with_packages):
        from app.services.vendor_service import vendor_service as vs
        ai_resp = _fake_ai(intent="gift", tags=["nature"], missing=["recipient_name"])
        ai_resp["giftSuggestion"] = "Nature Retreat"
        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock, return_value=ai_resp), \
             patch.object(vs, "find_gift_matches", return_value=[]):
            event_id = _create_event(auth_client)
            resp = _chat(auth_client, event_id, "Gift for a nature lover")
        assert resp.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# vendor_service unit tests
# ══════════════════════════════════════════════════════════════════════════════

class TestVendorService:

    @pytest.fixture()
    def vs(self):
        from app.services.vendor_service import vendor_service
        return vendor_service

    def test_get_all_tags_deduplicates(self, vendor_with_packages, vs):
        from app.core.database import SessionLocal
        db = SessionLocal()
        try:
            tags = vs.get_all_tags(db)
        finally:
            db.close()
        assert len(tags) == len(set(tags))

    def test_get_all_tags_returns_known_tags(self, vendor_with_packages, vs):
        from app.core.database import SessionLocal
        db = SessionLocal()
        try:
            tags = vs.get_all_tags(db)
        finally:
            db.close()
        assert isinstance(tags, list)
        assert len(tags) > 0
        assert "romantic" in tags

    def test_find_gift_matches_no_budget_limit(self, vendor_with_packages, vs):
        from app.core.database import SessionLocal
        db = SessionLocal()
        try:
            assert len(vs.find_gift_matches(db, ["romantic"], budget=None)) >= 1
        finally:
            db.close()

    def test_find_gift_matches_multiple_tags(self, vendor_with_packages, vs):
        from app.core.database import SessionLocal
        db = SessionLocal()
        try:
            names = [r.name for r in vs.find_gift_matches(db, ["romantic", "nature"], budget=None)]
        finally:
            db.close()
        assert "Romantic Dinner" in names or "Nature Retreat" in names
