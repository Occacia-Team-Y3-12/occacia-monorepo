from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr


class AdminRegister(BaseModel):
    email: EmailStr
    password: str
    staff_role: Optional[str] = "staff"


class AdminResponse(BaseModel):
    id: int
    admin_id: str
    email: str
    staff_role: Optional[str]
    model_config = ConfigDict(from_attributes=True)


class VendorAdminView(BaseModel):
    id: int
    vendor_id: Optional[str]
    business_name: str
    email: str
    phone: Optional[str]
    display_name: Optional[str]
    contact_phone: Optional[str]
    location_base: Optional[str]
    approval_status: str
    is_verified: bool
    approved_at: Optional[datetime]
    # Spec: AccountStatus — ACTIVE / SUSPENDED / DISABLED
    # Falls back to None if the column doesn't exist on older DB rows
    status: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class VendorRejectRequest(BaseModel):
    reason: str = "Your application did not meet our current requirements."


class NotificationResponse(BaseModel):
    notification_id: str
    user_id: str
    event_id: str | None = None
    task_id: str | None = None
    channel: str
    type: str
    status: str
    dedupe_key: str | None = None
    payload: dict
    error_message: str | None = None
    sent_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedNotificationsResponse(BaseModel):
    items: list[NotificationResponse]
    next_cursor: str | None = None
