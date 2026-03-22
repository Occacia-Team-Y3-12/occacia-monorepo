"""
app/schemas/vendor_schema.py
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Any

from pydantic import BaseModel, EmailStr, Field, field_validator
from pydantic import ConfigDict

from app.schemas.event_planning_schema import TaskResponse
from app.schemas.package_schema import FulfillmentRequestResponse


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

# Update this class back


class VendorUpdate(BaseModel):
    business_name: Optional[str] = Field(default=None, alias="businessName")
    location_base: Optional[str] = Field(default=None, alias="locationBase")
    phone: Optional[str] = None
    display_name: Optional[str] = Field(default=None, alias="displayName")
    contact_phone: Optional[str] = Field(default=None, alias="contactPhone")

    model_config = ConfigDict(populate_by_name=True)

# 3. Standard Output (Safe Response)


class VendorTaskSummary(BaseModel):
    """Summary of a vendor's task counts by status."""
    pending: int = Field(0, description="Count of tasks pending acceptance.")
    accepted: int = Field(
        0, description="Count of tasks accepted by the vendor.")
    in_progress: int = Field(
        0, description="Count of tasks currently in progress.")
    completed: int = Field(0, description="Count of tasks completed.")
    cancelled: int = Field(0, description="Count of tasks cancelled.")

    model_config = ConfigDict(from_attributes=True)


class VendorResponse(BaseModel):
    id: int
    user_id: int
    business_name: str
    email: EmailStr
    location_base: Optional[str] = None
    phone: Optional[str] = None
    display_name: Optional[str] = None
    contact_phone: Optional[str] = None
    is_verified: bool
    approval_status: str
    task_summary: Optional[VendorTaskSummary] = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedFulfillmentRequestsResponse(BaseModel):
    items: list[FulfillmentRequestResponse]
    next_cursor: str | None = Field(default=None, alias="nextCursor")

    model_config = ConfigDict(populate_by_name=True)


class RespondFulfillmentRequestRequest(BaseModel):
    decision: str
    response_note: str | None = Field(default=None, alias="responseNote")

    @field_validator("decision")
    @classmethod
    def validate_decision(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in {"ACCEPT", "REJECT"}:
            raise ValueError("decision must be ACCEPT or REJECT")
        return normalized

    @field_validator("response_note")
    @classmethod
    def validate_response_note(cls, value: str | None) -> str | None:
        if value is None:
            return None
        trimmed = value.strip()
        return trimmed or None

    model_config = ConfigDict(populate_by_name=True)


class RespondFulfillmentRequestResponse(BaseModel):
    fulfillment_request: FulfillmentRequestResponse = Field(
        alias="fulfillmentRequest")
    task: TaskResponse

    model_config = ConfigDict(populate_by_name=True)


class PaginatedVendorTasksResponse(BaseModel):
    items: list[TaskResponse]
    next_cursor: str | None = Field(default=None, alias="nextCursor")

    model_config = ConfigDict(populate_by_name=True)


class VendorTaskUpdateRequest(BaseModel):
    status: str
    note: str | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in {"IN_PROGRESS", "DONE"}:
            raise ValueError("status must be IN_PROGRESS or DONE")
        return normalized

    @field_validator("note")
    @classmethod
    def validate_note(cls, value: str | None) -> str | None:
        if value is None:
            return None
        trimmed = value.strip()
        return trimmed or None
