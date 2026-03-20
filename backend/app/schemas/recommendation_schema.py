from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RecommendationPackageItemResponse(BaseModel):
    task_id: str = Field(alias="taskId")
    task_name: str = Field(alias="taskName")
    quantity: int
    offering_id: str = Field(alias="offeringId")
    offering_name: str = Field(alias="offeringName")
    offering_category: str = Field(alias="offeringCategory")
    vendor_id: str = Field(alias="vendorId")
    vendor_name: str | None = Field(default=None, alias="vendorName")
    unit_price: float = Field(alias="unitPrice")
    task_price: float = Field(alias="taskPrice")
    currency: str
    ai_rank: int | None = Field(default=None, alias="aiRank")

    model_config = {"populate_by_name": True}


class TaskRecommendationResponse(BaseModel):
    recommendation_id: str = Field(alias="recommendationId")
    event_id: str = Field(alias="eventId")
    task_id: str = Field(alias="taskId")
    offering_id: str = Field(alias="offeringId")
    score: float
    rank: int
    generated_at: datetime = Field(alias="generatedAt")

    model_config = {"populate_by_name": True}


class TaskRecommendationListResponse(BaseModel):
    items: list[TaskRecommendationResponse]

    model_config = {"populate_by_name": True}


class RecommendationPackageResponse(BaseModel):
    package_id: str = Field(alias="packageId")
    event_id: str = Field(alias="eventId")
    package_type: str = Field(alias="packageType")
    package_total_price: float = Field(alias="packageTotalPrice")
    currency: str
    is_customized: bool = Field(alias="isCustomized")
    base_package_id: str | None = Field(default=None, alias="basePackageId")
    created_by_customer_id: str | None = Field(default=None, alias="createdByCustomerId")
    generated_at: datetime = Field(alias="generatedAt")
    expires_at: datetime | None = Field(default=None, alias="expiresAt")
    is_expired: bool = Field(alias="isExpired")
    items: list[RecommendationPackageItemResponse]

    model_config = {"populate_by_name": True}


class RecommendationPackageDetailsResponse(RecommendationPackageResponse):
    allowed_offerings_by_task: dict[str, list[TaskRecommendationResponse]] = Field(alias="allowedOfferingsByTask")

    model_config = {"populate_by_name": True}


class RecommendationPackageListResponse(BaseModel):
    event_id: str = Field(alias="eventId")
    generated_at: datetime = Field(alias="generatedAt")
    expires_at: datetime | None = Field(default=None, alias="expiresAt")
    is_expired: bool = Field(alias="isExpired")
    packages: list[RecommendationPackageResponse]

    model_config = {"populate_by_name": True}


class CustomPackageItemRequest(BaseModel):
    package_item_id: str | None = Field(default=None, alias="packageItemId")
    package_id: str | None = Field(default=None, alias="packageId")
    task_id: str = Field(alias="taskId")
    offering_id: str = Field(alias="offeringId")
    quantity: int | None = None
    unit_price: float | None = Field(default=None, alias="unitPrice")
    line_total: float | None = Field(default=None, alias="lineTotal")

    model_config = {"populate_by_name": True}


class CreateCustomPackageRequest(BaseModel):
    base_package_id: str = Field(alias="basePackageId")
    items: list[CustomPackageItemRequest] = Field(min_length=1)

    model_config = {"populate_by_name": True}


class UpdateCustomPackageRequest(BaseModel):
    items: list[CustomPackageItemRequest] = Field(min_length=1)

    model_config = {"populate_by_name": True}
