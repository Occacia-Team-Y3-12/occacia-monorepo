from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from datetime import datetime
from typing import Optional
import re

# ==========================================
# 📥 REQUEST SCHEMA (Inbound Data)
# ==========================================
class VendorRegisterRequest(BaseModel):
    email: EmailStr 
    display_name: str = Field(..., min_length=3, max_length=50, description="Unique business name")
    phone: str = Field(..., min_length=10, max_length=15)
    business_type: str = Field(default="General")
    address: str = Field(..., min_length=5)
    password: str = Field(..., min_length=8)

    @field_validator("phone")
    @classmethod
    def validate_sl_phone(cls, v):
        # Sri Lankan Mobile Logic: Must start with +94 or 0 and have 9/10 digits
        clean_phone = re.sub(r'[\s\-]', '', v)
        if not re.match(r'^(\+94|0)?7[0-9]{8}$', clean_phone):
            raise ValueError('Invalid Sri Lankan mobile number format')
        return clean_phone

    @field_validator("password")
    @classmethod
    def password_complexity(cls, v):
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v

# ==========================================
# 📤 RESPONSE SCHEMA (Outbound Data)
# ==========================================
class VendorResponse(BaseModel):
    id: int
    email: EmailStr
    display_name: str
    business_type: str
    address: str
    phone: str
    status: str
    is_verified: bool
    created_at: datetime

    # This allows Pydantic to convert SQLAlchemy objects to JSON
    model_config = ConfigDict(from_attributes=True)