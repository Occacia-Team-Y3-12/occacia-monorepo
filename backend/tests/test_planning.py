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
    return {
        "ai": patch(
            "app.routers.v1.planning_router.ai_service.generate_date_plan",
            new_callable=AsyncMock,
            return_value=ai_return,
        ),
        "vendor": patch(
            "app.routers.v1.planning_router.vendor_service.find_perfect_matches",
            return_value=vendor_return or [],
        ),
        "gift": patch(
            "app.routers.v1.planning_router.vendor_service.find_gift_matches",
            return_value=vendor_return or [],
        ),
        "history": patch(
            "app.routers.v1.planning_router.chat_service.get_session_history",
            return_value=history or [],
        ),
        "save": patch(
            "app.routers.v1.planning_router.chat_service.save_message",
            return_value=None,
        ),
        "personas": patch(
            "app.routers.v1.planning_router.persona_service.get_personas",
            return_value=[],
        ),
    }


# ── Auth ─────────────────────────────────────────────────────────────

def test_planning_requires_auth(client):
    r = client.post("/api/v1/planning/generate", json={
        "user_query": "Hello", "session_id": "s1"
    })
    assert r.status_code == 401


# ── Session ID Validation ────────────────────────────────────────────

def test_invalid_session_id_rejected(auth_client):
    patches = make_patches(AI_CHAT_RESPONSE)
    with patches["ai"], patches["history"], patches["save"], patches["personas"]:
        r = auth_client.post("/api/v1/planning/generate", json={
            "user_query": "Hi",
            "session_id": "bad session id with spaces!"
        })
        assert r.status_code == 400
        assert "session_id" in r.json()["detail"].lower()


def test_valid_session_id_accepted(auth_client):
    patches = make_patches(AI_CHAT_RESPONSE)
    with patches["ai"], patches["history"], patches["save"], patches["personas"]:
        r = auth_client.post("/api/v1/planning/generate", json={
            "user_query": "Hi",
            "session_id": "valid-session-123"
        })
        assert r.status_code == 200


# ── Intent: chat ─────────────────────────────────────────────────────

def test_chat_intent_returns_response(auth_client):
    patches = make_patches(AI_CHAT_RESPONSE)
    with patches["ai"], patches["vendor"], patches["history"], patches["save"], patches["personas"]:
        r = auth_client.post("/api/v1/planning/generate", json={
            "user_query": "Hi", "session_id": "s1"
        })
        assert r.status_code == 200
        data = r.json()
        assert data["intent"] == "chat"
        assert data["matched_venues"] == []


def test_chat_intent_does_not_search_db(auth_client):
    patches = make_patches(AI_CHAT_RESPONSE)
    with patches["ai"], patches["vendor"] as mock_vendor, patches["history"], patches["save"], patches["personas"]:
        auth_client.post("/api/v1/planning/generate", json={
            "user_query": "Hi", "session_id": "s1"
        })
        mock_vendor.assert_not_called()


# ── Intent: planning ─────────────────────────────────────────────────

def test_planning_intent_searches_db(auth_client):
    pkg = mock_package("Romantic Dinner", ["romantic", "luxury"], 150.0)
    patches = make_patches(AI_PLANNING_RESPONSE, vendor_return=[pkg])
    with patches["ai"], patches["vendor"] as mock_vendor, patches["history"], patches["save"], patches["personas"]:
        r = auth_client.post("/api/v1/planning/generate", json={
            "user_query": "I want a romantic dinner", "session_id": "s1"
        })
        assert r.status_code == 200
        mock_vendor.assert_called_once()


def test_planning_intent_returns_venues(auth_client):
    pkg = mock_package("Romantic Dinner", ["romantic", "luxury"], 150.0)
    patches = make_patches(AI_PLANNING_RESPONSE, vendor_return=[pkg])
    with patches["ai"], patches["vendor"], patches["history"], patches["save"], patches["personas"]:
        r = auth_client.post("/api/v1/planning/generate", json={
            "user_query": "I want a romantic dinner", "session_id": "s1"
        })
        data = r.json()
        assert len(data["matched_venues"]) == 1
        assert data["matched_venues"][0]["name"] == "Romantic Dinner"
        assert data["matched_venues"][0]["vendor_name"] == "Test Vendor"


