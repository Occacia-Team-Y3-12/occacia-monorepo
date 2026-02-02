from pydantic import BaseModel, EmailStr, Field, ConfigDict # <--- IMPORT ConfigDict
from datetime import datetime

# 1. The Input Model (What you send)
class VendorCreate(BaseModel):
    business_name: str = Field(..., min_length=3)
    business_type: str
    email: EmailStr
    contact_number: str
    address: str

# 2. The Output Model (What you get back)
class VendorResponse(VendorCreate):
    id: int
    status: str
    created_at: datetime

    # OLD WAY: class Config: from_attributes = True
    # NEW WAY:
    model_config = ConfigDict(from_attributes=True)