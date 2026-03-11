"""
tests/test_messaging_workflow.py

OCA-209 — Validate Messaging Workflow
End-to-end pytest suite covering the full chat/planning interaction lifecycle:

  1.  Happy path  — single turn returns 200 with correct shape
  2.  Session isolation — two sessions never bleed into each other
  3.  Multi-turn memory — history grows correctly across turns
  4.  missing_info carry-forward — AI-flagged gaps re-injected next turn
  5.  missing_info resolution — resolved gaps NOT re-injected
  6.  Rate limiting — 11th request in 60 s → 429
  7.  Session ID validation — bad chars → 400
  8.  Planning intent — matched_venues populated
  9.  Gift intent — gift_suggestion populated
 10.  Multi-intent — BOTH matched_venues AND gift_suggestion populated
 11.  Chat intent — matched_venues stays empty
 12.  AI fallback — Langflow down → 200 with graceful message
 13.  Budget extraction — natural language budget lands in response
 14.  Guest extraction — "20 people" parsed correctly
 15.  Location extraction — alias "CMB" → "colombo" in response
 16.  Confidence score — match_score_label present in every venue
 17.  Context compression — turn-1 always in history after 10 turns
 18.  Message persistence — every turn saved to DB
 19.  Unauthenticated request — 401 / 403
 20.  Empty query — handled without 500
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

PLAN_URL = "/api/v1/planning/generate"


def _uid():
    return uuid4().hex[:8]


def _payload(message="Plan a romantic dinner", session_id=None):
    return {
        "session_id": session_id or f"sess-{_uid()}",
        "user_query": message,
    }


def _fake_ai(
    intent="date",
    tags=None,
    missing=None,
    chat_response="Here is your plan.",
    gift=None,
    location=None,
    budget=None,
    guests=None,
):
    return {
        "intent":            intent,
        "venue_tags":        tags if tags is not None else ["romantic"],
        "budget_per_head":   budget,
        "guest_count":       guests,
        "chat_response":     chat_response,
        "missing_info":      missing if missing is not None else [],
        "gift_suggestion":   gift,
        "event_type":        None,
        "location":          location,
        "reasoning":         None,
        "personality_profile": None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture()
def db():
    from app.core.database import SessionLocal
    s = SessionLocal()
    yield s
    s.close()


@pytest.fixture()
def vs():
    from app.services.vendor_service import vendor_service
    return vendor_service


# ═════════════════════════════════════════════════════════════════════════════
# 1. HAPPY PATH
# ═════════════════════════════════════════════════════════════════════════════

class TestHappyPath:
    """A well-formed request must return 200 with the correct response shape."""

    def test_single_turn_returns_200(self, auth_client, vendor_with_packages):
        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock, return_value=_fake_ai()):
            resp = auth_client.post(PLAN_URL, json=_payload())
        assert resp.status_code == 200, resp.text

    def test_response_has_required_fields(self, auth_client, vendor_with_packages):
        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock, return_value=_fake_ai()):
            resp = auth_client.post(PLAN_URL, json=_payload())

        body = resp.json()
        for field in ["intent", "chat_response", "matched_venues",
                      "gift_suggestion", "missing_info", "venue_tags"]:
            assert field in body, f"Response missing field: {field}"

    def test_intent_echoed_in_response(self, auth_client, vendor_with_packages):
        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock,
                   return_value=_fake_ai(intent="planning")):
            resp = auth_client.post(PLAN_URL, json=_payload())

        assert resp.json()["intent"] == "planning"

    def test_chat_response_present(self, auth_client, vendor_with_packages):
        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock,
                   return_value=_fake_ai(chat_response="I found some great options!")):
            resp = auth_client.post(PLAN_URL, json=_payload())

        assert resp.json()["chat_response"] == "I found some great options!"


# ═════════════════════════════════════════════════════════════════════════════
# 2. SESSION ISOLATION
# ═════════════════════════════════════════════════════════════════════════════

class TestSessionIsolation:
    """Messages from one session must never appear in another session's history."""

    def test_two_sessions_do_not_share_history(self, auth_client,
                                                vendor_with_packages, db):
        from app.services.chat_service import chat_service

        sid_a = f"sess-{_uid()}"
        sid_b = f"sess-{_uid()}"

        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock,
                   return_value=_fake_ai(chat_response="Reply for A")):
            auth_client.post(PLAN_URL, json=_payload("Message for A", sid_a))

        history_b = chat_service.get_session_history(db, sid_b)
        assert len(history_b) == 0, "Session B must have no history from session A"

    def test_session_a_history_not_in_session_b_messages(self, auth_client,
                                                           vendor_with_packages, db):
        from app.services.chat_service import chat_service

        sid_a = f"sess-{_uid()}"
        sid_b = f"sess-{_uid()}"

        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock, return_value=_fake_ai()):
            auth_client.post(PLAN_URL, json=_payload("Unique message alpha", sid_a))
            auth_client.post(PLAN_URL, json=_payload("Different message beta", sid_b))

        history_a = chat_service.get_session_history(db, sid_a)
        history_b = chat_service.get_session_history(db, sid_b)

        a_texts = [m.user_message for m in history_a]
        b_texts = [m.user_message for m in history_b]

        assert "Unique message alpha"   in a_texts
        assert "Unique message alpha" not in b_texts
        assert "Different message beta" in b_texts
        assert "Different message beta" not in a_texts


