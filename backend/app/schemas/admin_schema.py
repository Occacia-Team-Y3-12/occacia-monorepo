from __future__ import annotations
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.schemas.event_planning_schema import TaskResponse
from app.schemas.package_schema import (
    FulfillmentRequestResponse,
    PackageOrderResponse,
)


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
    status: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class VendorRejectRequest(BaseModel):
    reason: str = "Your application did not meet our current requirements."


class NotificationResponse(BaseModel):
    notification_id: str
    user_id: str
    recipient_email: str
    recipient_name: str | None = None
    event_id: str | None = None
    task_id: str | None = None
    channel: str
    type: str
    status: str
    dedupe_key: str | None = None
    payload: dict
    subject: str
    body_text: str
    body_html: str | None = None
    provider: str | None = None
    provider_message_id: str | None = None
    attempt_count: int
    max_attempts: int
    last_attempt_at: datetime | None = None
    next_attempt_at: datetime | None = None
    error_message: str | None = None
    sent_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedNotificationsResponse(BaseModel):
    items: list[NotificationResponse]
    next_cursor: str | None = None


class CustomerAdminView(BaseModel):
    customer_id: str
    email: str
    full_name: str
    phone: Optional[str] = None
    locale: Optional[str] = None
    status: str
    model_config = ConfigDict(from_attributes=True)


class PaginatedCustomers(BaseModel):
    items: list[CustomerAdminView]
    nextCursor: Optional[str] = None


class CustomerStatusUpdateRequest(BaseModel):
    status: str = Field(..., pattern="^(ACTIVE|SUSPENDED|DISABLED|PENDING)$")


SupportActionType = Literal[
    "NOTE_ONLY",
    "REASSIGN_VENDOR",
    "UNASSIGN_VENDOR",
    "UNLOCK_EDITING",
    "EXTEND_EXPIRY",
    "OVERRIDE_STATUS",
    "ESCALATE",
]

AdminTaskAction = Literal[
    "UNASSIGN_VENDOR",
    "EXTEND_EXPIRY",
    "OVERRIDE_STATUS",
    "UNLOCK_EDITING",
    "REASSIGN_VENDOR",
]


class InternalNoteResponse(BaseModel):
    note_id: str = Field(alias="noteId")
    admin_id: str = Field(alias="adminId")
    package_order_id: str | None = Field(default=None, alias="packageOrderId")
    event_id: str | None = Field(default=None, alias="eventId")
    task_id: str | None = Field(default=None, alias="taskId")
    vendor_id: str | None = Field(default=None, alias="vendorId")
    action_type: SupportActionType = Field(alias="actionType")
    note: str
    created_at: datetime = Field(alias="createdAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class InternalNoteCreateRequest(BaseModel):
    package_order_id: str | None = Field(default=None, alias="packageOrderId")
    event_id: str | None = Field(default=None, alias="eventId")
    task_id: str | None = Field(default=None, alias="taskId")
    vendor_id: str | None = Field(default=None, alias="vendorId")
    action_type: SupportActionType = Field(alias="actionType")
    note: str

    @field_validator("note")
    @classmethod
    def validate_note(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("note must not be empty")
        return trimmed

    model_config = ConfigDict(populate_by_name=True)


class PaginatedInternalNotesResponse(BaseModel):
    items: list[InternalNoteResponse]
    next_cursor: str | None = Field(default=None, alias="nextCursor")

    model_config = ConfigDict(populate_by_name=True)


class PaginatedPackageOrdersResponse(BaseModel):
    items: list[PackageOrderResponse]
    next_cursor: str | None = Field(default=None, alias="nextCursor")

    model_config = ConfigDict(populate_by_name=True)


class PaginatedTasksResponse(BaseModel):
    items: list[TaskResponse]
    next_cursor: str | None = Field(default=None, alias="nextCursor")

    model_config = ConfigDict(populate_by_name=True)


class PaginatedFulfillmentRequestsResponse(BaseModel):
    items: list[FulfillmentRequestResponse]
    next_cursor: str | None = Field(default=None, alias="nextCursor")

    model_config = ConfigDict(populate_by_name=True)


class AdminTaskSupportActionRequest(BaseModel):
    action: AdminTaskAction
    assigned_vendor_id: str | None = Field(default=None, alias="assignedVendorId")
    expires_at: datetime | None = Field(default=None, alias="expiresAt")
    status: str | None = None
    note: str | None = None

    @field_validator("note")
    @classmethod
    def validate_optional_note(cls, value: str | None) -> str | None:
        if value is None:
            return value
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("note must not be empty")
        return trimmed

    model_config = ConfigDict(populate_by_name=True)


class DashboardMetricCounts(BaseModel):
    total: int
    active: int
    pending: int


class AdminDashboardResponse(BaseModel):
    users: DashboardMetricCounts
    users_table: DashboardMetricCounts = Field(alias="usersTable")
    vendors: DashboardMetricCounts
    events: DashboardMetricCounts
    package_orders: DashboardMetricCounts = Field(alias="packageOrders")
    generated_at: datetime = Field(alias="generatedAt")

    model_config = ConfigDict(populate_by_name=True)
