from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


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
