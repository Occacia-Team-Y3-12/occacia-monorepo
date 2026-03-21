from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.event_planning_schema import TaskResponse


class PackageCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    price_per_head: Optional[float] = None
    min_guests: Optional[int] = 1
    max_guests: Optional[int] = 100
    tags: Optional[List[str]] = []
    location_coverage: Optional[str] = None
    blocked_dates: Optional[List[str]] = []


class PackageUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    price_per_head: Optional[float] = None
    min_guests: Optional[int] = None
    max_guests: Optional[int] = None
    tags: Optional[List[str]] = None
    location_coverage: Optional[str] = None
    blocked_dates: Optional[List[str]] = None


class PackageResponse(BaseModel):
    id: int
    vendor_id: int
    name: str
    description: Optional[str]
    price: float
    price_per_head: Optional[float]
    min_guests: Optional[int]
    max_guests: Optional[int]
    tags: Optional[List[str]]
    location_coverage: Optional[str]
    blocked_dates: Optional[List[str]]
    model_config = ConfigDict(from_attributes=True)


class PackageOrderResponse(BaseModel):
    packageOrderId: str
    eventId: str
    packageId: str
    packageOrderTotalPrice: float
    currency: str
    status: str
    createdAt: datetime
    statusUpdatedAt: datetime
    notes: Optional[str] = None
    idempotencyKey: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class PaginatedPackageOrdersResponse(BaseModel):
    items: List[PackageOrderResponse]
    nextCursor: Optional[str] = None


class FulfillmentRequestResponse(BaseModel):
    fulfillmentRequestId: str
    packageOrderId: str
    taskId: str
    vendorId: str
    offeringId: str
    status: str
    requestedAt: datetime
    respondBy: Optional[datetime] = None
    respondedAt: Optional[datetime] = None
    responseNote: Optional[str] = None
    attemptNo: int

    model_config = ConfigDict(from_attributes=True)


class PackageOrderDetailsResponse(BaseModel):
    packageOrder: PackageOrderResponse
    tasks: List[TaskResponse]

    model_config = ConfigDict(from_attributes=True)


class ConfirmPackageOrderResponse(BaseModel):
    packageOrder: PackageOrderResponse
    tasks: List[TaskResponse]
    fulfillmentRequests: List[FulfillmentRequestResponse]

    model_config = ConfigDict(from_attributes=True)


class ReassignTaskRequest(BaseModel):
    offeringId: str
    note: Optional[str] = None


class ReassignTaskResponse(BaseModel):
    task: TaskResponse
    fulfillmentRequest: FulfillmentRequestResponse

    model_config = ConfigDict(from_attributes=True)
