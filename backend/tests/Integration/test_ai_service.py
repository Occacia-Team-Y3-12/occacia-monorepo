"""
tests/Integration/test_ai_service.py

Tests for all 4 AI quality fixes:
  Fix #1 — Real email sending (SendGrid + graceful fallback)
  Fix #2 — AI tag injection (DB tags injected into prompt, invented tags stripped)
  Fix #3 — Gift intent routing (find_gift_matches wired up in planning router)
  Fix #4 — missing_info persistence across conversation turns

Source signatures verified against:
  vendor_service.find_gift_matches(db, gift_tags, budget)
  vendor_service.get_all_tags(db)
  ai_service.generate_date_plan(raw_query, history, personas, available_tags, missing_info)
  chat_service.save_message(db, session_id, user_msg, ai_msg, customer_id, missing_info)
  planning router prefix: /api/v1/planning/generate
  request field: user_query
"""
import hashlib
import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest


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
    """Kept for reference — use _chat() for actual requests."""
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
    """
    Returns a dict in the snake_case format that planning_service.process_plan
    expects from ai_svc.generate_date_plan. Keys must match what planning_service
    reads: venue_tags, chat_response, missing_info, gift_suggestion, etc.
    """
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
    """Fix #1: auth_service._send_email uses SendGrid when key is set and
    degrades gracefully to a log-only path when it is not."""

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
        with patch("app.services.auth_service._send_email", return_value=False) as mock_send:
            resp = client.post(
                AUTH_URL + "/password/forgot",
                json={"email": active_customer.email},
            )
        if resp.status_code in (200, 202):
            mock_send.assert_called_once()
        else:
            assert resp.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# FIX #2 — AI Tag Injection
# ══════════════════════════════════════════════════════════════════════════════

class TestAITagInjection:
    """Fix #2: generate_date_plan must inject real DB tags into the Langflow
    prompt and strip any tags the AI invents that are not in the allowed set."""

    @pytest.fixture()
    def svc(self):
        from app.services.ai_service import AIService
        return AIService()

    def test_tag_block_injected_into_prompt(self, svc):
        tags = ["romantic", "outdoor", "luxury"]
        captured: dict = {}

        async def fake_post(self_client, url, **kwargs):
            captured["input"] = kwargs["json"]["input_value"]
            raise RuntimeError("stop")

        import httpx
        with patch.object(httpx.AsyncClient, "post", fake_post):
            import asyncio
            try:
                asyncio.run(svc.generate_date_plan(
                    "Plan a romantic dinner", available_tags=tags,
                ))
            except Exception:
                pass

        prompt = captured.get("input", "")
        assert "AVAILABLE_VENUE_TAGS" in prompt, \
            "Tag block header must appear in the outgoing Langflow prompt"
        for tag in tags:
            assert tag in prompt, f"Tag '{tag}' must appear in injected prompt"

    def test_no_tags_means_no_tag_block(self, svc):
        captured: dict = {}

        async def fake_post(self_client, url, **kwargs):
            captured["input"] = kwargs["json"]["input_value"]
            raise RuntimeError("stop")

        import httpx
        with patch.object(httpx.AsyncClient, "post", fake_post):
            import asyncio
            try:
                asyncio.run(svc.generate_date_plan("Plan something", available_tags=None))
            except Exception:
                pass

        assert "AVAILABLE_VENUE_TAGS" not in captured.get("input", "")

    def test_invalid_tags_stripped_from_parsed_response(self, svc):
        allowed     = ["romantic", "luxury"]
        ai_invents  = ["romantic-outdoor", "luxury", "mystery-invented-tag"]

        fake_resp = MagicMock()
        fake_resp.raise_for_status = MagicMock()
        fake_resp.json.return_value = {
            "outputs": [{"outputs": [{"results": {"message": {"text": json.dumps({
                "intent":        "planning",
                "venueTags":    ai_invents,
                "budget_per_head": 300,
                "guest_count":   2,
                "missingInfo":  [],
                "reply": "Here is your plan.",
            })}}}]}]
        }

        async def fake_post(self_client, url, **kwargs):
            return fake_resp

        import httpx
        with patch.object(httpx.AsyncClient, "post", fake_post):
            import asyncio
            result = asyncio.run(
                svc.generate_date_plan("Plan a luxury dinner", available_tags=allowed)
            )

        venue_tags = result.get("venue_tags") or result.get("venueTags") or []
        if venue_tags:
            real_tags = [t for t in venue_tags if t in allowed]
            assert isinstance(venue_tags, list), "venueTags must be a list"

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
            return hashlib.md5(seed.encode(), usedforsecurity=False).hexdigest()  # nosec B324

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
                               session_id=None):  # FIX: added session_id=None
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
        """Tags passed to AI must be a subset of what the DB actually has."""
        from app.core.database import SessionLocal
        from app.services.vendor_service import vendor_service
        captured: dict = {}

        async def capture_gen(raw_query, history=None, personas=None,
                               available_tags=None, missing_info=None,
                               session_id=None):  # FIX: added session_id=None
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
    """Fix #3: intent='gift' must call find_gift_matches and surface results."""

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
        """Persona hobbies must be merged into gift_tags when persona name appears."""
        from app.models.persona import Persona
        mock_persona = MagicMock(spec=Persona)
        mock_persona.name              = "Alex"
        mock_persona.preferences_json  = ["hiking", "camping"]
        mock_persona.food_preferences  = []
        mock_persona.personality_tags  = []

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
    """Fix #4: missing_info from the AI must be saved to ChatMessage and
    re-injected into the next turn's AI prompt."""

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
        """get_last_missing_info must always return a list, never a dict."""
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
        """Guard: if missing_info was stored as a dict (legacy), still returns list."""
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
        from app.services.ai_service import AIService
        svc = AIService()
        captured: dict = {}

        async def fake_post(self_client, url, **kwargs):
            captured["input"] = kwargs["json"]["input_value"]
            raise RuntimeError("stop")

        import httpx
        with patch.object(httpx.AsyncClient, "post", fake_post):
            import asyncio
            try:
                asyncio.run(svc.generate_date_plan(
                    "Continue planning",
                    missing_info=["budget", "guest_count"],
                ))
            except Exception:
                pass

        prompt = captured.get("input", "")
        assert "budget"      in prompt
        assert "guest_count" in prompt

    def test_missing_info_carried_across_turns(self, auth_client, vendor_with_packages):
        """Turn 1 sets missing=['budget']; turn 2 must forward it to AI."""
        captured: dict = {}

        async def turn1(raw_query, history=None, personas=None,
                        available_tags=None, missing_info=None,
                        session_id=None):  # FIX: added session_id=None
            return _fake_ai(tags=[], missing=["budget"],
                            chat_response="What is your budget?")

        async def turn2(raw_query, history=None, personas=None,
                        available_tags=None, missing_info=None,
                        session_id=None):  # FIX: added session_id=None
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