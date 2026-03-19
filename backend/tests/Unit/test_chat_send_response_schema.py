"""
tests/Unit/test_chat_send_response_schema.py

Unit tests for the extended ChatSendResponse schema.
Verifies backward compatibility (spec fields always present) and that
all extended planning fields are optional with safe defaults.
"""
import pytest
from app.schemas.event_planning_schema import ChatSendResponse, VenueDisplay


class TestChatSendResponseBackwardCompat:

    def test_minimal_construction_with_only_reply(self):
        """Spec clients that only set reply should still work."""
        r = ChatSendResponse(reply="Hello!")
        assert r.reply == "Hello!"
        assert r.suggested_tasks == []

    def test_minimal_construction_with_reply_and_tasks(self):
        r = ChatSendResponse(reply="Hi", suggested_tasks=[{"name": "Buy cake"}])
        assert r.reply == "Hi"
        assert len(r.suggested_tasks) == 1

    def test_reply_is_required(self):
        with pytest.raises(Exception):
            ChatSendResponse()

    def test_suggested_tasks_defaults_to_empty_list(self):
        r = ChatSendResponse(reply="x")
        assert r.suggested_tasks == []

    def test_serialises_with_camel_case_alias(self):
        r = ChatSendResponse(reply="x", suggested_tasks=[])
        data = r.model_dump(by_alias=True)
        assert "suggestedTasks" in data
        assert "suggested_tasks" not in data

    def test_serialises_with_snake_case_when_not_aliased(self):
        r = ChatSendResponse(reply="x")
        data = r.model_dump(by_alias=False)
        assert "suggested_tasks" in data


class TestChatSendResponseExtendedDefaults:

    def test_intent_defaults_to_none(self):
        assert ChatSendResponse(reply="x").intent is None

    def test_reasoning_defaults_to_none(self):
        assert ChatSendResponse(reply="x").reasoning is None

    def test_personality_profile_defaults_to_none(self):
        assert ChatSendResponse(reply="x").personality_profile is None

    def test_gift_suggestion_defaults_to_none(self):
        assert ChatSendResponse(reply="x").gift_suggestion is None

    def test_event_type_defaults_to_none(self):
        assert ChatSendResponse(reply="x").event_type is None

    def test_event_date_defaults_to_none(self):
        assert ChatSendResponse(reply="x").event_date is None

    def test_location_defaults_to_none(self):
        assert ChatSendResponse(reply="x").location is None

    def test_budget_per_head_defaults_to_none(self):
        assert ChatSendResponse(reply="x").budget_per_head is None

    def test_guest_count_defaults_to_none(self):
        assert ChatSendResponse(reply="x").guest_count is None

    def test_venue_tags_defaults_to_empty_list(self):
        assert ChatSendResponse(reply="x").venue_tags == []

    def test_missing_info_defaults_to_empty_list(self):
        assert ChatSendResponse(reply="x").missing_info == []

    def test_matched_venues_defaults_to_empty_list(self):
        assert ChatSendResponse(reply="x").matched_venues == []

    def test_venue_match_tier_defaults_to_none(self):
        assert ChatSendResponse(reply="x").venue_match_tier is None

    def test_ask_save_persona_defaults_to_false(self):
        assert ChatSendResponse(reply="x").ask_save_persona is False

    def test_persona_saved_defaults_to_false(self):
        assert ChatSendResponse(reply="x").persona_saved is False

    def test_persona_confirmed_defaults_to_false(self):
        assert ChatSendResponse(reply="x").persona_confirmed is False


class TestChatSendResponseExtendedPopulation:

    def test_full_construction_with_all_fields(self):
        r = ChatSendResponse(
            reply="Great!",
            suggested_tasks=[{"name": "Book venue"}],
            intent="planning",
            reasoning="User wants a dinner.",
            personalityProfile="romantic",
            giftSuggestion="Flowers",
            eventType="dinner",
            eventDate="2026-12-25",
            location="Colombo",
            budgetPerHead=500.0,
            guestCount=4,
            venueTags=["romantic", "luxury"],
            missingInfo=["date"],
            matchedVenues=[],
            venueMatchTier=1,
            askSavePersona=True,
            personaSaved=False,
            personaConfirmed=True,
        )
        assert r.reply == "Great!"
        assert r.intent == "planning"
        assert r.venue_tags == ["romantic", "luxury"]
        assert r.ask_save_persona is True
        assert r.persona_confirmed is True
        assert r.venue_match_tier == 1

    def test_accepts_snake_case_field_names(self):
        """populate_by_name=True means snake_case works too."""
        r = ChatSendResponse(
            reply="x",
            venue_tags=["cozy"],
            ask_save_persona=True,
            persona_saved=True,
        )
        assert r.venue_tags == ["cozy"]
        assert r.ask_save_persona is True

    def test_camel_case_aliases_serialise_correctly(self):
        r = ChatSendResponse(
            reply="x",
            venue_tags=["a"],
            missing_info=["b"],
            ask_save_persona=True,
            persona_saved=True,
            persona_confirmed=True,
            venue_match_tier=2,
            budget_per_head=100.0,
            guest_count=2,
            event_type="dinner",
            event_date="2026-01-01",
            personality_profile="fun",
            gift_suggestion="Gift",
        )
        data = r.model_dump(by_alias=True)
        assert data["venueTags"] == ["a"]
        assert data["missingInfo"] == ["b"]
        assert data["askSavePersona"] is True
        assert data["personaSaved"] is True
        assert data["personaConfirmed"] is True
        assert data["venueMatchTier"] == 2
        assert data["budgetPerHead"] == 100.0
        assert data["guestCount"] == 2
        assert data["eventType"] == "dinner"
        assert data["eventDate"] == "2026-01-01"
        assert data["personalityProfile"] == "fun"
        assert data["giftSuggestion"] == "Gift"


class TestVenueDisplay:

    def test_minimal_construction(self):
        v = VenueDisplay(name="Venue One")
        assert v.name == "Venue One"
        assert v.tags == []
        assert v.is_verified is False

    def test_full_construction(self):
        v = VenueDisplay(
            id=1,
            name="Grand Venue",
            description="A great place",
            price_per_head=200.0,
            tags=["romantic", "luxury"],
            match_score=3,
            match_score_max=5,
            match_score_label="3 of 5 tags matched",
            vendor_name="Top Vendor",
            is_verified=True,
        )
        assert v.id == 1
        assert v.tags == ["romantic", "luxury"]
        assert v.match_score == 3
        assert v.vendor_name == "Top Vendor"
        assert v.is_verified is True

    def test_serialises_with_camel_case(self):
        v = VenueDisplay(
            name="x",
            price_per_head=100.0,
            match_score=2,
            match_score_max=4,
            match_score_label="2 of 4",
            vendor_name="V",
            is_verified=True,
        )
        data = v.model_dump(by_alias=True)
        assert "pricePerHead" in data
        assert "matchScore" in data
        assert "matchScoreMax" in data
        assert "matchScoreLabel" in data
        assert "vendorName" in data
        assert "isVerified" in data

    def test_matched_venues_in_response_contain_venue_display(self):
        venue = VenueDisplay(name="Test Venue", tags=["romantic"])
        r = ChatSendResponse(reply="Found it!", matched_venues=[venue])
        assert len(r.matched_venues) == 1
        assert r.matched_venues[0].name == "Test Venue"