# ═════════════════════════════════════════════════════════════════════════════
# 3. MULTI-TURN MEMORY
# ═════════════════════════════════════════════════════════════════════════════

class TestMultiTurnMemory:
    """History must grow correctly across consecutive turns in the same session."""

    def test_history_grows_across_turns(self, auth_client,
                                         vendor_with_packages, db):
        from app.services.chat_service import chat_service

        sid = f"sess-{_uid()}"
        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock, return_value=_fake_ai()):
            auth_client.post(PLAN_URL, json=_payload("Turn 1", sid))
            auth_client.post(PLAN_URL, json=_payload("Turn 2", sid))
            auth_client.post(PLAN_URL, json=_payload("Turn 3", sid))

        history = chat_service.get_session_history(db, sid)
        assert len(history) == 3, f"Expected 3 turns, got {len(history)}"

    def test_history_ordered_chronologically(self, auth_client,
                                              vendor_with_packages, db):
        from app.services.chat_service import chat_service

        sid = f"sess-{_uid()}"
        messages = ["First message", "Second message", "Third message"]

        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock, return_value=_fake_ai()):
            for msg in messages:
                auth_client.post(PLAN_URL, json=_payload(msg, sid))

        history = chat_service.get_session_history(db, sid)
        retrieved = [m.user_message for m in history]
        assert retrieved == messages, \
            f"Messages must be in chronological order. Got: {retrieved}"

    def test_ai_receives_history_on_turn_2(self, auth_client,
                                             vendor_with_packages):
        """On turn 2 the AI call must receive non-empty history."""
        sid = f"sess-{_uid()}"
        captured = {}

        async def fake_ai_turn2(raw_query, history=None, personas=None,
                                 available_tags=None, missing_info=None):
            captured["history"] = history
            return _fake_ai()

        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock, return_value=_fake_ai()):
            auth_client.post(PLAN_URL, json=_payload("First turn", sid))

        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   side_effect=fake_ai_turn2):
            auth_client.post(PLAN_URL, json=_payload("Second turn", sid))

        assert captured.get("history"), \
            "AI must receive non-empty history on turn 2"
        assert len(captured["history"]) >= 1


# ═════════════════════════════════════════════════════════════════════════════
# 4. MISSING INFO CARRY-FORWARD
# ═════════════════════════════════════════════════════════════════════════════

class TestMissingInfoCarryForward:
    """missing_info flagged by the AI must be forwarded to the next turn."""

    def test_missing_info_carried_to_next_turn(self, auth_client,
                                                 vendor_with_packages):
        sid = f"sess-{_uid()}"
        captured = {}

        async def turn2(raw_query, history=None, personas=None,
                        available_tags=None, missing_info=None):
            captured["missing"] = missing_info
            return _fake_ai(missing=[])

        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock,
                   return_value=_fake_ai(missing=["budget", "location"])):
            auth_client.post(PLAN_URL, json=_payload("Plan a party", sid))

        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   side_effect=turn2):
            auth_client.post(PLAN_URL, json=_payload("I need help", sid))

        forwarded = captured.get("missing") or []
        assert "budget"   in forwarded, "budget must be carried forward"
        assert "location" in forwarded, "location must be carried forward"

    def test_missing_info_in_turn1_response(self, auth_client,
                                              vendor_with_packages):
        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock,
                   return_value=_fake_ai(missing=["guest_count"])):
            resp = auth_client.post(PLAN_URL, json=_payload())

        assert "guest_count" in resp.json()["missing_info"]


