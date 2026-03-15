"""
app/schemas/vendor_schema.py
"""
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
