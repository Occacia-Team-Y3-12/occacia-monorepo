# import pytest
# from unittest.mock import MagicMock, patch
# from fastapi.testclient import TestClient
# from app.main import app
# from app.schemas.plan_schema import VenueDisplay

# # Create a test client (acts like a browser/Swagger)
# client = TestClient(app)

# # ==========================================
# # 🧪 TEST 1: THE PLANNING SCENARIO
# # ==========================================
# # We want to prove: If AI says "planning", we MUST search the DB.
# @patch("app.routers.planning.ai_service")      # Mock the AI
# @patch("app.routers.planning.vendor_service")  # Mock the DB Service
# def test_generate_plan_success(mock_vendor_service, mock_ai_service):
    
#     # 1. Fake the AI Response (What Langflow WOULD return)
#     mock_ai_service.generate_date_plan.return_value = {
#         "intent": "planning",
#         "reasoning": "User wants a date.",
#         "location": "Kandy",
#         "venue_tags": ["romantic"],
#         "budget_per_head": 5000,
#         "guest_count": 2
#     }

#     # 2. Fake the Database Results (What Postgres WOULD return)
#     # We create fake objects matching your VenueDisplay schema
#     mock_vendor_service.find_perfect_matches.return_value = [
#         MagicMock(name="Hotel A", description="Nice view", price_per_head=5000.0, tags=["romantic"]),
#         MagicMock(name="Hotel B", description="Good food", price_per_head=4000.0, tags=["quiet"])
#     ]

#     # 3. The Actual Request
#     payload = {"user_query": "I want a romantic dinner in Kandy"}
#     response = client.post("/api/planning/generate", json=payload)

#     # 4. The Assertions (The Proof)
#     assert response.status_code == 200
#     data = response.json()
    
#     # Check if logic worked
#     assert data["intent"] == "planning"
#     assert len(data["matched_venues"]) == 2  # Should have found our 2 fake hotels
#     assert data["matched_venues"][0]["name"] == "Hotel A"

# # ==========================================
# # 🧪 TEST 2: THE CHAT SCENARIO
# # ==========================================
# # We want to prove: If AI says "chat", we MUST NOT search the DB.
# @patch("app.routers.planning.ai_service")
# @patch("app.routers.planning.vendor_service")
# def test_chat_mode_no_db(mock_vendor_service, mock_ai_service):
    
#     # 1. Fake the AI (Just chatting)
#     mock_ai_service.generate_date_plan.return_value = {
#         "intent": "chat",
#         "chat_response": "Hello! How can I help?",
#         "venue_tags": []
#     }

#     # 2. The Request
#     payload = {"user_query": "Hi"}
#     response = client.post("/api/planning/generate", json=payload)

#     # 3. Assertions
#     assert response.status_code == 200
#     data = response.json()
    
#     assert data["intent"] == "chat"
#     assert data["matched_venues"] == [] # List must be empty!
    
#     # Critical Check: Ensure DB service was NEVER called
#     mock_vendor_service.find_perfect_matches.assert_not_called()