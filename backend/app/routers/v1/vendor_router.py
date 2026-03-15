"""
app/routers/v1/vendor_router.py

Vendor self-service endpoints (requires vendor JWT).
"""
from __future__ import annotations

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
# DELETED duplicate auth logic. We import the central vault guard.
from app.core.dependencies import get_current_vendor
from app.models.vendor import Vendor
from app.schemas.vendor_schema import VendorResponse, VendorUpdate
from app.schemas.package_schema import PackageCreate, PackageUpdate, PackageResponse
from app.services.vendor_service import vendor_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/vendors", tags=["Vendors"])

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
