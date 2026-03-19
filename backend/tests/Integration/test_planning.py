from unittest.mock import AsyncMock, MagicMock, patch
import pytest


# ── Helpers ──────────────────────────────────────────────────────────

def mock_package(name="Test Venue", tags=None, price=100.0):
    pkg = MagicMock()
    pkg.id = 1
    pkg.name = name
    pkg.description = "A great venue"
    pkg.price_per_head = price
    pkg.tags = tags or ["romantic"]
    pkg.location_coverage = "Colombo"
    vendor = MagicMock()
    vendor.display_name = "Test Vendor"
    vendor.business_name = "Test Vendor"
    vendor.contact_phone = "+94771234567"
    vendor.phone = "+94771234567"
    vendor.location_base = "Colombo"
    vendor.email = "vendor@test.com"
    vendor.is_verified = True
    pkg.vendor = vendor
    return pkg


AI_PLANNING_RESPONSE = {
    "intent": "planning",
    "reasoning": "User wants romantic dinner",
    "chat_response": "I found some great venues!",
    "venue_tags": ["romantic", "luxury"],
    "budget_per_head": 150.0,
    "guest_count": 2,
    "location": "Colombo",
    "event_type": "dinner",
    "personality_profile": "romantic, thoughtful",
    "gift_suggestion": None,
    "missing_info": [],
}

AI_CHAT_RESPONSE = {
    "intent": "chat",
    "chat_response": "Hello! How can I help you plan something special?",
    "venue_tags": [],
    "missing_info": [],
}

AI_GIFT_RESPONSE = {
    "intent": "gift",
    "chat_response": "I found some great gift options!",
    "venue_tags": ["hiking", "adventure"],
    "budget_per_head": 100.0,
    "guest_count": 1,
    "gift_suggestion": "An outdoor adventure experience",
    "missing_info": [],
}


def make_patches(ai_return, vendor_return=None, history=None):
    # Patches now target customer_router where planning_service is wired in.
    # planning_router has been retired — POST /planning/generate no longer exists.
    return {
        "ai": patch(
            "app.routers.v1.customer_router.ai_service.generate_date_plan",
            new_callable=AsyncMock,
            return_value=ai_return,
        ),
        "vendor": patch(
            "app.routers.v1.customer_router._vendor_service.find_perfect_matches",
            return_value=vendor_return or [],
        ),
        "gift": patch(
            "app.routers.v1.customer_router._vendor_service.find_gift_matches",
            return_value=vendor_return or [],
        ),
        "history": patch(
            "app.routers.v1.customer_router.chat_service.get_session_history",
            return_value=history or [],
        ),
        "save": patch(
            "app.routers.v1.customer_router.chat_service.save_message",
            return_value=None,
        ),
        "personas": patch(
            "app.routers.v1.customer_router._persona_service.get_personas",
            return_value=[],
        ),
    }


# ── Auth ─────────────────────────────────────────────────────────────

def _create_event(auth_client) -> str:
    r = auth_client.post(
        "/api/v1/customers/events",
        json={"eventType": "Birthday", "title": "Test Event"},
    )
    assert r.status_code == 201, r.text
    return r.json()["eventId"]


def test_planning_requires_auth(client):
    # POST /planning/generate is retired. The equivalent is the event chat endpoint.
    # Unauthenticated requests to any customer endpoint must return 401.
    r = client.post("/api/v1/customers/events/EVT-fake/chat", json={"content": "Hello"})
    assert r.status_code == 401


# ── Helpers ──────────────────────────────────────────────────────────

def _create_event(auth_client) -> str:
    """Create a draft event and return its eventId."""
    r = auth_client.post(
        "/api/v1/customers/events",
        json={"eventType": "Birthday", "title": "Test Planning Event"},
    )
    assert r.status_code == 201, r.text
    return r.json()["eventId"]


def _chat(auth_client, event_id: str, content: str):
    return auth_client.post(
        f"/api/v1/customers/events/{event_id}/chat",
        json={"content": content},
    )


# ── Auth ─────────────────────────────────────────────────────────────

def test_planning_requires_auth(client):
    r = client.post("/api/v1/customers/events/EVT-fake/chat", json={"content": "Hello"})
    assert r.status_code == 401


# ── Intent: chat ─────────────────────────────────────────────────────

def test_chat_intent_returns_response(auth_client):
    event_id = _create_event(auth_client)
    patches = make_patches(AI_CHAT_RESPONSE)
    with patches["ai"], patches["vendor"], patches["history"], patches["save"], patches["personas"]:
        r = _chat(auth_client, event_id, "Hi")
        assert r.status_code == 200
        data = r.json()
        assert data["intent"] == "chat"
        assert data["matchedVenues"] == []


def test_chat_intent_does_not_search_db(auth_client):
    event_id = _create_event(auth_client)
    patches = make_patches(AI_CHAT_RESPONSE)
    with patches["ai"], patches["vendor"] as mock_vendor, patches["history"], patches["save"], patches["personas"]:
        _chat(auth_client, event_id, "Hi")
        mock_vendor.assert_not_called()


# ── Intent: planning ─────────────────────────────────────────────────