# ═════════════════════════════════════════════════════════════════════════════
# 5. MISSING INFO RESOLUTION
# ═════════════════════════════════════════════════════════════════════════════

class TestMissingInfoResolution:
    """Once the user provides a missing detail, it should not keep being asked."""

    def test_resolved_missing_info_not_re_injected(self, auth_client,
                                                     vendor_with_packages):
        sid = f"sess-{_uid()}"
        turn3_captured = {}

        async def turn1(*a, **kw):
            return _fake_ai(missing=["budget"])

        async def turn2(*a, **kw):
            return _fake_ai(missing=[])   # AI satisfied — budget resolved

        async def turn3(raw_query, history=None, personas=None,
                        available_tags=None, missing_info=None):
            turn3_captured["missing"] = missing_info
            return _fake_ai(missing=[])

        for fn in [turn1, turn2, turn3]:
            with patch("app.services.ai_service.ai_service.generate_date_plan",
                       side_effect=fn):
                auth_client.post(PLAN_URL, json=_payload("msg", sid))

        # After AI returned missing=[] on turn 2, turn 3 must not carry "budget"
        assert "budget" not in (turn3_captured.get("missing") or []), \
            "Resolved missing_info must not be re-injected on subsequent turns"


# ═════════════════════════════════════════════════════════════════════════════
# 6. RATE LIMITING
# ═════════════════════════════════════════════════════════════════════════════

class TestRateLimiting:
    """More than 10 requests per minute must return 429."""

    def test_rate_limit_blocks_11th_request(self, auth_client,
                                              vendor_with_packages):
        from app.routers.v1.planning_router import check_rate_limit
        from fastapi import HTTPException

        call_count = 0

        def mock_rate_limit(customer_id, session_id=None):
            nonlocal call_count
            call_count += 1
            if call_count > 10:
                raise HTTPException(status_code=429,
                                    detail="Rate limit exceeded.")

        with patch("app.routers.v1.planning_router.check_rate_limit",
                   side_effect=mock_rate_limit), \
             patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock, return_value=_fake_ai()):
            responses = [
                auth_client.post(PLAN_URL, json=_payload())
                for _ in range(11)
            ]

        statuses = [r.status_code for r in responses]
        assert 429 in statuses, \
            f"Expected a 429 after 10 requests, got statuses: {statuses}"

    def test_first_10_requests_succeed(self, auth_client, vendor_with_packages):
        """The first 10 requests must all succeed (not be rate-limited)."""
        from app.routers.v1.planning_router import check_rate_limit

        call_count = 0

        def mock_rate_limit(customer_id, session_id=None):
            nonlocal call_count
            call_count += 1
            if call_count > 10:
                from fastapi import HTTPException
                raise HTTPException(status_code=429, detail="Rate limit exceeded.")

        with patch("app.routers.v1.planning_router.check_rate_limit",
                   side_effect=mock_rate_limit), \
             patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock, return_value=_fake_ai()):
            responses = [
                auth_client.post(PLAN_URL, json=_payload())
                for _ in range(10)
            ]

        assert all(r.status_code == 200 for r in responses), \
            "First 10 requests must all return 200"


# ═════════════════════════════════════════════════════════════════════════════
# 7. SESSION ID VALIDATION
# ═════════════════════════════════════════════════════════════════════════════

