"""
tests/test_ai_improvements.py

Pytest suite for AI Improvements #2, #3, #4, #5, #6:

  Fix #2 — Structured Persona → Tag Mapping
  Fix #3 — Langflow Timeout + Immediate Fallback
  Fix #4 — Redis Cache TTL (2 h) + Invalidation on Package Update
  Fix #5 — Sri Lanka Location Aliases
  Fix #6 — Multi-Intent Handling (venue + gift in same message)
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
import httpx


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

PLAN_URL = "/api/v1/planning/generate"  # retired — use _chat() helper instead
AUTH_URL = "/api/v1/auth/customers"


def _uid():
    from uuid import uuid4
    return uuid4().hex[:8]


def _create_event(auth_client, title="AI Test Event") -> str:
    r = auth_client.post(
        "/api/v1/customers/events",
        json={"eventType": "Birthday", "title": title},
    )
    assert r.status_code == 201, r.text
    return r.json()["eventId"]


def _chat(auth_client, event_id: str, message="Plan a romantic dinner"):
    return auth_client.post(
        f"/api/v1/customers/events/{event_id}/chat",
        json={"content": message},
    )


def _plan_payload(message="Plan a romantic dinner", session_id=None):
    """Kept for reference only — use _chat() for actual requests."""
    return {
        "session_id": session_id or f"sess-{_uid()}",
        "user_query": message,
    }


def _fake_ai(intent="date", tags=None, missing=None, chat_response="Here is your plan.", gift=None):
    return {
        "intent": intent,
        "venue_tags": tags if tags is not None else ["romantic"],
        "budget_per_head": 150,
        "guest_count": 2,
        "chat_response": chat_response,
        "missing_info": missing if missing is not None else [],
        "gift_suggestion": gift,
        "reasoning": None,
        "personality_profile": None,
        "event_type": None,
        "location": None,
    }


def _persona(
    name="Sarah",
    relationship="sister",
    personality="adventurous",
    food_preferences=None,
    color_preferences=None,
    music_preferences=None,
    personality_tags=None,
    preferences_json=None,   # legacy field
):
    p = MagicMock()
    p.name = name
    p.relationship = relationship
    p.personality = personality
    p.food_preferences = food_preferences
    p.color_preferences = color_preferences
    p.music_preferences = music_preferences
    p.personality_tags = personality_tags
    p.preferences_json = preferences_json
    return p


# ═════════════════════════════════════════════════════════════════════════════
# FIX #2 — Structured Persona Context
# ═════════════════════════════════════════════════════════════════════════════

class TestStructuredPersonaContext:
    """_build_structured_persona_context() must produce a prompt that maps
    preference fields to concrete package tags."""

    # Import inside each method to avoid module-level failures when app not installed
    def _fn(self):
        from app.services.ai_service import _build_structured_persona_context
        return _build_structured_persona_context

    # ── 1. Empty list returns empty string ───────────────────────────────────

    def test_empty_personas_returns_empty_string(self):
        ctx = self._fn()([])
        assert ctx == ""

    # ── 2. Personality tags map to known package tags ────────────────────────

    def test_personality_tags_produce_package_tags(self):
        persona = _persona(personality_tags=["adventure", "outdoor"])
        ctx = self._fn()([persona])

        assert "adventure" in ctx
        assert "outdoor" in ctx
        # Check the mapping output appears
        assert "Suggested package tags" in ctx

    # ── 3. Food preferences map correctly ────────────────────────────────────

    def test_food_preferences_map_to_tags(self):
        persona = _persona(food_preferences=["fine dining"])
        ctx = self._fn()([persona])

        # "fine dining" → ["fine-dining", "luxury"]
        assert "fine-dining" in ctx or "luxury" in ctx

    # ── 4. Color preferences map correctly ───────────────────────────────────

    def test_color_preferences_map_to_tags(self):
        persona = _persona(color_preferences=["red"])
        ctx = self._fn()([persona])

        # "red" → ["romantic", "luxury"]
        assert "romantic" in ctx or "luxury" in ctx

    # ── 5. Music preferences map correctly ───────────────────────────────────

    def test_music_preferences_map_to_tags(self):
        persona = _persona(music_preferences=["jazz"])
        ctx = self._fn()([persona])

        # "jazz" → ["fine-dining", "luxury", "romantic"]
        assert "romantic" in ctx or "fine-dining" in ctx

    # ── 6. Legacy preferences_json fallback still works ──────────────────────

    def test_legacy_preferences_json_fallback(self):
        """When new fields are all None, preferences_json hobbies are used."""
        persona = _persona(preferences_json=["hiking", "nature"])
        ctx = self._fn()([persona])

        # "hiking" → ["adventure", "hiking", "outdoor"] / "nature" → ["nature", ...]
        assert "hiking" in ctx or "nature" in ctx or "outdoor" in ctx

    # ── 7. GLOBAL TAG BIAS section appears ───────────────────────────────────

    def test_global_bias_section_present(self):
        persona = _persona(personality_tags=["romantic", "beach"])
        ctx = self._fn()([persona])

        assert "GLOBAL TAG BIAS" in ctx

    # ── 8. Multiple personas merged correctly ────────────────────────────────

    def test_multiple_personas_merged(self):
        p1 = _persona(name="Alice", personality_tags=["adventure"])
        p2 = _persona(name="Bob",   personality_tags=["wellness"])
        ctx = self._fn()([p1, p2])

        assert "Alice" in ctx
        assert "Bob" in ctx
        # Both tag sets should appear in global bias
        assert "adventure" in ctx
        assert "wellness" in ctx

    # ── 9. Comma-string preferences parsed correctly ──────────────────────────

    def test_comma_string_preferences_parsed(self):
        """Fields may arrive as comma-separated strings from the DB."""
        persona = _persona(personality_tags="romantic, beach, outdoor")
        ctx = self._fn()([persona])

        assert "romantic" in ctx
        assert "beach" in ctx

    # ── 10. CRITICAL instruction present in prompt ───────────────────────────

    def test_critical_instruction_in_prompt(self):
        """AI must be told to PRIORITISE the suggested tags."""
        persona = _persona(personality_tags=["adventure"])
        ctx = self._fn()([persona])

        assert "PRIORITISE" in ctx or "CRITICAL" in ctx

    # ── 11. generate_date_plan uses structured context (integration check) ───

    @pytest.mark.asyncio
    async def test_generate_date_plan_uses_structured_persona(self):
        """generate_date_plan should call _build_structured_persona_context."""
        from app.services.ai_service import AIService, _build_structured_persona_context

        service = AIService()
        persona = _persona(personality_tags=["romantic"])

        captured = {}

        def _fake_build(personas):
            captured["called"] = True
            captured["personas"] = personas
            return "FAKE_PERSONA_CTX"

        with patch("app.services.ai_service._build_structured_persona_context",
                   side_effect=_fake_build) as mock_build:

            # Build a valid Groq-format mock response
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = {
                "choices": [{
                    "message": {
                        "content": json.dumps({
                            "intent": "planning",
                            "venue_tags": ["romantic"],
                            "missing_info": [],
                            "chat_response": "Great! Let me help you plan something romantic.",
                            "gift_suggestion": None,
                            "gift_category": None,
                        })
                    }
                }]
            }

            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_response)

            with patch("httpx.AsyncClient", return_value=mock_client), \
                 patch("app.services.ai_service._get_redis", return_value=None):
                # Provide a dummy key so the service doesn't fail on missing key
                service.groq_api_key = "test-key"
                await service.generate_date_plan(
                    raw_query="Plan something romantic",
                    personas=[persona],
                )

        assert captured.get("called"), (
            "_build_structured_persona_context was not called — "
            "generate_date_plan is still using the old text-blob approach"
        )


# ═════════════════════════════════════════════════════════════════════════════
# FIX #3 — Langflow Timeout + Immediate Fallback
# ═════════════════════════════════════════════════════════════════════════════

class TestLangflowTimeout:
    """generate_date_plan must return a friendly fallback dict when Groq
    times out, and must NOT raise an exception to the caller."""

    def _service(self):
        from app.services.ai_service import AIService
        svc = AIService()
        svc.groq_api_key = "test-key"   # provide a key so the guard doesn't fire
        svc.base_url  = "http://fake-langflow"
        svc.token     = "fake-token"
        svc.org_id    = "fake-org"
        return svc

    # ── 1. TimeoutException returns fallback without raising ─────────────────

    @pytest.mark.asyncio
    async def test_timeout_returns_fallback_not_raises(self):
        svc = self._service()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("timed out"))

        with patch("httpx.AsyncClient", return_value=mock_client), \
             patch("app.services.ai_service._get_redis", return_value=None):
            result = await svc.generate_date_plan("Plan a birthday party")

        assert isinstance(result, dict), "Fallback must return a dict"
        assert result["intent"] == "chat"
        assert "venue_tags" in result
        assert result["venue_tags"] == []

    # ── 2. Fallback chat_response is user-friendly ───────────────────────────

    @pytest.mark.asyncio
    async def test_timeout_fallback_has_friendly_message(self):
        svc = self._service()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("timed out"))

        with patch("httpx.AsyncClient", return_value=mock_client), \
             patch("app.services.ai_service._get_redis", return_value=None):
            result = await svc.generate_date_plan("Plan a birthday party")

        chat = result.get("chat_response", "")
        assert len(chat) > 10, "Fallback chat_response should be a real message"

    # ── 3. Client is created with timeout=25.0 ───────────────────────────────

    @pytest.mark.asyncio
    async def test_client_uses_25_second_timeout(self):
        """httpx.AsyncClient must be instantiated with timeout=25.0."""
        svc = self._service()

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "intent": "chat",
                        "venue_tags": [],
                        "missing_info": [],
                        "chat_response": "Hello!",
                    })
                }
            }]
        }

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client) as mock_cls, \
             patch("app.services.ai_service._get_redis", return_value=None):
            await svc.generate_date_plan("Hello")

        # Check AsyncClient was instantiated with timeout=25.0
        mock_cls.assert_called_once_with(timeout=25.0)

    # ── 4. Non-timeout errors still propagate ────────────────────────────────

    @pytest.mark.asyncio
    async def test_non_timeout_errors_still_raise(self):
        """A 500 HTTPStatusError should still propagate (not be swallowed like a timeout).
        Tenacity may wrap it in RetryError after exhausting retries — either is acceptable."""
        from tenacity import RetryError

        svc = self._service()

        mock_response = MagicMock()
        mock_response.status_code = 500
        http_err = httpx.HTTPStatusError(
            "Server error", request=MagicMock(), response=mock_response
        )

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(side_effect=http_err)

        with patch("httpx.AsyncClient", return_value=mock_client), \
             patch("app.services.ai_service._get_redis", return_value=None):
            with pytest.raises((httpx.HTTPStatusError, RetryError)):
                await svc.generate_date_plan("Hello")


# ═════════════════════════════════════════════════════════════════════════════
# FIX #4 — Redis Cache TTL + Invalidation
# ═════════════════════════════════════════════════════════════════════════════

class TestRedisCacheTTL:
    """AI responses must be cached with a 2-hour (7200 s) TTL."""

    def _service(self):
        from app.services.ai_service import AIService
        svc = AIService()
        svc.groq_api_key = "test-key"   # provide a key so the guard doesn't fire
        svc.base_url  = "http://fake-langflow"
        svc.token     = "fake-token"
        svc.org_id    = "fake-org"
        return svc

    def _good_groq_response(self):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "intent": "planning",
                        "venue_tags": ["romantic"],
                        "missing_info": [],
                        "chat_response": "Here is your plan.",
                    })
                }
            }]
        }
        return mock_response

    # ── 1. setex called with 7200 (2 hours) ──────────────────────────────────

    @pytest.mark.asyncio
    async def test_cache_ttl_is_7200_seconds(self):
        svc = self._service()

        mock_redis = MagicMock()
        mock_redis.get.return_value = None   # no cache hit
        mock_redis.setex = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=self._good_groq_response())

        with patch("httpx.AsyncClient", return_value=mock_client), \
             patch("app.services.ai_service._get_redis", return_value=mock_redis):
            await svc.generate_date_plan("Plan a wedding")

        assert mock_redis.setex.called, "setex must be called to cache the response"
        ttl_used = mock_redis.setex.call_args[0][1]
        assert ttl_used == 7200, f"Expected TTL=7200 s (2 h), got {ttl_used} s"

    # ── 2. Cache hit avoids Groq call ────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_cache_hit_skips_langflow(self):
        svc = self._service()

        cached_payload = json.dumps({"intent": "planning", "venue_tags": ["romantic"], "missing_info": []})
        mock_redis = MagicMock()
        mock_redis.get.return_value = cached_payload

        with patch("app.services.ai_service._get_redis", return_value=mock_redis), \
             patch("httpx.AsyncClient") as mock_cls:
            result = await svc.generate_date_plan("Plan a wedding")

        mock_cls.assert_not_called()
        assert result["intent"] == "planning"

    # ── 3. Old TTL of 300 s is NOT used ──────────────────────────────────────

    @pytest.mark.asyncio
    async def test_old_300s_ttl_not_used(self):
        svc = self._service()

        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        mock_redis.setex = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=self._good_groq_response())

        with patch("httpx.AsyncClient", return_value=mock_client), \
             patch("app.services.ai_service._get_redis", return_value=mock_redis):
            await svc.generate_date_plan("Plan a birthday")

        ttl_used = mock_redis.setex.call_args[0][1]
        assert ttl_used != 300, "Old 5-minute TTL should have been replaced with 7200 s"


class TestCacheInvalidation:
    """update_package() and create_package() must flush ai_cache:* keys."""

    def _pkg_data(self):
        d = MagicMock()
        d.name = "Romantic Dinner"
        d.description = "A lovely dinner"
        d.price = 5000
        d.price_per_head = 500
        d.tags = ["romantic"]
        d.location_coverage = "colombo"
        d.blocked_dates = []
        return d

    # ── 4. update_package calls _flush_ai_cache ───────────────────────────────

    def test_update_package_flushes_cache(self):
        from app.services.vendor_service import vendor_service, _flush_ai_cache

        db = MagicMock()
        existing_pkg = MagicMock()
        existing_pkg.id = 1
        db.query.return_value.filter.return_value.first.return_value = existing_pkg

        with patch("app.services.vendor_service._flush_ai_cache") as mock_flush:
            vendor_service.update_package(db, 1, self._pkg_data())

        mock_flush.assert_called_once(), "update_package must call _flush_ai_cache()"

    # ── 5. create_package calls _flush_ai_cache ───────────────────────────────

    def test_create_package_flushes_cache(self):
        from app.services.vendor_service import vendor_service

        db = MagicMock()
        new_pkg = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock(side_effect=lambda obj: None)

        with patch("app.services.vendor_service._flush_ai_cache") as mock_flush:
            vendor_service.create_package(db, vendor_id=1, package_data=self._pkg_data())

        mock_flush.assert_called_once(), "create_package must call _flush_ai_cache()"

    # ── 6. _flush_ai_cache deletes keys matching ai_cache:* ──────────────────

    def test_flush_ai_cache_deletes_correct_keys(self):
        from app.services.vendor_service import _flush_ai_cache

        mock_redis_client = MagicMock()
        mock_redis_client.ping = MagicMock()
        mock_redis_client.keys.return_value = ["ai_cache:abc123", "ai_cache:def456"]
        mock_redis_client.delete = MagicMock(return_value=2)

        mock_redis_lib = MagicMock()
        mock_redis_lib.from_url.return_value = mock_redis_client

        with patch.dict("sys.modules", {"redis": mock_redis_lib}), \
             patch("app.services.vendor_service.settings", create=True):
            deleted = _flush_ai_cache()

        mock_redis_client.keys.assert_called_with("ai_cache:*")
        mock_redis_client.delete.assert_called_once_with("ai_cache:abc123", "ai_cache:def456")
        assert deleted == 2

    # ── 7. _flush_ai_cache returns 0 when no keys exist ──────────────────────

    def test_flush_ai_cache_no_keys_returns_zero(self):
        from app.services.vendor_service import _flush_ai_cache

        mock_redis_client = MagicMock()
        mock_redis_client.ping = MagicMock()
        mock_redis_client.keys.return_value = []

        mock_redis_lib = MagicMock()
        mock_redis_lib.from_url.return_value = mock_redis_client

        with patch.dict("sys.modules", {"redis": mock_redis_lib}), \
             patch("app.services.vendor_service.settings", create=True):
            result = _flush_ai_cache()

        mock_redis_client.delete.assert_not_called()
        assert result == 0

    # ── 8. _flush_ai_cache is silent when Redis is unavailable ───────────────

    def test_flush_ai_cache_silent_on_redis_unavailable(self):
        """If redis module itself is missing, _flush_ai_cache must not raise."""
        from app.services.vendor_service import _flush_ai_cache

        with patch.dict("sys.modules", {"redis": None}):
            result = _flush_ai_cache()   # must not raise

        assert result == 0


# ═════════════════════════════════════════════════════════════════════════════
# FIX #5 — Sri Lanka Location Aliases
# ═════════════════════════════════════════════════════════════════════════════

class TestLocationAliases:
    """_CITY_ALIASES and extract_location_from_text() must recognise common
    Sri Lanka shorthand inputs and map them to canonical city names."""

    def _extract(self, text: str):
        from app.services.vendor_service import vendor_service
        return vendor_service.extract_location_from_text(text)

    def _normalise(self, raw: str):
        from app.services.vendor_service import _normalise_city
        return _normalise_city(raw)

    # ── Colombo variants ─────────────────────────────────────────────────────

    def test_cmb_maps_to_colombo(self):
        assert self._extract("I want a venue in CMB") == "colombo"

    def test_col_maps_to_colombo(self):
        assert self._extract("somewhere in col") == "colombo"

    def test_exact_colombo_still_works(self):
        assert self._extract("venue in Colombo") == "colombo"

    # ── Kandy variants ───────────────────────────────────────────────────────

    def test_kandy_city_maps_to_kandy(self):
        assert self._extract("looking for something in Kandy city") == "kandy"

    def test_candy_typo_maps_to_kandy(self):
        assert self._extract("a venue in candy") == "kandy"

    def test_hill_country_maps_to_kandy(self):
        assert self._extract("in the hill country") == "kandy"

    # ── Galle / South variants ───────────────────────────────────────────────

    def test_down_south_maps_to_galle(self):
        assert self._extract("we're going down south") == "galle"

    def test_the_south_maps_to_galle(self):
        assert self._extract("somewhere in the south") == "galle"

    def test_near_galle_maps_to_galle(self):
        assert self._extract("near Galle, please") == "galle"

    def test_galle_fort_maps_to_galle(self):
        assert self._extract("inside galle fort") == "galle"

    def test_south_coast_maps_to_galle(self):
        assert self._extract("south coast venue") == "galle"

    # ── Other cities ─────────────────────────────────────────────────────────

    def test_trinco_maps_to_trincomalee(self):
        assert self._extract("planning in trinco") == "trincomalee"

    def test_east_coast_maps_to_trincomalee(self):
        assert self._extract("east coast trip") == "trincomalee"

    def test_little_england_maps_to_nuwara_eliya(self):
        assert self._extract("going to little england") == "nuwara eliya"

    def test_nuwaraeliya_no_space(self):
        assert self._normalise("nuwaraeliya") == "nuwara eliya"

    def test_hikka_maps_to_hikkaduwa(self):
        assert self._extract("beach party at hikka") == "hikkaduwa"

    def test_near_airport_maps_to_negombo(self):
        assert self._extract("somewhere near airport") == "negombo"

    def test_lion_rock_maps_to_sigiriya(self):
        assert self._extract("near lion rock") == "sigiriya"

    def test_nine_arches_maps_to_ella(self):
        assert self._extract("by the nine arches") == "ella"

    # ── Edge cases ───────────────────────────────────────────────────────────

    def test_no_location_returns_none(self):
        assert self._extract("I want a nice party") is None

    def test_longest_alias_wins(self):
        """'kandy city' (longer) should take priority over plain 'kandy'."""
        result = self._extract("event in Kandy city please")
        assert result == "kandy"

    def test_case_insensitive_matching(self):
        assert self._extract("Venue in CMB please") == "colombo"
        assert self._extract("DOWN SOUTH escape") == "galle"


# ═════════════════════════════════════════════════════════════════════════════
# FIX #6 — Multi-Intent Handling
# ═════════════════════════════════════════════════════════════════════════════

class TestMultiIntentHandling:
    """When a message contains BOTH a planning signal AND a gift signal,
    the router must run both find_perfect_matches AND find_gift_matches
    and return both matched_venues and gift_suggestion populated."""

    @pytest.fixture()
    def vs(self):
        from app.services.vendor_service import vendor_service
        return vendor_service

    # ── Signal detection unit tests (no DB needed) ───────────────────────────

    def test_combined_message_triggers_both_signals(self):
        """A message with 'dinner' + 'gift' must set both signal flags."""
        query = "I want a romantic dinner AND a gift for my wife"
        lower = query.lower()
        gift_signals = ["gift", "present", "buy", "surprise", "something for", "get her", "get him"]
        plan_signals = ["venue", "dinner", "restaurant", "party", "book", "plan", "celebrate",
                        "event", "wedding", "birthday", "anniversary", "arrange", "find a place"]
        assert any(s in lower for s in gift_signals), "Gift signal missing"
        assert any(s in lower for s in plan_signals), "Plan signal missing"

    def test_pure_planning_message_has_no_gift_signal(self):
        query = "I want a romantic dinner in Colombo for two"
        lower = query.lower()
        gift_signals = ["gift", "present", "buy", "surprise", "something for", "get her", "get him"]
        assert not any(s in lower for s in gift_signals)

    def test_pure_gift_message_has_no_plan_signal(self):
        query = "I want to buy a present for my wife"
        lower = query.lower()
        plan_signals = ["venue", "dinner", "restaurant", "party", "book", "plan", "celebrate",
                        "event", "wedding", "birthday", "anniversary", "arrange", "find a place"]
        assert not any(s in lower for s in plan_signals)

    def test_surprise_party_triggers_both_signals(self):
        query = "I want to surprise her with a party and a gift"
        lower = query.lower()
        gift_signals = ["gift", "present", "buy", "surprise", "something for", "get her", "get him"]
        plan_signals = ["venue", "dinner", "restaurant", "party", "book", "plan", "celebrate",
                        "event", "wedding", "birthday", "anniversary", "arrange", "find a place"]
        assert any(s in lower for s in gift_signals)
        assert any(s in lower for s in plan_signals)

    # ── Integration: both matchers called ────────────────────────────────────

    def test_multi_intent_calls_both_matchers(self, auth_client, vendor_with_packages, vs):
        """Router must call BOTH find_perfect_matches AND find_gift_matches
        when multi-intent is detected."""
        captured = {"venues": False, "gifts": False}

        def fake_venues(db, criteria):
            captured["venues"] = True
            return []

        def fake_gifts(db, gift_tags, budget=None):
            captured["gifts"] = True
            return []

        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock,
                   return_value=_fake_ai(intent="planning", tags=["romantic"])), \
             patch.object(vs, "find_perfect_matches", side_effect=fake_venues), \
             patch.object(vs, "find_gift_matches",    side_effect=fake_gifts):
            event_id = _create_event(auth_client)
            resp = _chat(auth_client, event_id, "I want a romantic dinner AND a gift for my wife")

        assert resp.status_code == 200, resp.text
        assert captured["venues"], "find_perfect_matches must be called for multi-intent"
        assert captured["gifts"],  "find_gift_matches must be called for multi-intent"

    # ── Integration: matched_venues populated ────────────────────────────────

    def test_multi_intent_populates_matched_venues(self, auth_client, vendor_with_packages, vs):
        """matched_venues must be non-empty when multi-intent venue match succeeds."""
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
             patch.object(vs, "find_perfect_matches", return_value=[pkg]), \
             patch.object(vs, "find_gift_matches",    return_value=[]):
            event_id = _create_event(auth_client)
            resp = _chat(auth_client, event_id, "I want a romantic dinner AND a gift for my wife")

        assert resp.status_code == 200, resp.text
        assert len(resp.json().get("matchedVenues", [])) > 0, \
            "matchedVenues must be populated in a multi-intent response"

    # ── Integration: gift_suggestion populated ────────────────────────────────

    def test_multi_intent_populates_gift_suggestion(self, auth_client, vendor_with_packages, vs):
        """gift_suggestion must be non-None when multi-intent gift match succeeds."""
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
                   return_value=_fake_ai(intent="planning", tags=["romantic"], gift=None)), \
             patch.object(vs, "find_perfect_matches", return_value=[]), \
             patch.object(vs, "find_gift_matches",    return_value=[pkg]):
            event_id = _create_event(auth_client)
            resp = _chat(auth_client, event_id, "I want a romantic dinner AND a gift for my wife")

        assert resp.status_code == 200, resp.text
        assert resp.json().get("giftSuggestion") is not None, \
            "giftSuggestion must be populated in a multi-intent response"

    # ── Integration: pure planning does NOT populate gift_suggestion ──────────

    def test_pure_planning_no_gift_suggestion(self, auth_client, vendor_with_packages, vs):
        """A pure planning message must leave gift_suggestion as None."""
        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock,
                   return_value=_fake_ai(intent="planning", tags=["romantic"], gift=None)), \
             patch.object(vs, "find_perfect_matches", return_value=[]), \
             patch.object(vs, "find_gift_matches",    return_value=[]) as mock_gift:
            event_id = _create_event(auth_client)
            resp = _chat(auth_client, event_id, "I want a romantic dinner in Colombo")

        assert resp.status_code == 200, resp.text
        assert resp.json().get("giftSuggestion") is None, \
            "Pure planning message must not produce a giftSuggestion"
        mock_gift.assert_not_called()

    # ── Integration: pure gift does NOT run venue matching ────────────────────

    def test_pure_gift_no_venue_matching(self, auth_client, vendor_with_packages, vs):
        """A pure gift intent must not call find_perfect_matches."""
        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock,
                   return_value=_fake_ai(intent="gift", tags=["nature"])), \
             patch.object(vs, "find_perfect_matches", return_value=[]) as mock_venues, \
             patch.object(vs, "find_gift_matches",    return_value=[]):
            event_id = _create_event(auth_client)
            resp = _chat(auth_client, event_id, "Buy a gift for a nature lover")

        assert resp.status_code == 200, resp.text
        mock_venues.assert_not_called()


# ═════════════════════════════════════════════════════════════════════════════
# FIX #7 — Conversation Context Compression
# ═════════════════════════════════════════════════════════════════════════════

class TestContextCompression:
    """build_context_string() must:
       - return everything verbatim for short histories (≤ 6 turns)
       - anchor turn 1 verbatim for long histories (original requirements)
       - compress middle turns into a summary
       - always keep the last 5 turns verbatim
       - never grow unboundedly regardless of history length
    """

    def _svc(self):
        from app.services.chat_service import chat_service
        return chat_service

    def _msg(self, user="hello", ai="hi"):
        m = MagicMock()
        m.user_message = user
        m.ai_message   = ai
        m.missing_info = []
        return m

    # ── 1. Empty history → empty string ──────────────────────────────────────

    def test_empty_history_returns_empty_string(self):
        assert self._svc().build_context_string([]) == ""

    # ── 2. Short history (≤ 6 turns) → all verbatim ──────────────────────────

    def test_short_history_all_verbatim(self):
        history = [self._msg(f"user {i}", f"ai {i}") for i in range(4)]
        ctx = self._svc().build_context_string(history)

        assert "CONVERSATION HISTORY:" in ctx
        for i in range(4):
            assert f"user {i}" in ctx
            assert f"ai {i}" in ctx

    # ── 3. Single turn included verbatim ─────────────────────────────────────

    def test_single_turn_verbatim(self):
        history = [self._msg("birthday party for 20 in Colombo", "Great!")]
        ctx = self._svc().build_context_string(history)
        assert "birthday party for 20 in Colombo" in ctx

    # ── 4. Long history → turn 1 always present ──────────────────────────────

    def test_turn_1_always_anchored_in_long_history(self):
        history = [self._msg(f"user {i}", f"ai {i}") for i in range(12)]
        ctx = self._svc().build_context_string(history)

        assert "user 0" in ctx, "Turn 1 user message must always appear"
        assert "ai 0"   in ctx, "Turn 1 AI message must always appear"

    # ── 5. Long history → ORIGINAL REQUIREMENTS label present ────────────────

    def test_original_requirements_label_present(self):
        history = [self._msg(f"u{i}", f"a{i}") for i in range(10)]
        ctx = self._svc().build_context_string(history)
        assert "ORIGINAL REQUIREMENTS" in ctx

    # ── 6. Long history → last 5 turns verbatim ──────────────────────────────

    def test_last_5_turns_always_verbatim(self):
        history = [self._msg(f"user {i}", f"ai {i}") for i in range(12)]
        ctx = self._svc().build_context_string(history)

        for i in range(7, 12):   # last 5 of 12 = indices 7–11
            assert f"user {i}" in ctx, f"Recent turn {i} must be verbatim"
            assert f"ai {i}"   in ctx, f"Recent turn {i} must be verbatim"

    # ── 7. Long history → middle turns NOT verbatim ──────────────────────────

    def test_middle_turns_compressed_not_verbatim(self):
        history = [self._msg(f"user {i}", f"ai {i}") for i in range(12)]
        ctx = self._svc().build_context_string(history)

        # turns 1–6 are middle (turn 0 is anchored, 7–11 are recent)
        for i in range(2, 7):
            assert f"user {i}" not in ctx, \
                f"Middle turn {i} should be compressed, not verbatim"

    # ── 8. Long history → summary section present ────────────────────────────

    def test_summary_section_present_for_long_history(self):
        history = [self._msg(f"u{i}", f"a{i}") for i in range(12)]
        ctx = self._svc().build_context_string(history)
        assert "SUMMARY" in ctx.upper()

    # ── 9. Context size is bounded for very long history ─────────────────────

    def test_context_size_bounded_for_100_turns(self):
        from app.services.chat_service import CONTEXT_RECENT_TURNS
        history = [self._msg(f"user turn {i} " * 20, f"ai turn {i} " * 20)
                   for i in range(100)]

        ctx = self._svc().build_context_string(history)

        # generous upper bound: turn-1 + summary line + 5 recent turns, each ~220 chars
        max_expected = (CONTEXT_RECENT_TURNS + 3) * 2 * 250
        assert len(ctx) < max_expected, (
            f"Compressed context ({len(ctx)} chars) exceeds expected max "
            f"({max_expected} chars) — compression not working"
        )

    # ── 10. CONTEXT_RECENT_TURNS constant equals 5 ───────────────────────────

    def test_context_recent_turns_constant_is_5(self):
        from app.services.chat_service import CONTEXT_RECENT_TURNS
        assert CONTEXT_RECENT_TURNS == 5, \
            f"Expected CONTEXT_RECENT_TURNS=5, got {CONTEXT_RECENT_TURNS}"

    # ── 11. Summary extracts budget fact from middle turns ───────────────────

    def test_summary_extracts_budget_from_middle_turns(self):
        history = (
            [self._msg("plan a dinner", "sure")] +          # turn 1
            [self._msg("budget is 5000 rupees", "noted")] + # middle (will be summarised)
            [self._msg(f"u{i}", f"a{i}") for i in range(5)] # last 5 (verbatim)
        )
        ctx = self._svc().build_context_string(history)
        # The word "budget" or "5000" should survive compression into the summary
        assert "budget" in ctx.lower() or "5000" in ctx, \
            "Budget fact from middle turn must appear in the compressed summary"

    # ── 12. Summary extracts location fact from middle turns ─────────────────

    def test_summary_extracts_location_from_middle_turns(self):
        history = (
            [self._msg("plan an event", "sure")] +              # turn 1
            [self._msg("we want it in colombo", "got it")] +    # middle
            [self._msg(f"u{i}", f"a{i}") for i in range(5)]    # last 5
        )
        ctx = self._svc().build_context_string(history)
        assert "colombo" in ctx.lower(), \
            "Location fact from middle turn must appear in the compressed summary"


# ═════════════════════════════════════════════════════════════════════════════
# FIX #8 — Confidence Score on Venue Matches
# ═════════════════════════════════════════════════════════════════════════════

class TestConfidenceScore:
    """_package_to_dict() must compute match_score, match_score_max, and
    match_score_label for every venue in matched_venues so the UI can show
    e.g. '3 of 4 tags matched' instead of every result looking identical."""

    @pytest.fixture()
    def vs(self):
        from app.services.vendor_service import vendor_service
        return vendor_service

    def _pkg(self, tags, name="Test Package"):
        p = MagicMock()
        p.id = 1
        p.name = name
        p.description = "desc"
        p.price = 5000
        p.price_per_head = 500
        p.tags = tags
        p.location_coverage = "colombo"
        p.vendor = MagicMock()
        p.vendor.display_name = "Vendor"
        p.vendor.business_name = "Vendor Co"
        return p

    def _to_dict(self, pkg, requested_tags=None):
        from app.routers.v1.planning_router import _package_to_dict
        return _package_to_dict(pkg, requested_tags=requested_tags)

    # ── 1. Full match → score equals total ───────────────────────────────────

    def test_full_tag_match_score(self):
        pkg = self._pkg(["romantic", "fine-dining", "luxury"])
        d = self._to_dict(pkg, requested_tags=["romantic", "fine-dining", "luxury"])

        assert d["match_score"]     == 3
        assert d["match_score_max"] == 3
        assert d["match_score_label"] == "3 of 3 tags matched"

    # ── 2. Partial match → correct fraction ──────────────────────────────────

    def test_partial_tag_match_score(self):
        pkg = self._pkg(["romantic"])
        d = self._to_dict(pkg, requested_tags=["romantic", "fine-dining", "luxury"])

        assert d["match_score"]     == 1
        assert d["match_score_max"] == 3
        assert d["match_score_label"] == "1 of 3 tags matched"

    # ── 3. Zero match → score is 0 ───────────────────────────────────────────

    def test_zero_tag_match_score(self):
        pkg = self._pkg(["beach", "outdoor"])
        d = self._to_dict(pkg, requested_tags=["romantic", "fine-dining"])

        assert d["match_score"]     == 0
        assert d["match_score_max"] == 2
        assert d["match_score_label"] == "0 of 2 tags matched"

    # ── 4. No requested_tags → fields are None ───────────────────────────────

    def test_no_requested_tags_returns_none_fields(self):
        pkg = self._pkg(["romantic"])
        d = self._to_dict(pkg, requested_tags=None)

        assert d["match_score"]       is None
        assert d["match_score_max"]   is None
        assert d["match_score_label"] is None

    # ── 5. Label format is human-readable ────────────────────────────────────

    def test_label_is_human_readable_string(self):
        pkg = self._pkg(["romantic", "luxury"])
        d = self._to_dict(pkg, requested_tags=["romantic", "luxury", "beach"])

        label = d["match_score_label"]
        assert isinstance(label, str)
        assert "of" in label
        assert "matched" in label

    # ── 6. match_score fields present in endpoint response ───────────────────

    def test_match_score_present_in_api_response(self, auth_client, vendor_with_packages, vs):
        """The /planning/generate response must include match_score_label
        in every matched_venues entry."""
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
             patch.object(vs, "find_perfect_matches", return_value=[pkg]), \
             patch.object(vs, "get_all_tags", return_value=["romantic"]), \
             patch.object(vs, "get_availability_block", return_value=""):
            event_id = _create_event(auth_client)
            resp = _chat(auth_client, event_id, "Plan a romantic dinner in Colombo")

        assert resp.status_code == 200, resp.text
        venues = resp.json().get("matchedVenues", [])
        assert len(venues) > 0, "Expected at least one matched venue"
        first = venues[0]
        assert "matchScoreLabel" in first or "match_score_label" in first, \
            "match_score_label must be present in each matched venue"
        assert "matchScore" in first or "match_score" in first, \
            "matchScore must be present in each matched venue"
        assert "matchScoreMax" in first or "match_score_max" in first, \
            "matchScoreMax must be present in each matched venue"

    # ── 7. Better match has higher score than worse match ────────────────────

    def test_better_match_has_higher_score(self):
        requested = ["romantic", "fine-dining", "luxury"]
        full_match    = self._pkg(["romantic", "fine-dining", "luxury"], "Full")
        partial_match = self._pkg(["romantic"],                           "Partial")

        d_full    = self._to_dict(full_match,    requested_tags=requested)
        d_partial = self._to_dict(partial_match, requested_tags=requested)

        assert d_full["match_score"] > d_partial["match_score"], \
            "Full match must have higher match_score than partial match"