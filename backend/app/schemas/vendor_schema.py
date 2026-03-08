from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from app.common.enums import VendorStatus

# contains fields common to both reading and writing vendor data
class VendorBase(BaseModel):
    business_name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., min_length=5, max_length=20)
    description: Optional[str] = Field(None, max_length=500)
    website: Optional[str] = None

class VendorCreate(VendorBase):
    email: EmailStr
    password: str = Field(..., min_length=8)
#test
# VendorUpdate is used for patch requests to modify existing profiles
class VendorUpdate(BaseModel):
    business_name: Optional[str] = None
    contact_name: Optional[str] = None
    phone_number: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None

# VendorResponse defines the structure of data sent back to the client
class VendorResponse(VendorBase):
    id: str
    user_id: str
    # status: The current approval state (PENDING, APPROVED, etc.)
    status: VendorStatus
    
    # this enables something ( Pydantic to read data directly from SQLAlchemy model objects)
    class Config:
        from_attributes = True