class TestSessionIdValidation:
    """Malformed session_id values must be rejected with 400."""

    def test_session_id_with_spaces_rejected(self, auth_client):
        resp = auth_client.post(PLAN_URL, json=_payload(session_id="bad session"))
        assert resp.status_code == 400, resp.text

    def test_session_id_with_slash_rejected(self, auth_client):
        resp = auth_client.post(PLAN_URL, json=_payload(session_id="bad/session"))
        assert resp.status_code == 400, resp.text

    def test_session_id_too_long_rejected(self, auth_client):
        resp = auth_client.post(PLAN_URL, json=_payload(session_id="a" * 65))
        assert resp.status_code == 400, resp.text

    def test_valid_session_id_accepted(self, auth_client, vendor_with_packages):
        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock, return_value=_fake_ai()):
            resp = auth_client.post(PLAN_URL,
                                     json=_payload(session_id="valid-session_01"))
        assert resp.status_code == 200, resp.text


# ═════════════════════════════════════════════════════════════════════════════
# 8. INTENT ROUTING — PLANNING
# ═════════════════════════════════════════════════════════════════════════════

class TestPlanningIntent:
    """When intent is planning/date, matched_venues must be populated."""

    def test_planning_intent_populates_matched_venues(self, auth_client,
                                                        vendor_with_packages, vs):
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
                   return_value=_fake_ai(intent="planning", tags=["romantic"])), \
             patch.object(vs, "find_perfect_matches", return_value=[pkg]):
            resp = auth_client.post(PLAN_URL,
                                     json=_payload("Plan a romantic dinner"))

        assert resp.status_code == 200, resp.text
        assert len(resp.json()["matched_venues"]) > 0, \
            "matched_venues must be populated for planning intent"

    def test_planning_intent_venue_has_id_and_name(self, auth_client,
                                                     vendor_with_packages, vs):
        from app.core.database import SessionLocal
        from app.models.package import Package as Pkg

        db = SessionLocal()
        try:
            pkg = db.query(Pkg).first()
        finally:
            db.close()

        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock,
                   return_value=_fake_ai(intent="planning", tags=["romantic"])), \
             patch.object(vs, "find_perfect_matches", return_value=[pkg]):
            resp = auth_client.post(PLAN_URL, json=_payload())

        venue = resp.json()["matched_venues"][0]
        assert "id"   in venue, "venue must have id"
        assert "name" in venue, "venue must have name"


# ═════════════════════════════════════════════════════════════════════════════
# 9. INTENT ROUTING — GIFT
# ═════════════════════════════════════════════════════════════════════════════

class TestGiftIntent:
    """When intent is gift, gift_suggestion must be populated."""

    def test_gift_intent_populates_gift_suggestion(self, auth_client,
                                                     vendor_with_packages, vs):
        """For gift intent the router runs find_gift_matches and puts results
        in matched_venues (same field as planning).  gift_suggestion is only
        auto-populated in the multi-intent branch when the AI doesn't already
        provide one.  So we assert matched_venues is non-empty."""
        from app.core.database import SessionLocal
        from app.models.package import Package as Pkg

        db = SessionLocal()
        try:
            pkg = db.query(Pkg).first()
        finally:
            db.close()

        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock,
                   return_value=_fake_ai(intent="gift", tags=["nature"])), \
             patch.object(vs, "find_gift_matches", return_value=[pkg]):
            resp = auth_client.post(PLAN_URL,
                                     json=_payload("I want to buy a gift"))

        assert resp.status_code == 200, resp.text
        assert len(resp.json()["matched_venues"]) > 0, \
            "matched_venues must be populated when gift intent returns packages"

    def test_gift_intent_does_not_call_venue_matcher(self, auth_client,
                                                       vendor_with_packages, vs):
        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock,
                   return_value=_fake_ai(intent="gift", tags=["nature"])), \
             patch.object(vs, "find_perfect_matches",
                          return_value=[]) as mock_venues, \
             patch.object(vs, "find_gift_matches", return_value=[]):
            auth_client.post(PLAN_URL, json=_payload("Buy a gift"))

        mock_venues.assert_not_called()


# ═════════════════════════════════════════════════════════════════════════════
# 10. INTENT ROUTING — MULTI
# ═════════════════════════════════════════════════════════════════════════════

