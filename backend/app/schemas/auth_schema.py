from typing import Annotated, Literal
from pydantic import BaseModel, EmailStr, Field

# ==========================================
# 🛠️ BASE & REGISTRATION SCHEMAS
# ==========================================

class RegisterBase(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)

class CustomerRegister(RegisterBase):
    role: Literal["CUSTOMER"] = "CUSTOMER"
    full_name: str = Field(min_length=2)
    phone: str | None = None
    address: str | None = None
    locale: str | None = None

class VendorRegister(RegisterBase):
    role: Literal["VENDOR"] = "VENDOR"
    display_name: str = Field(min_length=2)
    contact_phone: str | None = None

RegisterRequest = Annotated[
    CustomerRegister | VendorRegister,
    Field(discriminator="role")
]

# ==========================================
# 🔐 PASSWORD RESET SCHEMAS (UC-07)
# ==========================================

class ForgotPasswordRequest(BaseModel):
    """Payload to initiate reset: Customer provides their email."""
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    """Payload to finalize reset: Customer provides token and new password."""
    token: str
    new_password: str = Field(min_length=6)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)

class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(alias="refreshToken")

    model_config = {"populate_by_name": True}

# ==========================================
# 🚀 RESPONSE SCHEMAS
# ==========================================

class RegisterResponse(BaseModel):
    message: str
    email: EmailStr

class VerifyEmailResponse(BaseModel):
    message: str

class AuthMessageResponse(BaseModel):
    """Generic success/failure message response."""
    message: str

class AuthUserResponse(BaseModel):
    user_id: str = Field(alias="userId")
    email: EmailStr
    role: str
    status: str

    model_config = {"populate_by_name": True}

class AuthResponse(BaseModel):
    access_token: str = Field(alias="accessToken")
    refresh_token: str = Field(alias="refreshToken")
    user: AuthUserResponse

    model_config = {"populate_by_name": True}
