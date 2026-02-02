from pydantic import BaseModel, ConfigDict
from typing import List, Optional

# 1. The Input Request
class PlanRequest(BaseModel):
    user_query: str
    session_id: str
# 2. The Venue Display (Matches your DB Table fields)
class VenueDisplay(BaseModel):
    name: str
    description: Optional[str] = None
    # Changed from 0.0 to None to allow clean filtering
    price_per_head: Optional[float] = None 
    tags: List[str] = []

    # Pydantic v2 configuration for SQLAlchemy compatibility
    model_config = ConfigDict(from_attributes=True)

# 3. The Final Response Schema (Flattened & Flexible)
class PlanResponse(BaseModel):
    intent: str
    
    # 🧠 Conversational Fields
    # These are now Optional and default to None to stay hidden in Chat mode
    reasoning: Optional[str] = None 
    personality_profile: Optional[str] = None
    chat_response: Optional[str] = None
    
    # 📅 Planning-Specific Fields
    # We remove default values like "Any" or 0 and replace them with None
    # to ensure they are stripped out by 'response_model_exclude_none'
    gift_suggestion: Optional[str] = None
    event_type: Optional[str] = None
    location: Optional[str] = None 
    budget_per_head: Optional[float] = None
    guest_count: Optional[int] = None
    
    # 🏷️ Metadata and Search Results
    # Using Optional[List] allows these to be completely hidden when empty
    venue_tags: Optional[List[str]] = None
    missing_info: Optional[List[str]] = None
    matched_venues: Optional[List[VenueDisplay]] = None