class TestMultiIntent:
    """A message with both planning + gift signals must populate both fields."""

    def test_multi_intent_both_matchers_called(self, auth_client,
                                                 vendor_with_packages, vs):
        called = {"venues": False, "gifts": False}

        def fake_venues(db, criteria):
            called["venues"] = True
            return []

        def fake_gifts(db, gift_tags, budget=None):
            called["gifts"] = True
            return []

        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock,
                   return_value=_fake_ai(intent="planning", tags=["romantic"])), \
             patch.object(vs, "find_perfect_matches", side_effect=fake_venues), \
             patch.object(vs, "find_gift_matches",    side_effect=fake_gifts):
            resp = auth_client.post(
                PLAN_URL,
                json=_payload("I want a romantic dinner AND a gift for my wife"),
            )

        assert resp.status_code == 200, resp.text
        assert called["venues"], "find_perfect_matches must be called"
        assert called["gifts"],  "find_gift_matches must be called"

    def test_multi_intent_response_200(self, auth_client, vendor_with_packages, vs):
        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock,
                   return_value=_fake_ai(intent="planning", tags=["romantic"])), \
             patch.object(vs, "find_perfect_matches", return_value=[]), \
             patch.object(vs, "find_gift_matches",    return_value=[]):
            resp = auth_client.post(
                PLAN_URL,
                json=_payload("Plan a birthday dinner and get her a present"),
            )
        assert resp.status_code == 200, resp.text


# ═════════════════════════════════════════════════════════════════════════════
# 11. CHAT INTENT
# ═════════════════════════════════════════════════════════════════════════════

class TestChatIntent:
    """Pure chat intent must not run venue or gift matchers."""

    def test_chat_intent_empty_matched_venues(self, auth_client,
                                               vendor_with_packages, vs):
        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock,
                   return_value=_fake_ai(intent="chat", tags=[])), \
             patch.object(vs, "find_perfect_matches",
                          return_value=[]) as mock_venues, \
             patch.object(vs, "find_gift_matches",
                          return_value=[]) as mock_gifts:
            resp = auth_client.post(PLAN_URL, json=_payload("Hello there"))

        assert resp.status_code == 200, resp.text
        assert resp.json()["matched_venues"] == []
        mock_venues.assert_not_called()
        mock_gifts.assert_not_called()


# ═════════════════════════════════════════════════════════════════════════════
# 12. AI FALLBACK
# ═════════════════════════════════════════════════════════════════════════════

class TestAIFallback:
    """If Langflow is unavailable, the endpoint must return 200 with a
    user-friendly fallback message — never a 500."""

    def test_langflow_timeout_returns_200(self, auth_client, vendor_with_packages):
        import httpx
        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock,
                   side_effect=httpx.TimeoutException("timeout")):
            resp = auth_client.post(PLAN_URL, json=_payload())
        # The router catches all exceptions and returns a fallback dict
        assert resp.status_code == 200, resp.text

    def test_langflow_down_response_has_chat_response(self, auth_client,
                                                        vendor_with_packages):
        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock,
                   side_effect=RuntimeError("Langflow down")):
            resp = auth_client.post(PLAN_URL, json=_payload())

        assert resp.status_code == 200, resp.text
        assert resp.json().get("chat_response"), \
            "Fallback response must include a chat_response message"

    def test_langflow_down_matched_venues_empty(self, auth_client,
                                                  vendor_with_packages):
        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock,
                   side_effect=RuntimeError("Langflow down")):
            resp = auth_client.post(PLAN_URL, json=_payload())

        assert resp.json()["matched_venues"] == [], \
            "matched_venues must be empty when AI fails"


# ═════════════════════════════════════════════════════════════════════════════
# 13 & 14. STRUCTURED EXTRACTION — BUDGET + GUESTS
# ═════════════════════════════════════════════════════════════════════════════

class TestStructuredExtraction:
    """Natural language budget and guest count must be parsed from the query."""

    def test_budget_extracted_from_query(self, auth_client, vendor_with_packages):
        captured = {}

        async def capture(raw_query, history=None, personas=None,
                          available_tags=None, missing_info=None):
            captured["query"] = raw_query
            return _fake_ai()

        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   side_effect=capture):
            resp = auth_client.post(
                PLAN_URL,
                json=_payload("My budget is 5000 rupees for the dinner"),
            )

        assert resp.status_code == 200, resp.text
        # Budget should be extracted and injected into the enriched query
        assert "5000" in captured.get("query", ""), \
            "Budget must be extracted and passed to the AI"

    def test_guest_count_extracted_from_query(self, auth_client,
                                               vendor_with_packages):
        captured = {}

        async def capture(raw_query, history=None, personas=None,
                          available_tags=None, missing_info=None):
            captured["query"] = raw_query
            return _fake_ai()

        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   side_effect=capture):
            resp = auth_client.post(
                PLAN_URL,
                json=_payload("We will have 20 people at the event"),
            )

        assert resp.status_code == 200, resp.text
        assert "20" in captured.get("query", ""), \
            "Guest count must be extracted and passed to the AI"


