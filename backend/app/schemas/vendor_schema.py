from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr

# 1. Registration Input
class VendorRegisterRequest(BaseModel):
    business_name: str
    email: EmailStr
    password: str
    location_base: Optional[str] = None
    phone: Optional[str] = None
    display_name: Optional[str] = None
    contact_phone: Optional[str] = None

# 2. Login Input
class VendorLoginRequest(BaseModel):
    email: EmailStr
    password: str

# 3. Standard Output (Safe Response)
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

# 4. Token Output
class Token(BaseModel):
    access_token: str
    token_type: str
# backend/app/schemas/vendor_schema.py

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum

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

# Vendor Schemas
class VendorBase(BaseModel):
    business_name: str
    business_email: EmailStr
    business_phone: Optional[str] = None
    business_address: Optional[str] = None
    business_type: Optional[str] = None
    description: Optional[str] = None

class VendorCreate(VendorBase):
    user_id: Optional[int] = None
    vendor_type: VendorType = VendorType.INDIVIDUAL
    organization_id: Optional[int] = None

class VendorUpdate(BaseModel):
    business_name: Optional[str] = None
    business_email: Optional[EmailStr] = None
    business_phone: Optional[str] = None
    business_address: Optional[str] = None
    business_type: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None

class VendorStatusUpdate(BaseModel):
    status: VendorStatus
    status_reason: Optional[str] = None

class VendorResponse(VendorBase):
    id: int
    status: VendorStatus
    status_reason: Optional[str] = None
    vendor_type: VendorType
    organization_id: Optional[int] = None
    logo_url: Optional[str] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class VendorDetailResponse(VendorResponse):
    organization: Optional['OrganizationResponse'] = None
    
    class Config:
        from_attributes = True

# Organization Schemas
class OrganizationBase(BaseModel):
    name: str
    legal_name: str
    registration_number: Optional[str] = None
    tax_id: Optional[str] = None
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None

class OrganizationCreate(OrganizationBase):
    pass

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

class OrganizationStatusUpdate(BaseModel):
    status: OrganizationStatus
    status_reason: Optional[str] = None

class OrganizationResponse(OrganizationBase):
    id: int
    status: OrganizationStatus
    status_reason: Optional[str] = None
    logo_url: Optional[str] = None
    business_license_url: Optional[str] = None
    tax_certificate_url: Optional[str] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class OrganizationDetailResponse(OrganizationResponse):
    vendors: List[VendorResponse] = []
    
    class Config:
        from_attributes = True

# List Response Schemas
class VendorListResponse(BaseModel):
    items: List[VendorResponse]
    total: int
    page: int
    page_size: int

class OrganizationListResponse(BaseModel):
    items: List[OrganizationResponse]
    total: int
    page: int
    page_size: int

# Filter Schemas
class VendorFilter(BaseModel):
    status: Optional[VendorStatus] = None
    vendor_type: Optional[VendorType] = None
    search: Optional[str] = None

class OrganizationFilter(BaseModel):
    status: Optional[OrganizationStatus] = None
    search: Optional[str] = None

# Update forward references
VendorDetailResponse.model_rebuild()
OrganizationDetailResponse.model_rebuild()