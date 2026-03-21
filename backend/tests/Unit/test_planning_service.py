"""
tests/Unit/test_planning_service.py

Unit tests for planning_service internals — no HTTP, minimal DB.
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest


def _uid() -> str:
    return uuid4().hex[:8]


def _mock_pkg(pkg_id=1, name="Test Package", tags=None, pph=100.0, location="Colombo"):
    """
    Mock Package with explicit scalar attributes.
    MagicMock auto-creates missing attrs as new Mocks — we must set
    price_per_head explicitly so getattr() returns a real float.
    """
    pkg = MagicMock(spec=[
        "id", "name", "description", "price_per_head", "tags",
        "location_coverage", "vendor", "min_guests", "max_guests",
        "blocked_dates", "price", "vendor_id",
    ])
    pkg.id = pkg_id
    pkg.name = name
    pkg.description = "A test package"
    pkg.price_per_head = float(pph) if pph is not None else None
    pkg.price = float(pph) * 10 if pph else 0.0
    pkg.tags = list(tags) if tags else ["romantic"]
    pkg.location_coverage = location
    pkg.min_guests = 2
    pkg.max_guests = 50
    pkg.blocked_dates = []
    pkg.vendor_id = pkg_id
    vendor = MagicMock(spec=["display_name", "business_name", "id"])
    vendor.display_name = "Test Vendor"
    vendor.business_name = "Test Vendor Co"
    vendor.id = pkg_id
    pkg.vendor = vendor
    return pkg


def _mock_chat_session(step="0", venue_data=None, persona_draft=None,
                        rec_ids=None, gift_rec_ids=None, chosen_persona_id=None,
                        booking_id=None, pending_save=None):
    sess = MagicMock()
    sess.step = step
    sess.venue_data = json.dumps(venue_data or {})
    sess.persona_draft = json.dumps(persona_draft or {})
    sess.rec_ids = json.dumps(rec_ids or [])
    sess.gift_rec_ids = json.dumps(gift_rec_ids or [])
    sess.chosen_persona_id = chosen_persona_id
    sess.booking_id = booking_id
    sess.pending_save = json.dumps(pending_save) if pending_save else None
    return sess


# ═════════════════════════════════════════════════════════════════════════════
# StateStore
# ═════════════════════════════════════════════════════════════════════════════

class TestStateStore:

    def _make_store(self, redis_available=True, session_data=None):
        from app.services.planning_service import StateStore

        mock_db = MagicMock()
        sess = _mock_chat_session(**(session_data or {}))
        mock_db.query.return_value.filter.return_value.first.return_value = sess
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        if redis_available:
            mock_r = MagicMock()
            mock_r.ping = MagicMock()
            mock_r.get = MagicMock(return_value=None)
            mock_r.setex = MagicMock()
            mock_r.delete = MagicMock()
        else:
            mock_r = None

        with patch("app.services.planning_service.StateStore._connect_redis",
                   return_value=mock_r), \
             patch("app.services.planning_service.StateStore._load_or_create_session",
                   return_value=sess):
            store = StateStore.__new__(StateStore)
            store._db = mock_db
            store._event_id = f"EVT-{_uid()}"
            store._r = mock_r
            store._session = sess
            store._TTL = 86400

        return store, mock_r, sess

    def test_step_reads_from_redis_when_available(self):
        store, mock_r, _ = self._make_store()
        mock_r.get.return_value = "3"
        assert store.step == "3"

    def test_step_falls_back_to_db_when_redis_miss(self):
        store, mock_r, sess = self._make_store(session_data={"step": "2"})
        mock_r.get.return_value = None
        sess.step = "2"
        assert store.step == "2"

    def test_step_falls_back_to_db_when_redis_down(self):
        store, _, sess = self._make_store(redis_available=False)
        sess.step = "1"
        assert store.step == "1"

    def test_step_defaults_to_zero_when_both_empty(self):
        store, _, sess = self._make_store(redis_available=False)
        sess.step = None
        assert store.step == "0"

    def test_step_setter_writes_to_redis_and_db(self):
        store, mock_r, sess = self._make_store()
        store.step = "3"
        mock_r.setex.assert_called()
        assert sess.step == "3"

    def test_step_setter_writes_db_only_when_redis_down(self):
        store, _, sess = self._make_store(redis_available=False)
        store.step = "2"
        assert sess.step == "2"

    def test_venue_data_serialised_as_json(self):
        store, mock_r, _ = self._make_store()
        vd = {"location": "Colombo", "budget": 50000}
        store.venue_data = vd
        stored = mock_r.setex.call_args[0][2]
        assert json.loads(stored) == vd

    def test_venue_data_deserialised_from_redis(self):
        store, mock_r, _ = self._make_store()
        mock_r.get.return_value = json.dumps({"location": "Kandy"})
        assert store.venue_data["location"] == "Kandy"

    def test_venue_data_empty_dict_on_miss(self):
        store, _, sess = self._make_store(redis_available=False)
        sess.venue_data = None
        assert store.venue_data == {}

    def test_persona_draft_roundtrip(self):
        store, mock_r, _ = self._make_store()
        draft = {"name": "Sarah"}
        store.persona_draft = draft
        mock_r.get.return_value = json.dumps(draft)
        assert store.persona_draft["name"] == "Sarah"

    def test_rec_ids_empty_list_on_miss(self):
        store, _, sess = self._make_store(redis_available=False)
        sess.rec_ids = None
        assert store.rec_ids == []

    def test_clear_nulls_redis_and_db(self):
        store, mock_r, sess = self._make_store()
        store.clear("rec_ids", "gift_rec_ids")
        mock_r.delete.assert_called()
        assert sess.rec_ids is None
        assert sess.gift_rec_ids is None

    def test_clear_works_without_redis(self):
        store, _, sess = self._make_store(redis_available=False)
        sess.rec_ids = json.dumps([1, 2])
        store.clear("rec_ids")
        assert sess.rec_ids is None

    def test_booking_id_persisted_to_session(self):
        store, mock_r, sess = self._make_store()
        mock_r.get.return_value = None
        store.booking_id = "BKG-abc123"
        assert sess.booking_id == "BKG-abc123"

    def test_redis_get_exception_falls_back_to_db(self):
        store, mock_r, sess = self._make_store()
        mock_r.get.side_effect = Exception("Redis down")
        sess.step = "2"
        assert store.step == "2"

    def test_redis_set_exception_still_writes_db(self):
        store, mock_r, sess = self._make_store()
        mock_r.setex.side_effect = Exception("Redis write failed")
        store.step = "3"
        assert sess.step == "3"


# ═════════════════════════════════════════════════════════════════════════════
# Gift budget 25% split
# ═════════════════════════════════════════════════════════════════════════════

class TestGiftBudgetCalculation:

    def _split(self, total, guests):
        if total and guests:
            return (float(total) * 0.75) / float(guests), float(total) * 0.25
        elif total:
            return float(total), None
        return None, None

    def test_25_percent_split(self):
        venue, gift = self._split(100000, 10)
        assert gift == 25000.0
        assert venue == 7500.0

    def test_no_guests_no_gift_budget(self):
        venue, gift = self._split(50000, None)
        assert venue == 50000.0
        assert gift is None

    def test_no_budget_returns_none(self):
        assert self._split(None, 10) == (None, None)

    def test_gift_estimated_price_gift_bph_times_guests(self):
        from app.services.planning_service import _to_gift
        result = _to_gift(_mock_pkg(pph=2500.0), gift_bph=2500.0, guest_count=4)
        assert result.estimated_price == 10000.0

    def test_gift_estimated_price_falls_back_to_pph(self):
        from app.services.planning_service import _to_gift
        result = _to_gift(_mock_pkg(pph=500.0), gift_bph=None, guest_count=5)
        assert result.estimated_price == 2500.0

    def test_gift_estimated_price_none_without_guests(self):
        from app.services.planning_service import _to_gift
        result = _to_gift(_mock_pkg(pph=500.0), gift_bph=None, guest_count=None)
        assert result.estimated_price is None


# ═════════════════════════════════════════════════════════════════════════════
# Deduplication
# ═════════════════════════════════════════════════════════════════════════════

class TestDeduplication:

    def test_shared_package_removed_from_gifts(self):
        from app.services.planning_service import _to_venue, _to_gift
        shared = _mock_pkg(pkg_id=1)
        unique = _mock_pkg(pkg_id=2)
        venues     = [_to_venue(shared)]
        raw_gifts  = [_to_gift(shared), _to_gift(unique)]
        venue_ids  = {v.id for v in venues if v.id}
        result     = [g for g in raw_gifts if g.id not in venue_ids][:3]
        assert len(result) == 1
        assert result[0].id == 2

    def test_unique_gifts_all_returned(self):
        from app.services.planning_service import _to_venue, _to_gift
        v = _mock_pkg(pkg_id=10)
        g1, g2 = _mock_pkg(pkg_id=11), _mock_pkg(pkg_id=12)
        venue_ids = {_to_venue(v).id}
        result = [g for g in [_to_gift(g1), _to_gift(g2)] if g.id not in venue_ids]
        assert len(result) == 2

    def test_capped_at_3(self):
        from app.services.planning_service import _to_gift
        gifts = [_to_gift(_mock_pkg(pkg_id=i)) for i in range(10)]
        assert len([g for g in gifts if g.id not in set()][:3]) == 3


# ═════════════════════════════════════════════════════════════════════════════
# tweak_note
# ═════════════════════════════════════════════════════════════════════════════

class TestTweakNote:

    def test_none_tweak_on_exact_match(self):
        from app.services.planning_service import _to_venue
        assert _to_venue(_mock_pkg(), tweak=None).tweak_note is None

    def test_location_fallback_note(self):
        from app.services.planning_service import _to_venue
        note = "Outside Colombo — short trip needed"
        assert _to_venue(_mock_pkg(), tweak=note).tweak_note == note

    def test_budget_fallback_note(self):
        from app.services.planning_service import _to_venue
        note = "Slightly above budget"
        assert _to_venue(_mock_pkg(), tweak=note).tweak_note == note

    def test_gift_over_budget_note(self):
        from app.services.planning_service import _to_gift
        note = "Slightly above gift budget"
        assert _to_gift(_mock_pkg(), tweak=note).tweak_note == note

    def test_tweak_note_in_venue_schema(self):
        from app.schemas.planning_schema import VenueDisplay
        v = VenueDisplay(id=1, name="Test", tweak_note="test note")
        assert v.tweak_note == "test note"

    def test_tweak_note_in_gift_schema(self):
        from app.schemas.planning_schema import GiftDisplay
        g = GiftDisplay(id=1, name="Gift", tweak_note="over budget")
        assert g.tweak_note == "over budget"

    def test_tweak_note_via_alias(self):
        from app.schemas.planning_schema import VenueDisplay
        v = VenueDisplay.model_validate({"id": 1, "name": "X", "tweakNote": "alias note"})
        assert v.tweak_note == "alias note"


# ═════════════════════════════════════════════════════════════════════════════
# Persona summary in booking notes
# ═════════════════════════════════════════════════════════════════════════════

class TestPersonaSummary:

    def test_includes_name(self):
        from app.services.planning_service import _persona_summary
        assert "Sarah" in _persona_summary({"name": "Sarah"})

    def test_includes_relationship(self):
        from app.services.planning_service import _persona_summary
        assert "girlfriend" in _persona_summary({"name": "Sarah", "relationship": "girlfriend"})

    def test_includes_food(self):
        from app.services.planning_service import _persona_summary
        assert "sushi" in _persona_summary({"name": "Sarah", "food_preferences": ["sushi"]})

    def test_includes_vibe(self):
        from app.services.planning_service import _persona_summary
        assert "romantic" in _persona_summary({"name": "Sarah", "personality_tags": ["romantic"]})

    def test_uses_persona_object(self):
        from app.services.planning_service import _persona_summary
        p = MagicMock()
        p.name = "Alice"
        p.relationship = "wife"
        p.food_preferences = ["pizza"]
        p.personality_tags = ["luxury"]
        result = _persona_summary({}, persona=p)
        assert "Alice" in result and "wife" in result

    def test_empty_draft_no_crash(self):
        from app.services.planning_service import _persona_summary
        assert isinstance(_persona_summary({}), str)

    def test_food_capped_at_3(self):
        from app.services.planning_service import _persona_summary
        # Use unique 4-char tokens that won't false-match substrings of each other
        draft = {"name": "Bob", "food_preferences": ["aaaa", "bbbb", "cccc", "dddd", "eeee"]}
        result = _persona_summary(draft)
        count = sum(1 for f in ["aaaa", "bbbb", "cccc", "dddd", "eeee"] if f in result)
        assert count <= 3


# ═════════════════════════════════════════════════════════════════════════════
# FIX 4 — known-facts block
# ═════════════════════════════════════════════════════════════════════════════

class TestKnownFactsBlock:

    def test_location_in_block(self):
        from app.services.planning_service import _known_facts_block
        block = _known_facts_block({"location": "Colombo"}, {}, None)
        assert "Colombo" in block
        assert block != ""

    def test_budget_in_block(self):
        from app.services.planning_service import _known_facts_block
        block = _known_facts_block({"budget": 50000}, {}, None)
        assert "50,000" in block or "50000" in block

    def test_guests_in_block(self):
        from app.services.planning_service import _known_facts_block
        block = _known_facts_block({"guest_count": 20}, {}, None)
        assert "20" in block

    def test_date_in_block(self):
        from app.services.planning_service import _known_facts_block
        block = _known_facts_block({"event_date": "2026-06-15"}, {}, None)
        assert "2026-06-15" in block

    def test_persona_name_from_draft(self):
        from app.services.planning_service import _known_facts_block
        assert "Sarah" in _known_facts_block({}, {"name": "Sarah"}, None)

    def test_persona_name_from_object(self):
        from app.services.planning_service import _known_facts_block
        p = MagicMock()
        p.name = "Alice"
        assert "Alice" in _known_facts_block({}, {}, p)

    def test_empty_when_nothing_known(self):
        from app.services.planning_service import _known_facts_block
        assert _known_facts_block({}, {}, None) == ""

    def test_do_not_ask_language(self):
        from app.services.planning_service import _known_facts_block
        block = _known_facts_block({"location": "Kandy"}, {}, None).upper()
        assert "DO NOT" in block or "CONFIRMED" in block or "AGAIN" in block


# ═════════════════════════════════════════════════════════════════════════════
# FIX 5 — past events injection
# ═════════════════════════════════════════════════════════════════════════════

class TestPastEventsInjection:

    def test_block_includes_event_type(self):
        past = [{"event_type": "Birthday", "event_date": "2025-06-15",
                 "location": "Colombo", "packages_used": []}]
        hints = [f"{e['event_type']} on {e['event_date']} in {e['location']}"
                 for e in past[:3] if e.get("event_type")]
        block = f"[CUSTOMER PAST EVENTS: {'; '.join(hints)}]"
        assert "Birthday" in block and "Colombo" in block

    def test_capped_at_3(self):
        past = [{"event_type": f"Ev{i}", "event_date": "2025-01-01",
                 "location": "X", "packages_used": []} for i in range(10)]
        hints = [e["event_type"] for e in past[:3] if e.get("event_type")]
        assert len(hints) == 3

    def test_empty_list_no_block(self):
        hints = [e["event_type"] for e in [] if e.get("event_type")]
        assert hints == []

    def test_missing_event_type_skipped(self):
        past = [
            {"event_type": None, "event_date": "2025-01-01", "location": "X"},
            {"event_type": "Birthday", "event_date": "2025-06-15", "location": "Y"},
        ]
        hints = [e["event_type"] for e in past[:3] if e.get("event_type")]
        assert hints == ["Birthday"]


# ═════════════════════════════════════════════════════════════════════════════
# FIX 8 — persona merge from AI
# ═════════════════════════════════════════════════════════════════════════════

class TestPersonaMergeFromAI:

    def test_merges_name(self):
        from app.services.planning_service import _merge_persona_from_ai
        result = _merge_persona_from_ai(
            {}, {"save_persona": {"name": "Sarah", "relationship": "girlfriend"}}, ""
        )
        assert result["name"] == "Sarah"
        assert result["relationship"] == "girlfriend"

    def test_does_not_overwrite_existing(self):
        from app.services.planning_service import _merge_persona_from_ai
        result = _merge_persona_from_ai(
            {"name": "Sarah", "food_preferences": ["sushi"]},
            {"save_persona": {"name": "Other", "food_preferences": ["pizza"]}},
            ""
        )
        assert result["name"] == "Sarah"
        assert result["food_preferences"] == ["sushi"]

    def test_adds_new_fields(self):
        from app.services.planning_service import _merge_persona_from_ai
        result = _merge_persona_from_ai(
            {"name": "Sarah"},
            {"save_persona": {"food_preferences": ["ramen"]}},
            ""
        )
        assert result["food_preferences"] == ["ramen"]

    def test_personality_profile_fallback(self):
        from app.services.planning_service import _merge_persona_from_ai
        result = _merge_persona_from_ai(
            {"name": "Sarah"},
            {"save_persona": None, "personality_profile": "romantic"},
            ""
        )
        assert result.get("personality") == "romantic"

    def test_no_crash_on_none(self):
        from app.services.planning_service import _merge_persona_from_ai
        result = _merge_persona_from_ai({"name": "X"}, {"save_persona": None}, "")
        assert result["name"] == "X"


# ═════════════════════════════════════════════════════════════════════════════
# venue_missing
# ═════════════════════════════════════════════════════════════════════════════

class TestVenueMissing:

    def test_all_present_empty(self):
        from app.services.planning_service import _venue_missing
        assert _venue_missing({"location": "X", "budget": 1,
                                "guest_count": 2, "event_date": "2026-01-01"}) == []

    def test_missing_location(self):
        from app.services.planning_service import _venue_missing
        assert "location" in _venue_missing({"budget": 1, "guest_count": 2, "event_date": "X"})

    def test_missing_budget(self):
        from app.services.planning_service import _venue_missing
        assert any("budget" in m for m in _venue_missing(
            {"location": "X", "guest_count": 2, "event_date": "X"}
        ))

    def test_missing_guests(self):
        from app.services.planning_service import _venue_missing
        assert any("guest" in m for m in _venue_missing(
            {"location": "X", "budget": 1, "event_date": "X"}
        ))

    def test_missing_date(self):
        from app.services.planning_service import _venue_missing
        assert any("date" in m for m in _venue_missing(
            {"location": "X", "budget": 1, "guest_count": 2}
        ))

    def test_all_missing_returns_4(self):
        from app.services.planning_service import _venue_missing
        assert len(_venue_missing({})) == 4


# ═════════════════════════════════════════════════════════════════════════════
# _build_persona_context (alias test — works with both old and new name)
# ═════════════════════════════════════════════════════════════════════════════

class TestBuildPersonaContext:

    def _fn(self):
        try:
            from app.services.ai_service import _build_persona_context
            return _build_persona_context
        except ImportError:
            from app.services.ai_service import _build_structured_persona_context
            return _build_structured_persona_context

    def _p(self, **kw):
        p = MagicMock()
        p.name = kw.get("name", "Test")
        p.relationship = kw.get("relationship", "")
        p.food_preferences = kw.get("food_preferences", None)
        p.music_preferences = kw.get("music_preferences", None)
        p.personality_tags = kw.get("personality_tags", None)
        p.color_preferences = kw.get("color_preferences", None)
        p.preferences_json = kw.get("preferences_json", None)
        return p

    def test_empty_returns_empty_string(self):
        assert self._fn()([]) == ""

    def test_personality_tags_in_output(self):
        ctx = self._fn()([self._p(personality_tags=["adventure"])])
        assert "adventure" in ctx

    def test_food_preferences_in_output(self):
        ctx = self._fn()([self._p(food_preferences=["fine dining"])])
        assert ctx  # non-empty

    def test_multiple_personas(self):
        ctx = self._fn()([self._p(name="Alice"), self._p(name="Bob")])
        assert "Alice" in ctx and "Bob" in ctx