def test_planning_intent_no_tags_skips_db(auth_client):
    ai_response = {**AI_PLANNING_RESPONSE, "venue_tags": [], "intent": "planning"}
    patches = make_patches(ai_response)
    with patches["ai"], patches["vendor"] as mock_vendor, patches["history"], patches["save"], patches["personas"]:
        r = auth_client.post("/api/v1/planning/generate", json={
            "user_query": "I want something nice", "session_id": "s1"
        })
        assert r.status_code == 200
        mock_vendor.assert_not_called()


def test_planning_response_fields(auth_client):
    pkg = mock_package()
    patches = make_patches(AI_PLANNING_RESPONSE, vendor_return=[pkg])
    with patches["ai"], patches["vendor"], patches["history"], patches["save"], patches["personas"]:
        r = auth_client.post("/api/v1/planning/generate", json={
            "user_query": "Romantic dinner", "session_id": "s1"
        })
        data = r.json()
        assert data["intent"] == "planning"
        assert data["event_type"] == "dinner"
        assert data["location"] == "Colombo"
        assert data["budget_per_head"] == 150.0
        assert data["guest_count"] == 2
        assert data["venue_tags"] == ["romantic", "luxury"]


# ── Intent: gift ─────────────────────────────────────────────────────

def test_gift_intent_searches_gift_matches(auth_client):
    pkg = mock_package("Adventure Pack", ["hiking", "adventure"], 80.0)
    patches = make_patches(AI_GIFT_RESPONSE, vendor_return=[pkg])
    with patches["ai"], patches["gift"] as mock_gift, patches["history"], patches["save"], patches["personas"]:
        r = auth_client.post("/api/v1/planning/generate", json={
            "user_query": "I need a gift for my girlfriend", "session_id": "s1"
        })
        assert r.status_code == 200
        mock_gift.assert_called_once()


def test_gift_intent_returns_matched_packages(auth_client):
    pkg = mock_package("Adventure Pack", ["hiking", "adventure"], 80.0)
    patches = make_patches(AI_GIFT_RESPONSE, vendor_return=[pkg])
    with patches["ai"], patches["gift"], patches["history"], patches["save"], patches["personas"]:
        r = auth_client.post("/api/v1/planning/generate", json={
            "user_query": "I need a gift", "session_id": "s1"
        })
        data = r.json()
        assert len(data["matched_venues"]) == 1
        assert data["matched_venues"][0]["name"] == "Adventure Pack"


# ── AI Error Handling ─────────────────────────────────────────────────

def test_ai_error_returns_fallback(auth_client):
    with (
        patch("app.routers.v1.planning_router.ai_service.generate_date_plan",
              new_callable=AsyncMock, side_effect=Exception("Langflow down")),
        patch("app.routers.v1.planning_router.chat_service.get_session_history", return_value=[]),
        patch("app.routers.v1.planning_router.chat_service.save_message", return_value=None),
        patch("app.routers.v1.planning_router.persona_service.get_personas", return_value=[]),
    ):
        r = auth_client.post("/api/v1/planning/generate", json={
            "user_query": "Hi", "session_id": "s1"
        })
        assert r.status_code == 200
        assert r.json()["intent"] == "chat"
        assert "foggy" in r.json()["chat_response"].lower()


# ── Memory Persistence ────────────────────────────────────────────────

def test_chat_history_saved(auth_client):
    patches = make_patches(AI_CHAT_RESPONSE)
    with patches["ai"], patches["history"], patches["personas"], \
         patch("app.routers.v1.planning_router.chat_service.save_message") as mock_save:
        mock_save.return_value = None
        auth_client.post("/api/v1/planning/generate", json={
            "user_query": "Hi", "session_id": "s1"
        })
        mock_save.assert_called_once()


def test_chat_history_loaded_per_session(auth_client):
    patches = make_patches(AI_CHAT_RESPONSE)
    with patches["ai"], patches["personas"], patches["save"], \
         patch("app.routers.v1.planning_router.chat_service.get_session_history") as mock_history:
        mock_history.return_value = []
        auth_client.post("/api/v1/planning/generate", json={
            "user_query": "Hi", "session_id": "my-session"
        })
        mock_history.assert_called_once()
        call_kwargs = mock_history.call_args
        assert "my-session" in str(call_kwargs)