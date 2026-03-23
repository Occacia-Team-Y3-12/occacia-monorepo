from __future__ import annotations

from app.schemas import event_planning_schema, planning_schema
from app.schemas.event_planning_schema import ChatSendResponse, VenueDisplay


def test_minimal_construction_requires_only_reply():
    response = ChatSendResponse(reply="Hello!")
    assert response.reply == "Hello!"


def test_suggested_tasks_defaults_empty():
    assert ChatSendResponse(reply="x").suggested_tasks == []


def test_gift_fields_do_not_exist():
    fields = ChatSendResponse.model_fields
    assert "gift_suggestion" not in fields
    assert "gift_category" not in fields
    assert "matched_gifts" not in fields
    assert "is_ai_fallback" not in fields


def test_camelcase_aliases_work():
    response = ChatSendResponse(
        reply="x",
        suggestedTasks=[],
        missingInfo=["date"],
        askSavePersona=True,
    )
    assert response.missing_info == ["date"]
    assert response.ask_save_persona is True


def test_snake_case_also_works():
    response = ChatSendResponse(
        reply="x",
        missing_info=["date"],
        ask_save_persona=True,
    )
    assert response.missing_info == ["date"]
    assert response.ask_save_persona is True


def test_serialize_by_alias():
    data = ChatSendResponse(reply="x").model_dump(by_alias=True)
    assert "suggestedTasks" in data
    assert "missingInfo" in data
    assert "askSavePersona" in data


def test_no_gift_suggestion_in_serialized_output():
    data = ChatSendResponse(reply="x").model_dump(by_alias=True)
    assert "giftSuggestion" not in data
    assert "matchedGifts" not in data
    assert "isAiFallback" not in data


def test_matched_venues_defaults_empty():
    assert ChatSendResponse(reply="x").matched_venues == []


def test_persona_flags_default_false():
    response = ChatSendResponse(reply="x")
    assert response.ask_save_persona is False
    assert response.persona_saved is False
    assert response.persona_confirmed is False


def test_booking_fields_default():
    response = ChatSendResponse(reply="x")
    assert response.booking_created is False
    assert response.booking_id is None
    assert response.redirect_url is None


def test_venue_display_construction():
    venue = VenueDisplay(name="Test")
    assert venue.name == "Test"
    assert venue.tags == []
    assert venue.is_verified is False


def test_giftdisplay_does_not_exist_in_event_planning_schema():
    assert not hasattr(event_planning_schema, "GiftDisplay")


def test_giftdisplay_does_not_exist_in_planning_schema():
    assert not hasattr(planning_schema, "GiftDisplay")
