"""
tests/test_ai_improvements.py

Pytest suite for AI Improvements #2, #3, #4:

  Fix #2 — Structured Persona → Tag Mapping
            _build_structured_persona_context() reads food_preferences,
            color_preferences, music_preferences, personality_tags and
            maps them to known package tags via _PREFERENCE_TO_TAGS.

  Fix #3 — Langflow Timeout + Immediate Fallback
            httpx.AsyncClient(timeout=25.0); TimeoutException returns a
            safe fallback dict without raising.

  Fix #4 — Redis Cache TTL (2 h) + Invalidation on Package Update
            setex uses 7200 s; update_package() and create_package()
            call _flush_ai_cache() which deletes ai_cache:* keys.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
import httpx


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

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

    from app.services.ai_service import _build_structured_persona_context  # type: ignore

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
        """generate_date_plan should call _build_structured_persona_context
        (not the old persona_service.build_persona_context)."""
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
            # Make Langflow call fail immediately so we don't need network
            with patch.object(service, "base_url", "http://fake"), \
                 patch.object(service, "token", "tok"), \
                 patch.object(service, "org_id", "org"):

                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()
                mock_response.json.return_value = {
                    "outputs": [{
                        "outputs": [{
                            "results": {
                                "message": {
                                    "text": json.dumps({
                                        "intent": "planning",
                                        "venue_tags": ["romantic"],
                                        "missing_info": [],
                                    })
                                }
                            }
                        }]
                    }]
                }

                with patch("httpx.AsyncClient") as mock_client_cls:
                    mock_client = AsyncMock()
                    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                    mock_client.__aexit__ = AsyncMock(return_value=False)
                    mock_client.post = AsyncMock(return_value=mock_response)
                    mock_client_cls.return_value = mock_client

                    with patch("app.services.ai_service._get_redis", return_value=None):
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
    """generate_date_plan must return a friendly fallback dict when Langflow
    times out, and must NOT raise an exception to the caller."""

    def _service(self):
        from app.services.ai_service import AIService
        svc = AIService()
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
            "outputs": [{
                "outputs": [{
                    "results": {
                        "message": {
                            "text": json.dumps({
                                "intent": "chat",
                                "venue_tags": [],
                                "missing_info": [],
                            })
                        }
                    }
                }]
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
        svc.base_url  = "http://fake-langflow"
        svc.token     = "fake-token"
        svc.org_id    = "fake-org"
        return svc

    def _good_langflow_response(self):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "outputs": [{
                "outputs": [{
                    "results": {
                        "message": {
                            "text": json.dumps({
                                "intent": "planning",
                                "venue_tags": ["romantic"],
                                "missing_info": [],
                            })
                        }
                    }
                }]
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
        mock_client.post = AsyncMock(return_value=self._good_langflow_response())

        with patch("httpx.AsyncClient", return_value=mock_client), \
             patch("app.services.ai_service._get_redis", return_value=mock_redis):
            await svc.generate_date_plan("Plan a wedding")

        assert mock_redis.setex.called, "setex must be called to cache the response"
        ttl_used = mock_redis.setex.call_args[0][1]
        assert ttl_used == 7200, f"Expected TTL=7200 s (2 h), got {ttl_used} s"

    # ── 2. Cache hit avoids Langflow call ────────────────────────────────────

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
        mock_client.post = AsyncMock(return_value=self._good_langflow_response())

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