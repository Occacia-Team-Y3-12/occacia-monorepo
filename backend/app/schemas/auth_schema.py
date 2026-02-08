from typing import Annotated, Literal, Union
from pydantic import BaseModel, EmailStr, Field

class RegisterBase(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)

class CustomerRegister(RegisterBase):
    role: Literal["CUSTOMER"] = "CUSTOMER"
    full_name: str = Field(min_length=2)
    phone: str | None = None
    address: str | None = None

class VendorRegister(RegisterBase):
    role: Literal["VENDOR"] = "VENDOR"
    display_name: str = Field(min_length=2)
    contact_phone: str | None = None

RegisterRequest = Annotated[
    Union[CustomerRegister, VendorRegister],
    Field(discriminator="role")
]