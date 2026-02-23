from unittest.mock import AsyncMock, patch


def test_generate_plan_success_planning_intent_calls_db(client):
    with (
        patch(
            "app.routers.v1.planning_router.ai_service.generate_date_plan",
            new_callable=AsyncMock,
        ) as mock_generate_date_plan,
        patch(
            "app.routers.v1.planning_router.vendor_service.find_perfect_matches",
        ) as mock_find_perfect_matches,
        patch(
            "app.routers.v1.planning_router.chat_service.get_session_history",
        ) as mock_get_session_history,
        patch(
            "app.routers.v1.planning_router.chat_service.save_message",
        ) as mock_save_message,
    ):
        mock_get_session_history.return_value = []
        mock_save_message.return_value = None

        mock_generate_date_plan.return_value = {
            "intent": "planning",
            "reasoning": "User wants a date.",
            "location": "Kandy",
            "venue_tags": ["romantic"],
            "budget_per_head": 5000,
            "guest_count": 2,
        }

        mock_find_perfect_matches.return_value = [
            {
                "name": "Hotel A",
                "description": "Nice view",
                "price_per_head": 5000.0,
                "tags": ["romantic"],
            },
            {
                "name": "Hotel B",
                "description": "Good food",
                "price_per_head": 4000.0,
                "tags": ["quiet"],
            },
        ]

        payload = {"user_query": "I want a romantic dinner in Kandy", "session_id": "s1"}
        response = client.post("/api/v1/planning/generate", json=payload)

        assert response.status_code == 200
        data = response.json()

        assert data["intent"] == "planning"
        assert len(data["matched_venues"]) == 2
        assert data["matched_venues"][0]["name"] == "Hotel A"
        mock_find_perfect_matches.assert_called_once()


def test_generate_plan_chat_intent_does_not_call_db(client):
    with (
        patch(
            "app.routers.v1.planning_router.ai_service.generate_date_plan",
            new_callable=AsyncMock,
        ) as mock_generate_date_plan,
        patch(
            "app.routers.v1.planning_router.vendor_service.find_perfect_matches",
        ) as mock_find_perfect_matches,
        patch(
            "app.routers.v1.planning_router.chat_service.get_session_history",
        ) as mock_get_session_history,
        patch(
            "app.routers.v1.planning_router.chat_service.save_message",
        ) as mock_save_message,
    ):
        mock_get_session_history.return_value = []
        mock_save_message.return_value = None

        mock_generate_date_plan.return_value = {
            "intent": "chat",
            "chat_response": "Hello! How can I help?",
            "venue_tags": [],
        }

        payload = {"user_query": "Hi", "session_id": "s1"}
        response = client.post("/api/v1/planning/generate", json=payload)

        assert response.status_code == 200
        data = response.json()

        assert data["intent"] == "chat"
        assert data["matched_venues"] == []
        mock_find_perfect_matches.assert_not_called()
