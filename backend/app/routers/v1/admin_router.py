"""
app/routers/v1/admin_router.py
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_admin
from app.core.config import settings
from app.core.database import get_db
from app.models.admin import Admin
from app.models.vendor import Vendor
from app.schemas.admin_schema import (
    AdminRegister, AdminResponse, NotificationResponse, PaginatedNotificationsResponse,
    VendorAdminView, VendorRejectRequest
)
from app.services.admin_service import admin_service 
from app.services.notification_service import notification_service
from app.services.auth_service import _send_email

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])
auth_admin_router = APIRouter(prefix="/auth/admin", tags=["Authentication"])

# --- Email helpers (Required here to satisfy Test Mocks) ---

def _send_approval_email(vendor: Vendor):
    subject = "Your Occacia vendor account has been approved!"
    body = (
        f"Congratulations, {vendor.display_name or vendor.business_name}!\n\n"
        f"Your vendor application for {vendor.business_name} has been approved.\n\n"
        f"Vendor ID: {vendor.vendor_id}\n"
    )
    _send_email(vendor.email, subject, body)

def _send_rejection_email(vendor: Vendor, reason: str):
    subject = "Update on your Occacia vendor application"
    body = f"Reason: {reason}"
    _send_email(vendor.email, subject, body)

# --- Auth Routes ---

@auth_admin_router.post("/register", response_model=AdminResponse, status_code=201)
def register_admin(payload: AdminRegister, db: Session = Depends(get_db)):
    """Provision admin account (internal)."""
    if getattr(settings, "DISABLE_ADMIN_REGISTER", "false").lower() == "true":
        raise HTTPException(status_code=403, detail="Admin registration is disabled.")
        
    return admin_service.register_admin(
        db, 
        email=payload.email, 
        password=payload.password, 
        staff_role=payload.staff_role
    )

@auth_admin_router.post("/login")
def admin_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Admin login."""
    return admin_service.login_admin(db, form_data.username, form_data.password)

@router.get("/vendors", response_model=list[VendorAdminView])
def list_vendors(
    approval_status: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    """List vendors for admin management."""
    _ = current_admin
    return admin_service.list_vendors(db, approval_status=approval_status, status=status)

@router.get("/vendors/{vendor_id}", response_model=VendorAdminView)
def get_vendor_detail(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    """Get vendor detail for admin management."""
    _ = current_admin
    return admin_service.get_vendor(db, vendor_id=vendor_id)

@router.post("/vendors/{vendor_id}/approve", response_model=VendorAdminView)
def approve_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    """Approve vendor registration."""
    vendor = admin_service.approve_vendor(db, vendor_id=vendor_id, admin_email=current_admin.email)
    _send_approval_email(vendor)
    return vendor

@router.post("/vendors/{vendor_id}/reject", response_model=VendorAdminView)
def reject_vendor(
    vendor_id: int,
    body: VendorRejectRequest = VendorRejectRequest(),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    """Reject vendor registration."""
    vendor = admin_service.reject_vendor(db, vendor_id=vendor_id, reason=body.reason, admin_email=current_admin.email)
    _send_rejection_email(vendor, body.reason)
    return vendor


@router.get("/notifications", response_model=PaginatedNotificationsResponse)
def list_notifications(
    limit: int = 50,
    cursor: str | None = None,
    user_id: str | None = None,
    event_id: str | None = None,
    task_id: str | None = None,
    status: str | None = None,
    type: str | None = None,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    _ = current_admin
    items, next_cursor = notification_service.list_notifications(
        db,
        limit=limit,
        cursor=cursor,
        user_id=user_id,
        event_id=event_id,
        task_id=task_id,
        status=status,
        type=type,
    )
    return PaginatedNotificationsResponse(
        items=[NotificationResponse.model_validate(item) for item in items],
        next_cursor=next_cursor,
    )
