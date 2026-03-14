"""
app/routers/v1/admin_router.py
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.admin import Admin
from app.models.vendor import Vendor
from app.schemas.admin_schema import (
    AdminRegister, AdminResponse, VendorAdminView, VendorRejectRequest
)
from app.core.dependencies import get_current_admin # Move get_current_admin to your dependencies file
from app.services.auth_admin_service import auth_admin_service
from app.services.admin_service import admin_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])
auth_admin_router = APIRouter(prefix="/auth/admin", tags=["Authentication"])

# --- Response Builders ---

def _admin_response(admin: Admin) -> AdminResponse:
    # Adjust fields based on your actual AdminResponse schema
    return AdminResponse(
        adminId=admin.admin_id,
        email=admin.email,
        staffRole=admin.staff_role,
        createdAt=admin.created_at
    )

def _vendor_response(vendor: Vendor) -> VendorAdminView:
    # Adjust fields based on your actual VendorAdminView schema
    return VendorAdminView(
        vendorId=vendor.vendor_id,
        businessName=vendor.business_name,
        email=vendor.email,
        approvalStatus=vendor.approval_status,
        status=vendor.status, # Stop hacking this. Fix your DB model if this is missing.
        isVerified=vendor.is_verified,
        approvedAt=vendor.approved_at
    )

# --- Auth Routes ---

@auth_admin_router.post("/register", response_model=AdminResponse, status_code=status.HTTP_201_CREATED)
def register_admin(payload: AdminRegister, db: Session = Depends(get_db)):
    """Provision admin account (internal)."""
    admin = auth_admin_service.register_admin(
        db, 
        email=payload.email, 
        password=payload.password, 
        staff_role=payload.staff_role
    )
    return _admin_response(admin)

@auth_admin_router.post("/login")
def admin_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Admin login."""
    return auth_admin_service.login_admin(db, form_data.username, form_data.password)

# --- Admin Vendor Routes ---

@router.get("/vendors", response_model=list[VendorAdminView])
def list_vendors(
    approval_status: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    """List all vendors."""
    vendors = admin_service.list_vendors(db, approval_status=approval_status, status=status)
    return [_vendor_response(v) for v in vendors]

@router.get("/vendors/{vendor_id}", response_model=VendorAdminView)
def get_vendor_detail(
    vendor_id: int,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    """Get vendor detail."""
    vendor = admin_service.get_vendor(db, vendor_id=vendor_id)
    return _vendor_response(vendor)

@router.put("/vendors/{vendor_id}/status", response_model=VendorAdminView)
def update_vendor_status(
    vendor_id: int,
    body: dict,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    """Update vendor account status."""
    vendor = admin_service.update_vendor_status(
        db, 
        vendor_id=vendor_id, 
        new_status=body.get("status"), 
        admin_email=current_admin.email
    )
    return _vendor_response(vendor)

@router.post("/vendors/{vendor_id}/approve", response_model=VendorAdminView)
def approve_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    """Approve vendor registration."""
    vendor = admin_service.approve_vendor(db, vendor_id=vendor_id, admin_email=current_admin.email)
    return _vendor_response(vendor)

@router.post("/vendors/{vendor_id}/reject", response_model=VendorAdminView)
def reject_vendor(
    vendor_id: int,
    body: VendorRejectRequest,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    """Reject vendor registration."""
    vendor = admin_service.reject_vendor(db, vendor_id=vendor_id, reason=body.reason, admin_email=current_admin.email)
    return _vendor_response(vendor)