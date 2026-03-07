# from unittest.mock import AsyncMock, patch, MagicMock
# import pytest
# from app.routers.v1.planning_router import check_rate_limit
# from fastapi import HTTPException


# AI_CHAT = {
#     "intent": "chat",
#     "chat_response": "Hello!",
#     "venue_tags": [],
#     "missing_info": [],
# }


# def make_base_patches():
#     return [
#         patch("app.routers.v1.planning_router.ai_service.generate_date_plan",
#               new_callable=AsyncMock, return_value=AI_CHAT),
#         patch("app.routers.v1.planning_router.chat_service.get_session_history", return_value=[]),
#         patch("app.routers.v1.planning_router.chat_service.save_message", return_value=None),
#         patch("app.routers.v1.planning_router.persona_service.get_personas", return_value=[]),
#     ]


# # ── Redis rate limiting ───────────────────────────────────────────────

# def test_rate_limit_allows_under_limit():
#     mock_redis = MagicMock()
#     mock_redis.pipeline.return_value.execute.return_value = [5, True]  # 5 requests
#     with patch("app.routers.v1.planning_router.get_redis", return_value=mock_redis):
#         # Should not raise
#         check_rate_limit(customer_id=1)


# def test_rate_limit_blocks_over_limit():
#     mock_redis = MagicMock()
#     mock_redis.pipeline.return_value.execute.return_value = [11, True]  # 11 > 10
#     with patch("app.routers.v1.planning_router.get_redis", return_value=mock_redis):
#         with pytest.raises(HTTPException) as exc:
#             check_rate_limit(customer_id=1)
#         assert exc.value.status_code == 429


# def test_rate_limit_fails_open_when_redis_unavailable():
#     with patch("app.routers.v1.planning_router.get_redis", return_value=None):
#         # Should NOT raise — fail open
#         check_rate_limit(customer_id=1)


# def test_rate_limit_endpoint_returns_429(auth_client):
#     mock_redis = MagicMock()
#     mock_redis.pipeline.return_value.execute.return_value = [999, True]
#     patches = make_base_patches()
#     with patches[0], patches[1], patches[2], patches[3]:
#         with patch("app.routers.v1.planning_router.get_redis", return_value=mock_redis):
#             r = auth_client.post("/api/v1/planning/generate", json={
#                 "user_query": "Hi", "session_id": "s1"
#             })
#             assert r.status_code == 429


# # ── Session isolation ─────────────────────────────────────────────────

# def test_different_customers_have_separate_rate_limits():
#     call_count = 0
#     captured_keys = []

#     def fake_pipeline():
#         mock_pipe = MagicMock()
#         def execute():
#             return [1, True]
#         mock_pipe.execute = execute
#         mock_pipe.incr = lambda key: captured_keys.append(key)
#         mock_pipe.expire = MagicMock()
#         return mock_pipe

#     mock_redis = MagicMock()
#     mock_redis.pipeline = fake_pipeline

#     with patch("app.routers.v1.planning_router.get_redis", return_value=mock_redis):
#         check_rate_limit(customer_id=1)
#         check_rate_limit(customer_id=2)

#     assert len(set(captured_keys)) == 2  # Different keys