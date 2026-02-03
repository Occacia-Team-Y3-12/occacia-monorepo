from pydantic import BaseModel, EmailStr
from typing import Optional, List

# 1. Registration Input
class VendorRegisterRequest(BaseModel):
    business_name: str
    email: EmailStr
    password: str
    location_base: str
    phone: Optional[str] = None

# 2. Login Input
class VendorLoginRequest(BaseModel):
    email: EmailStr
    password: str

# 3. Standard Output (Safe Response)
class VendorResponse(BaseModel):
    id: int
    business_name: str
    email: EmailStr
    location_base: str
    is_verified: bool
    phone: Optional[str] = None

    class Config:
        from_attributes = True # Allows reading from database models

# 4. Token Output
class Token(BaseModel):
    access_token: str
    token_type: str