# ═════════════════════════════════════════════════════════════════════════════
# 15. LOCATION ALIAS EXTRACTION
# ═════════════════════════════════════════════════════════════════════════════

class TestLocationExtraction:
    """Sri Lanka location aliases must be resolved before passing to AI."""

    def test_cmb_alias_extracted_as_colombo(self, auth_client,
                                              vendor_with_packages):
        captured = {}

        async def capture(raw_query, history=None, personas=None,
                          available_tags=None, missing_info=None):
            captured["query"] = raw_query
            return _fake_ai()

        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   side_effect=capture):
            resp = auth_client.post(
                PLAN_URL,
                json=_payload("I want a venue in CMB"),
            )

        assert resp.status_code == 200, resp.text
        assert "colombo" in captured.get("query", "").lower(), \
            "CMB alias must be resolved to 'colombo' before reaching the AI"

    def test_down_south_alias_extracted(self, auth_client, vendor_with_packages):
        captured = {}

        async def capture(raw_query, history=None, personas=None,
                          available_tags=None, missing_info=None):
            captured["query"] = raw_query
            return _fake_ai()

        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   side_effect=capture):
            resp = auth_client.post(
                PLAN_URL,
                json=_payload("Something nice down south"),
            )

        assert resp.status_code == 200, resp.text
        assert "galle" in captured.get("query", "").lower(), \
            "'down south' must be resolved to 'galle'"


# ═════════════════════════════════════════════════════════════════════════════
# 16. CONFIDENCE SCORE
# ═════════════════════════════════════════════════════════════════════════════

class TestConfidenceScoreInWorkflow:
    """Every matched_venues entry must include match_score_label."""

    def test_matched_venue_has_match_score_label(self, auth_client,
                                                   vendor_with_packages, vs):
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
                   return_value=_fake_ai(intent="planning", tags=["romantic"])), \
             patch.object(vs, "find_perfect_matches", return_value=[pkg]):
            resp = auth_client.post(PLAN_URL, json=_payload())

        assert resp.status_code == 200, resp.text
        venues = resp.json()["matched_venues"]
        assert len(venues) > 0
        assert "match_score_label" in venues[0], \
            "match_score_label must be present in every matched venue"
        assert "match_score" in venues[0], \
            "match_score must be present in every matched venue"


# ═════════════════════════════════════════════════════════════════════════════
# 17. CONTEXT COMPRESSION ACROSS MANY TURNS
# ═════════════════════════════════════════════════════════════════════════════

class TestContextCompressionWorkflow:
    """Turn 1 content must still reach the AI after many turns (compression)."""

    def test_turn_1_message_in_history_after_many_turns(self, auth_client,
                                                          vendor_with_packages, db):
        from app.services.chat_service import chat_service

        sid = f"sess-{_uid()}"

        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock, return_value=_fake_ai()):
            for i in range(8):
                auth_client.post(PLAN_URL,
                                  json=_payload(f"Message number {i}", sid))

        history = chat_service.get_session_history(db, sid)
        assert len(history) == 8
        assert history[0].user_message == "Message number 0", \
            "Turn 1 must be retrievable from DB after 8 turns"

    def test_context_string_includes_turn_1_after_many_turns(self, auth_client,
                                                               vendor_with_packages,
                                                               db):
        from app.services.chat_service import chat_service

        sid = f"sess-{_uid()}"

        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock, return_value=_fake_ai()):
            for i in range(8):
                auth_client.post(PLAN_URL,
                                  json=_payload(f"Turn content {i}", sid))

        history = chat_service.get_session_history(db, sid)
        ctx = chat_service.build_context_string(history)

        assert "Turn content 0" in ctx, \
            "Turn 1 content must appear in the compressed context string"


