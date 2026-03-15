"""
app/routers/v1/vendor_router.py

Vendor self-service endpoints (requires vendor JWT).
"""
from __future__ import annotations

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_admin, get_current_vendor
from app.models.admin import Admin
from app.models.vendor import Vendor
from app.schemas.admin_schema import VendorAdminView
from app.schemas.package_schema import PackageCreate, PackageUpdate, PackageResponse
from app.schemas.vendor_schema import VendorResponse, VendorUpdate
from app.services.vendor_service import AdminVendorService, vendor_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/vendors", tags=["Vendors"])
admin_router = APIRouter(prefix="/admin", tags=["Admin"])

# --- Local Guardrail ---


def require_approved_vendor(vendor: Vendor = Depends(get_current_vendor)) -> Vendor:
    """Blocks any action if vendor is not approved by admin."""
    if vendor.approval_status != "APPROVED":
        status_msg = {
            "PENDING": "Your account is pending admin approval. You will be notified by email once approved.",
            "REJECTED": "Your vendor application was not approved. Please contact support.",
        }.get(vendor.approval_status, "Your account is not active.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=status_msg)
    return vendor


def get_vendor_service(db: Session = Depends(get_db)):
    return AdminVendorService(db)


@admin_router.get("/vendors", response_model=list[VendorAdminView])
async def list_vendors(
    approval_status: str | None = Query(default=None),
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
    vendor_service: AdminVendorService = Depends(get_vendor_service)
):
    """List all vendors."""
    return vendor_service.list_vendors(
        approval_status=approval_status,
        status=status,
    )


@admin_router.get("/vendors/{vendor_id}", response_model=VendorAdminView)
async def get_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
    vendor_service: AdminVendorService = Depends(get_vendor_service)
):
    """Get vendor detail."""
    return vendor_service.get_vendor(vendor_id=vendor_id)


@admin_router.put("/vendors/{vendor_id}/status", response_model=VendorAdminView)
async def update_vendor_status(
    vendor_id: int,
    body: dict,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
    vendor_service: AdminVendorService = Depends(get_vendor_service)
):
    """Update vendor account status."""
    status_val = body.get("status") or ""
    return vendor_service.update_vendor_status(
        vendor_id=vendor_id,
        new_status=status_val,
        admin_email=current_admin.email,
    )


@admin_router.get("/vendors/stats/pending")
async def get_vendor_pending_stats(
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
    vendor_service: AdminVendorService = Depends(get_vendor_service)
):
    """
    Get counts of pending vendors and organizations.
    """
    return vendor_service.get_pending_counts()


# --- Profile Routes ---

@router.get("/me", response_model=VendorResponse)
def get_my_profile(vendor: Vendor = Depends(get_current_vendor)):
    """Get current vendor profile."""
    return vendor


@router.put("/me", response_model=VendorResponse)
def update_my_profile(
    body: VendorUpdate,
    vendor: Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db),
):
    """Update current vendor profile."""
    # Add by_alias=True to the model_dump call
    return vendor_service.update_profile(db, vendor, body.model_dump(exclude_unset=True, by_alias=True))


# --- Packages Routes ---

@router.get("/me/packages", response_model=List[PackageResponse])
def list_my_packages(
    vendor: Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db),
):
    """Any logged-in vendor can view their own packages."""
    return vendor_service.get_packages_by_vendor(db, vendor.id)


@router.post("/me/packages", response_model=PackageResponse, status_code=status.HTTP_201_CREATED)
def create_package(
    payload: PackageCreate,
    vendor: Vendor = Depends(require_approved_vendor),
    db: Session = Depends(get_db),
):
    """Only APPROVED vendors can create packages."""
    # Service expects the Pydantic object based on original code, so we pass 'payload'
    return vendor_service.create_package(db, vendor.id, payload)


@router.put("/me/packages/{package_id}", response_model=PackageResponse)
def update_package(
    package_id: int,
    payload: PackageUpdate,
    vendor: Vendor = Depends(require_approved_vendor),
    db: Session = Depends(get_db),
):
    """Only APPROVED vendors can update their own packages."""
    # SECURE: vendor.id is now strictly enforced in the service layer
    pkg = vendor_service.update_package(db, package_id, payload, vendor.id)
    if not pkg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Package not found or unauthorized.")
    return pkg


@router.delete("/me/packages/{package_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_package(
    package_id: int,
    vendor: Vendor = Depends(require_approved_vendor),
    db: Session = Depends(get_db),
):
    """Only APPROVED vendors can delete their own packages."""
    # SECURE: vendor.id is now strictly enforced in the service layer
    success = vendor_service.delete_package(db, package_id, vendor.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Package not found or unauthorized.")
    return None
