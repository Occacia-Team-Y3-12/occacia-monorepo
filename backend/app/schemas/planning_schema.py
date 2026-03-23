"""
app/schemas/planning_schema.py
"""
from __future__ import annotations
from pydantic import BaseModel, ConfigDict, Field
from typing import Any, Dict, List, Optional, Union


class PlanRequest(BaseModel):
    user_query: str = Field(..., description="The user's text input")
    session_id: str = Field(..., description="Unique ID for chat context")


class VenueDisplay(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
        populate_by_name=True,
    )
    id: Optional[Union[int, str]] = None
    name: str
    description: Optional[str] = None
    price_per_head: Optional[float] = Field(default=None, alias="pricePerHead")
    total_estimated_price: Optional[float] = Field(default=None, alias="totalEstimatedPrice")
    tags: List[str] = []
    location: Optional[str] = None
    match_score: Optional[int] = Field(default=None, alias="matchScore")
    match_score_max: Optional[int] = Field(default=None, alias="matchScoreMax")
    match_score_label: Optional[str] = Field(default=None, alias="matchScoreLabel")
    vendor_name: Optional[str] = Field(default=None, alias="vendorName")
    vendor_phone: Optional[str] = None
    vendor_location: Optional[str] = None
    vendor_email: Optional[str] = None
    is_verified: Optional[bool] = False
    tweak_note: Optional[str] = Field(default=None, alias="tweakNote")


class PlanResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    intent: Optional[str] = None
    reasoning: Optional[str] = None
    personality_profile: Optional[str] = None
    chat_response: Optional[str] = Field(default=None, alias="reply")
    event_type: Optional[str] = None
    event_date: Optional[str] = None
    location: Optional[str] = None
    budget_per_head: Optional[float] = None
    guest_count: Optional[int] = None
    venue_tags: List[str] = []
    missing_info: List[str] = []
    matched_venues: List[VenueDisplay] = []
    matched_packages: List[Dict[str, Any]] = []

    # Frontend state flags
    ask_save_persona: bool = False
    persona_saved: bool = False
    persona_confirmed: bool = False
    venue_match_tier: Optional[int] = None
    booking_created: bool = False
    booking_id: Optional[str] = None
    redirect_url: Optional[str] = None