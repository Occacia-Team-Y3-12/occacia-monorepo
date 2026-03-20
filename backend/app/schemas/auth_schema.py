from typing import Annotated, Literal, Optional

from pydantic import BaseModel, EmailStr, Field

# --- Registration Schemas ---

class RegisterBase(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)

    model_config = {"populate_by_name": True}

class CustomerRegister(RegisterBase):
    role: Literal["CUSTOMER"] = "CUSTOMER"
    full_name: str = Field(min_length=2, alias="fullName")
    phone: Optional[str] = None
    locale: Optional[str] = None

    model_config = {"populate_by_name": True}

class VendorRegister(RegisterBase):
    role: Literal["VENDOR"] = "VENDOR"
    display_name: str = Field(min_length=2)
    contact_phone: Optional[str] = None

RegisterRequest = Annotated[
    CustomerRegister | VendorRegister,
    Field(discriminator="role")
]

# --- Password Reset & Auth Schemas ---

class ForgotPasswordRequest(BaseModel):
    """Payload to initiate password reset via email."""
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    """Payload to finalize password reset using a secure token."""
    token: str
    new_password: str = Field(min_length=8, alias="newPassword")

    model_config = {"populate_by_name": True}

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)

class ResendVerificationRequest(BaseModel):
    email: EmailStr

class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(alias="refreshToken")

    model_config = {"populate_by_name": True}

# --- Response Schemas ---

class RegisterResponse(BaseModel):
    message: str

class VerifyEmailResponse(BaseModel):
    message: str

class AuthMessageResponse(BaseModel):
    """Generic success or failure message response."""
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
