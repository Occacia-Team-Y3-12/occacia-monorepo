from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


OFFERING_CATEGORIES = [
    "Food & Beverage",
    "Cakes & Bakery",
    "Catering",
    "Drinks & Bar",
    "Entertainment",
    "DJ & Music",
    "Photography & Videography",
    "Band & Live Music",
    "Decor & Flowers",
    "Floral Arrangements",
    "Event Decoration",
    "Venue & Spaces",
    "Transport",
    "Other",
]

QUALITY_TIERS = ["LOW", "MEDIUM", "HIGH"]


class OfferingCreate(BaseModel):
    name: str
    category: str
    description: Optional[str] = None
    price: float
    currency: str = "LKR"
    unit: Optional[str] = None
    quality_tier: str = Field(default="MEDIUM", alias="qualityTier")
    is_active: bool = Field(default=True, alias="isActive")
    is_available: bool = Field(default=True, alias="isAvailable")

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str) -> str:
        if value not in OFFERING_CATEGORIES:
            raise ValueError(f"category must be one of: {OFFERING_CATEGORIES}")
        return value

    @field_validator("quality_tier")
    @classmethod
    def validate_tier(cls, value: str) -> str:
        tier = value.upper()
        if tier not in QUALITY_TIERS:
            raise ValueError(f"quality_tier must be one of: {QUALITY_TIERS}")
        return tier

    @field_validator("price")
    @classmethod
    def validate_price(cls, value: float) -> float:
        if value < 0:
            raise ValueError("price must be non-negative")
        return value

    model_config = {"populate_by_name": True}


class OfferingUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    unit: Optional[str] = None
    quality_tier: Optional[str] = Field(default=None, alias="qualityTier")
    is_active: Optional[bool] = Field(default=None, alias="isActive")
    is_available: Optional[bool] = Field(default=None, alias="isAvailable")

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and value not in OFFERING_CATEGORIES:
            raise ValueError(f"category must be one of: {OFFERING_CATEGORIES}")
        return value

    @field_validator("quality_tier")
    @classmethod
    def validate_tier(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        tier = value.upper()
        if tier not in QUALITY_TIERS:
            raise ValueError(f"quality_tier must be one of: {QUALITY_TIERS}")
        return tier

    @field_validator("price")
    @classmethod
    def validate_price(cls, value: Optional[float]) -> Optional[float]:
        if value is not None and value < 0:
            raise ValueError("price must be non-negative")
        return value

    model_config = {"populate_by_name": True}


class OfferingResponse(BaseModel):
    offering_id: str = Field(alias="offeringId")
    vendor_id: str = Field(alias="vendorId")
    name: str
    category: str
    description: Optional[str] = None
    price: float
    currency: str
    unit: Optional[str] = None
    quality_tier: str = Field(alias="qualityTier")
    is_active: bool = Field(alias="isActive")
    is_available: bool = Field(alias="isAvailable")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    model_config = {"populate_by_name": True, "from_attributes": True}


class OfferingListResponse(BaseModel):
    items: list[OfferingResponse]


class TaskOfferingResponse(BaseModel):
    offering_id: str = Field(alias="offeringId")
    name: str
    category: str
    description: Optional[str] = None
    price: float
    currency: str
    unit: Optional[str] = None
    quality_tier: str = Field(alias="qualityTier")
    vendor_id: str = Field(alias="vendorId")
    vendor_name: Optional[str] = Field(default=None, alias="vendorName")
    rank: int
    score: Optional[float] = None
    is_selected: bool = Field(alias="isSelected")
    selected_at: Optional[datetime] = Field(default=None, alias="selectedAt")

    model_config = {"populate_by_name": True, "from_attributes": True}


class TaskOfferingListResponse(BaseModel):
    items: list[TaskOfferingResponse]
