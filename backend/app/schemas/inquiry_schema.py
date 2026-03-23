from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class InquiryCreate(BaseModel):
    subject: Optional[str] = None
    message: str

    model_config = {"populate_by_name": True}


class InquiryResponse(BaseModel):
    inquiry_id: str = Field(alias="inquiryId")
    created_by_user_id: str = Field(alias="createdByUserId")
    created_by_role: str = Field(alias="createdByRole")
    subject: Optional[str] = None
    message: str
    status: str
    handled_by_admin_id: Optional[str] = Field(default=None, alias="handledByAdminId")
    admin_reply: Optional[str] = Field(default=None, alias="adminReply")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    resolved_at: Optional[datetime] = Field(default=None, alias="resolvedAt")

    model_config = {"populate_by_name": True, "from_attributes": True}


class InquiryUpdateRequest(BaseModel):
    status: Optional[str] = None
    admin_reply: Optional[str] = Field(default=None, alias="adminReply")

    model_config = {"populate_by_name": True}


class PaginatedInquiriesResponse(BaseModel):
    items: List[InquiryResponse]
    next_cursor: Optional[str] = Field(default=None, alias="nextCursor")

    model_config = {"populate_by_name": True}
