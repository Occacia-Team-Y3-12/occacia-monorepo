from unittest.mock import AsyncMock, MagicMock, patch


AI_CHAT = {
    "intent": "chat",
    "chat_response": "Hello!",
    "venue_tags": [],
    "missing_info": [],
}


def make_base_patches():
    return [
        patch(
            "app.routers.v1.planning_router.ai_service.generate_date_plan",
            new_callable=AsyncMock,
            return_value=AI_CHAT,
        ),
        patch("app.routers.v1.planning_router.chat_service.get_session_history", return_value=[]),
        patch("app.routers.v1.planning_router.chat_service.save_message", return_value=None),
        patch("app.routers.v1.planning_router.persona_service.get_personas", return_value=[]),
    ]


def test_rate_limit_endpoint_returns_429(auth_client):
    mock_redis = MagicMock()
    mock_redis.pipeline.return_value.execute.return_value = [999, True]
    patches = make_base_patches()

    with patches[0], patches[1], patches[2], patches[3]:
        with patch("app.routers.v1.planning_router.get_redis", return_value=mock_redis):
            response = auth_client.post(
                "/api/v1/planning/generate",
                json={"user_query": "Hi", "session_id": "s1"},
            )

    assert response.status_code == 429