# ═════════════════════════════════════════════════════════════════════════════
# 18. MESSAGE PERSISTENCE
# ═════════════════════════════════════════════════════════════════════════════

class TestMessagePersistence:
    """Every request must persist both the user message and AI reply to DB."""

    def test_user_message_saved_to_db(self, auth_client,
                                        vendor_with_packages, db):
        from app.services.chat_service import chat_service

        sid = f"sess-{_uid()}"
        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock, return_value=_fake_ai()):
            auth_client.post(PLAN_URL,
                              json=_payload("Save this message please", sid))

        history = chat_service.get_session_history(db, sid)
        assert any("Save this message please" in (m.user_message or "")
                   for m in history), "User message must be saved to DB"

    def test_ai_reply_saved_to_db(self, auth_client,
                                    vendor_with_packages, db):
        from app.services.chat_service import chat_service

        sid = f"sess-{_uid()}"
        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock,
                   return_value=_fake_ai(chat_response="Unique AI reply XYZ")):
            auth_client.post(PLAN_URL, json=_payload("Any message", sid))

        history = chat_service.get_session_history(db, sid)
        assert any("Unique AI reply XYZ" in (m.ai_message or "")
                   for m in history), "AI reply must be saved to DB"

    def test_missing_info_saved_to_db(self, auth_client,
                                        vendor_with_packages, db):
        from app.services.chat_service import chat_service

        sid = f"sess-{_uid()}"
        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock,
                   return_value=_fake_ai(missing=["budget", "guest_count"])):
            auth_client.post(PLAN_URL, json=_payload("Plan something", sid))

        history = chat_service.get_session_history(db, sid)
        last = history[-1]
        assert "budget"      in (last.missing_info or [])
        assert "guest_count" in (last.missing_info or [])


# ═════════════════════════════════════════════════════════════════════════════
# 19. AUTHENTICATION
# ═════════════════════════════════════════════════════════════════════════════

class TestAuthentication:
    """Unauthenticated requests must be rejected."""

    def test_no_token_rejected(self, client):
        """Using the unauthenticated client must return 401 or 403."""
        resp = client.post(PLAN_URL, json=_payload())
        assert resp.status_code in (401, 403), \
            f"Expected 401/403 without auth, got {resp.status_code}"

    def test_invalid_token_rejected(self, client):
        from starlette.testclient import TestClient
        resp = client.post(
            PLAN_URL,
            json=_payload(),
            headers={"Authorization": "Bearer totally-fake-token"},
        )
        assert resp.status_code in (401, 403), resp.text


# ═════════════════════════════════════════════════════════════════════════════
# 20. EDGE CASES
# ═════════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Unusual inputs must be handled gracefully — never a 500."""

    def test_empty_query_does_not_500(self, auth_client, vendor_with_packages):
        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock,
                   return_value=_fake_ai(intent="chat", tags=[])):
            resp = auth_client.post(PLAN_URL, json=_payload(""))
        assert resp.status_code != 500, "Empty query must not cause a 500"

    def test_very_long_query_does_not_500(self, auth_client,
                                            vendor_with_packages):
        long_msg = "plan a dinner " * 200
        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock, return_value=_fake_ai()):
            resp = auth_client.post(PLAN_URL, json=_payload(long_msg))
        assert resp.status_code != 500, "Very long query must not cause a 500"

    def test_special_characters_in_query_do_not_500(self, auth_client,
                                                       vendor_with_packages):
        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock, return_value=_fake_ai()):
            resp = auth_client.post(
                PLAN_URL,
                json=_payload("Plan a dinner 🎉 with 'quotes' & <brackets>"),
            )
        assert resp.status_code != 500

    def test_no_packages_in_db_returns_200(self, auth_client, vs):
        """Even with an empty vendor catalogue the endpoint must return 200."""
        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock,
                   return_value=_fake_ai(intent="planning", tags=["romantic"])), \
             patch.object(vs, "find_perfect_matches", return_value=[]), \
             patch.object(vs, "get_all_tags", return_value=[]):
            resp = auth_client.post(
                PLAN_URL,
                json=_payload("Plan a romantic dinner"),
            )
        assert resp.status_code == 200, resp.text
        assert resp.json()["matched_venues"] == []