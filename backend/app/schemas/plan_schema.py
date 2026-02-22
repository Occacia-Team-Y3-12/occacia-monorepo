from pydantic import BaseModel, Field
from typing import List, Optional

# 🎯 THE FIX: Added session_id so the router can find it.
class PlanRequest(BaseModel):
    user_query: str = Field(..., description="The user's text input")
    session_id: str = Field(..., description="Unique ID for chat context")

class VenueDisplay(BaseModel):
    name: str
    description: Optional[str] = None
    price_per_head: Optional[float] = 0.0
    tags: List[str] = []

    class Config:
        from_attributes = True  # ✅ Crucial for SQLAlchemy compatibility

class PlanResponse(BaseModel):
    intent: str
    reasoning: Optional[str] = None
    personality_profile: Optional[str] = None
    chat_response: Optional[str] = None
    gift_suggestion: Optional[str] = None
    event_type: Optional[str] = None
    location: Optional[str] = "Any"
    budget_per_head: float = 0.0
    guest_count: int = 0
    venue_tags: List[str] = []
    missing_info: List[str] = []
    matched_venues: List[VenueDisplay] = []