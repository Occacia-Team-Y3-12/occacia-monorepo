"""
app/schemas/vendor_schema.py
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr

# --- Requests ---

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

# FIX: Added strict schema for profile updates
class VendorUpdate(BaseModel):
    displayName: Optional[str] = None
    contactPhone: Optional[str] = None

# --- Responses ---

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
