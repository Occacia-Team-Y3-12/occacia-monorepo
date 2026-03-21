# backend/app/schemas/organization_schema.py

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class OrganizationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class OrganizationBase(BaseModel):
    name: str
    legal_name: Optional[str] = None
    registration_number: Optional[str] = None
    tax_id: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    business_license_url: Optional[str] = None
    tax_certificate_url: Optional[str] = None


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(OrganizationBase):
    pass


class OrganizationResponse(OrganizationBase):
    id: int
    status: OrganizationStatus
    status_reason: Optional[str] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class OrganizationDetailResponse(OrganizationResponse):
    # Potentially include more details, like associated vendors
    pass


class OrganizationListResponse(BaseModel):
    items: List[OrganizationResponse]
    total: int
    page: int
    page_size: int


class OrganizationStatusUpdate(BaseModel):
    status: OrganizationStatus
    reason: Optional[str] = None


class OrganizationFilter(BaseModel):
    status: Optional[OrganizationStatus] = None
    search: Optional[str] = None
