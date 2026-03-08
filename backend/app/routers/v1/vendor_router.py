"""
app/routers/v1/vendor_router.py

Vendor self-service endpoints (requires vendor JWT):
  GET    /vendors/me                    — own profile
  GET    /vendors/me/packages           — own packages
  POST   /vendors/me/packages           — create package (blocked if not APPROVED)
  PUT    /vendors/me/packages/{id}      — update own package
  DELETE /vendors/me/packages/{id}      — delete own package
"""
from __future__ import annotations

import logging
from typing import List

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import SECRET_KEY, ALGORITHM
from app.models.vendor import Vendor
from app.models.package import Package
from app.schemas.vendor_schema import VendorResponse
from app.schemas.package_schema import PackageCreate, PackageUpdate, PackageResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/vendors", tags=["Vendors"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/vendors/login")


# ── Auth dependency ──────────────────────────────────────────────────

def get_current_vendor(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Vendor:
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            raise exc
    except jwt.PyJWTError:
        raise exc

    vendor = db.query(Vendor).filter(Vendor.email == email).first()
    if not vendor:
        raise exc
    return vendor


def require_approved_vendor(vendor: Vendor = Depends(get_current_vendor)) -> Vendor:
    """Blocks any action if vendor is not approved by admin."""
    if vendor.approval_status != "APPROVED":
        status_msg = {
            "PENDING": "Your account is pending admin approval. You will be notified by email once approved.",
            "REJECTED": "Your vendor application was not approved. Please contact support.",
        }.get(vendor.approval_status, "Your account is not active.")
        raise HTTPException(status_code=403, detail=status_msg)
    return vendor


# ── Profile ───────────────────────────────────────────────────────────

@router.get("/me", response_model=VendorResponse)
def get_my_profile(vendor: Vendor = Depends(get_current_vendor)):
    return vendor


# ── Packages ──────────────────────────────────────────────────────────

@router.get("/me/packages", response_model=List[PackageResponse])
def list_my_packages(
    vendor: Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db),
):
    """Any logged-in vendor can view their own packages."""
    return db.query(Package).filter(Package.vendor_id == vendor.id).all()


@router.post("/me/packages", response_model=PackageResponse, status_code=201)
def create_package(
    payload: PackageCreate,
    vendor: Vendor = Depends(require_approved_vendor),
    db: Session = Depends(get_db),
):
    """Only APPROVED vendors can create packages."""
    pkg = Package(
        vendor_id=vendor.id,
        name=payload.name,
        description=payload.description,
        price=payload.price,
        price_per_head=payload.price_per_head,
        min_guests=payload.min_guests,
        max_guests=payload.max_guests,
        tags=payload.tags or [],
        location_coverage=payload.location_coverage,
        blocked_dates=payload.blocked_dates or [],
    )
    db.add(pkg)
    db.commit()
    db.refresh(pkg)
    logger.info(f"📦 Vendor {vendor.vendor_id} created package '{pkg.name}'")
    return pkg


@router.put("/me/packages/{package_id}", response_model=PackageResponse)
def update_package(
    package_id: int,
    payload: PackageUpdate,
    vendor: Vendor = Depends(require_approved_vendor),
    db: Session = Depends(get_db),
):
    pkg = db.query(Package).filter(
        Package.id == package_id, Package.vendor_id == vendor.id
    ).first()
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(pkg, field, value)

    db.commit()
    db.refresh(pkg)
    logger.info(f"✏️ Vendor {vendor.vendor_id} updated package {package_id}")
    return pkg


@router.delete("/me/packages/{package_id}", status_code=204)
def delete_package(
    package_id: int,
    vendor: Vendor = Depends(require_approved_vendor),
    db: Session = Depends(get_db),
):
    pkg = db.query(Package).filter(
        Package.id == package_id, Package.vendor_id == vendor.id
    ).first()
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found.")
    db.delete(pkg)
    db.commit()
    logger.info(f"🗑️ Vendor {vendor.vendor_id} deleted package {package_id}")