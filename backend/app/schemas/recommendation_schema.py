from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RecommendationPackageItemResponse(BaseModel):
    task_id: str = Field(alias="taskId")
    task_name: str = Field(alias="taskName")
    quantity: int
    offering_id: str = Field(alias="offeringId")
    offering_name: str = Field(alias="offeringName")
    vendor_id: str = Field(alias="vendorId")
    vendor_name: str | None = Field(default=None, alias="vendorName")
    unit_price: float = Field(alias="unitPrice")
    task_price: float = Field(alias="taskPrice")
    currency: str
    ai_rank: int | None = Field(default=None, alias="aiRank")

    model_config = {"populate_by_name": True}


class RecommendationPackageResponse(BaseModel):
    package_id: str = Field(alias="packageId")
    event_id: str = Field(alias="eventId")
    package_type: str = Field(alias="packageType")
    package_total_price: float = Field(alias="packageTotalPrice")
    currency: str
    is_customized: bool = Field(alias="isCustomized")
    generated_at: datetime = Field(alias="generatedAt")
    expires_at: datetime | None = Field(default=None, alias="expiresAt")
    is_expired: bool = Field(alias="isExpired")
    items: list[RecommendationPackageItemResponse]

    model_config = {"populate_by_name": True}


class RecommendationPackageListResponse(BaseModel):
    event_id: str = Field(alias="eventId")
    generated_at: datetime = Field(alias="generatedAt")
    expires_at: datetime | None = Field(default=None, alias="expiresAt")
    is_expired: bool = Field(alias="isExpired")
    packages: list[RecommendationPackageResponse]

    model_config = {"populate_by_name": True}
