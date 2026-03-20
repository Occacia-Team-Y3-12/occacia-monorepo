"""
app/schemas/planning_schema.py
"""
from pydantic import BaseModel, ConfigDict, Field
from typing import Any, Dict, List, Optional


class PlanRequest(BaseModel):
    user_query: str = Field(..., description="The user's text input")
    session_id: str = Field(..., description="Unique ID for chat context")


class VenueDisplay(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    price_per_head: Optional[float] = None
    tags: List[str] = []
    total_estimated_price: Optional[float] = None
    match_score: Optional[int] = None
    match_score_max: Optional[int] = None
    match_score_label: Optional[str] = None
    vendor_name: Optional[str] = None
    vendor_phone: Optional[str] = None
    vendor_location: Optional[str] = None
    vendor_email: Optional[str] = None
    is_verified: Optional[bool] = False
    model_config = ConfigDict(from_attributes=True, extra="ignore")


class PlanResponse(BaseModel):
    intent: str
    reasoning: Optional[str] = None
    personality_profile: Optional[str] = None
    chat_response: Optional[str] = None
    gift_suggestion: Optional[str] = None
    event_type: Optional[str] = None
    event_date: Optional[str] = None
    location: Optional[str] = None
    budget_per_head: Optional[float] = None
    guest_count: Optional[int] = None
    venue_tags: List[str] = []
    missing_info: List[str] = []
    matched_venues: List[VenueDisplay] = []

    # Phase 6-7: generated packages returned in chat
    # Each item is a serialised RecommendationPackageResponse dict
    matched_packages: List[Dict[str, Any]] = []

    # Frontend state flags
    ask_save_persona: bool = False
    persona_saved: bool = False
    persona_confirmed: bool = False
    venue_match_tier: Optional[int] = None