def test_planning_intent_searches_db(auth_client):
    event_id = _create_event(auth_client)
    pkg = mock_package("Romantic Dinner", ["romantic", "luxury"], 150.0)
    patches = make_patches(AI_PLANNING_RESPONSE, vendor_return=[pkg])
    with patches["ai"], patches["vendor"] as mock_vendor, patches["history"], patches["save"], patches["personas"]:
        r = _chat(auth_client, event_id, "I want a romantic dinner")
        assert r.status_code == 200
        mock_vendor.assert_called_once()


def test_planning_intent_returns_venues(auth_client):
    event_id = _create_event(auth_client)
    pkg = mock_package("Romantic Dinner", ["romantic", "luxury"], 150.0)
    patches = make_patches(AI_PLANNING_RESPONSE, vendor_return=[pkg])
    with patches["ai"], patches["vendor"], patches["history"], patches["save"], patches["personas"]:
        r = _chat(auth_client, event_id, "I want a romantic dinner")
        data = r.json()
        assert len(data["matchedVenues"]) == 1
        assert data["matchedVenues"][0]["name"] == "Romantic Dinner"
        assert data["matchedVenues"][0]["vendorName"] == "Test Vendor"


def test_planning_intent_no_tags_skips_db(auth_client):
    event_id = _create_event(auth_client)
    ai_response = {**AI_PLANNING_RESPONSE, "venue_tags": [], "intent": "planning"}
    patches = make_patches(ai_response)
    with patches["ai"], patches["vendor"] as mock_vendor, patches["history"], patches["save"], patches["personas"]:
        r = _chat(auth_client, event_id, "I want something nice")
        assert r.status_code == 200
        mock_vendor.assert_not_called()


def test_planning_response_fields(auth_client):
    event_id = _create_event(auth_client)
    pkg = mock_package()
    patches = make_patches(AI_PLANNING_RESPONSE, vendor_return=[pkg])
    with patches["ai"], patches["vendor"], patches["history"], patches["save"], patches["personas"]:
        r = _chat(auth_client, event_id, "Romantic dinner")
        data = r.json()
        assert data["intent"] == "planning"
        assert data["eventType"] == "dinner"
        assert data["location"] == "Colombo"
        assert data["budgetPerHead"] == 150.0
        assert data["guestCount"] == 2
        assert data["venueTags"] == ["romantic", "luxury"]


# ── Intent: gift ─────────────────────────────────────────────────────

def test_gift_intent_searches_gift_matches(auth_client):
    event_id = _create_event(auth_client)
    pkg = mock_package("Adventure Pack", ["hiking", "adventure"], 80.0)
    patches = make_patches(AI_GIFT_RESPONSE, vendor_return=[pkg])
    with patches["ai"], patches["gift"] as mock_gift, patches["history"], patches["save"], patches["personas"]:
        r = _chat(auth_client, event_id, "I need a gift for my girlfriend")
        assert r.status_code == 200
        mock_gift.assert_called_once()


def test_gift_intent_returns_matched_packages(auth_client):
    event_id = _create_event(auth_client)
    pkg = mock_package("Adventure Pack", ["hiking", "adventure"], 80.0)
    patches = make_patches(AI_GIFT_RESPONSE, vendor_return=[pkg])
    with patches["ai"], patches["gift"], patches["history"], patches["save"], patches["personas"]:
        r = _chat(auth_client, event_id, "I need a gift")
        data = r.json()
        assert len(data["matchedVenues"]) == 1
        assert data["matchedVenues"][0]["name"] == "Adventure Pack"


# ── AI Error Handling ─────────────────────────────────────────────────

def test_ai_error_returns_fallback(auth_client):
    """When planning_service fails, endpoint falls back to rule-based reply and returns 200."""
    event_id = _create_event(auth_client)
    with (
        patch("app.routers.v1.customer_router.planning_service.process_plan",
              new_callable=AsyncMock, side_effect=Exception("AI down")),
    ):
        r = _chat(auth_client, event_id, "Hi")
        assert r.status_code == 200
        body = r.json()
        assert "reply" in body
        assert body["reply"]  # fallback rule-based reply from event_planning_service


# ── Memory Persistence ────────────────────────────────────────────────

def test_chat_history_saved(auth_client):
    """Messages are persisted to EventChatMessage via event_planning_service."""
    event_id = _create_event(auth_client)
    patches = make_patches(AI_CHAT_RESPONSE)
    with patches["ai"], patches["history"], patches["personas"], patches["save"] as mock_save:
        _chat(auth_client, event_id, "Hi")
        mock_save.assert_called_once()


def test_chat_history_loaded_per_session(auth_client):
    """Session history is loaded using event_id as the session key."""
    event_id = _create_event(auth_client)
    patches = make_patches(AI_CHAT_RESPONSE)
    with patches["ai"], patches["personas"], patches["save"], patches["history"] as mock_history:
        mock_history.return_value = []
        _chat(auth_client, event_id, "Hi")
        mock_history.assert_called_once()
        call_kwargs = mock_history.call_args
        assert event_id in str(call_kwargs)