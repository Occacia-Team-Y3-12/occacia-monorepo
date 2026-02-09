from pydantic import BaseModel
from typing import List, Optional, Any

# 1. The Input Request
class PlanRequest(BaseModel):
    user_query: str

# 2. The Venue Display (Matches your DB Table fields)
class VenueDisplay(BaseModel):
    name: str
    description: Optional[str] = None
    price_per_head: Optional[float] = 0.0
    tags: List[str] = []

    class Config:
        from_attributes = True  # ✅ CRITICAL: Allows conversion from SQLAlchemy Object

# 3. The Final Response Schema (Flattened)
class PlanResponse(BaseModel):
    intent: str
    reasoning: str
    personality_profile: Optional[str] = None
    chat_response: Optional[str] = None
    gift_suggestion: Optional[str] = None
    event_type: Optional[str] = None
    location: Optional[str] = "Any"
    budget_per_head: float = 0.0
    guest_count: int = 0
    venue_tags: List[str] = []
    missing_info: List[str] = []
    
    # ✅ FIX: Strictly typed list forces the conversion from SQL -> JSON
    matched_venues: List[VenueDisplay] = []