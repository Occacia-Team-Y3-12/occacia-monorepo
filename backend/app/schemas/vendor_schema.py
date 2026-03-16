"""
app/schemas/vendor_schema.py
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class VendorRegisterRequest(BaseModel):
    business_name: str
    email: EmailStr
    password: str
    location_base: Optional[str] = None
    phone: Optional[str] = None
    display_name: Optional[str] = None
    contact_phone: Optional[str] = None


class VendorLoginRequest(BaseModel):
    email: EmailStr
    password: str


class VendorUpdate(BaseModel):
    business_name: Optional[str] = Field(default=None, alias="businessName")
    location_base: Optional[str] = Field(default=None, alias="locationBase")
    phone: Optional[str] = None
    display_name: Optional[str] = Field(default=None, alias="displayName")
    contact_phone: Optional[str] = Field(default=None, alias="contactPhone")

    model_config = ConfigDict(populate_by_name=True)


class VendorResponse(BaseModel):
    id: int
    vendor_id: Optional[str] = None
    business_name: str
    email: EmailStr
    location_base: Optional[str] = None
    is_verified: bool
    phone: Optional[str] = None
    display_name: Optional[str] = None
    contact_phone: Optional[str] = None
    approval_status: Optional[str] = None
    approved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


class VendorStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class OrganizationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class VendorType(str, Enum):
    INDIVIDUAL = "individual"
    ORGANIZATION = "organization"


class VendorDetailResponse(VendorResponse):
    status_reason: Optional[str] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    vendor_type: Optional[VendorType] = None
    organization_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class OrganizationCreate(BaseModel):
    name: str
    legal_name: Optional[str] = None
    registration_number: Optional[str] = None
    tax_id: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    business_license_url: Optional[str] = None
    tax_certificate_url: Optional[str] = None


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    legal_name: Optional[str] = None
    registration_number: Optional[str] = None
    tax_id: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    business_license_url: Optional[str] = None
    tax_certificate_url: Optional[str] = None


class OrganizationResponse(BaseModel):
    id: int
    name: str
    legal_name: Optional[str] = None
    registration_number: Optional[str] = None
    tax_id: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    status: Optional[OrganizationStatus] = None
    status_reason: Optional[str] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    business_license_url: Optional[str] = None
    tax_certificate_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class OrganizationDetailResponse(OrganizationResponse):
    pass


class VendorListResponse(BaseModel):
    items: list[VendorResponse]
    total: int
    page: int
    page_size: int


class OrganizationListResponse(BaseModel):
    items: list[OrganizationResponse]
    total: int
    page: int
    page_size: int


class VendorStatusUpdate(BaseModel):
    status: VendorStatus
    reason: Optional[str] = None


class OrganizationStatusUpdate(BaseModel):
    status: OrganizationStatus
    reason: Optional[str] = None


class VendorFilter(BaseModel):
    status: Optional[VendorStatus] = None
    vendor_type: Optional[str] = None
    search: Optional[str] = None


class OrganizationFilter(BaseModel):
    status: Optional[OrganizationStatus] = None
    search: Optional[str] = None
