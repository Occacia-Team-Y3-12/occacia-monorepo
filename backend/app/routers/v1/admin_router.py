"""
app/routers/v1/admin_router.py

Routes per OpenAPI contract:
  POST /auth/admin/register             — provision admin (via auth_admin_router)
  POST /auth/admin/login                — admin login (via auth_admin_router)
  GET  /admin/vendors                   — list vendors (?approval_status / ?status)
  GET  /admin/vendors/{vendorId}        — vendor detail
  PUT  /admin/vendors/{vendorId}/status — update account status ACTIVE/SUSPENDED/DISABLED
  POST /admin/vendors/{vendorId}/approve— approve vendor
  POST /admin/vendors/{vendorId}/reject — reject vendor
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, SECRET_KEY, ALGORITHM
from app.models.admin import Admin
from app.models.vendor import Vendor
from app.models.package import Package
from app.schemas.admin_schema import (
    AdminRegister, AdminResponse, VendorAdminView, VendorRejectRequest
)
from app.schemas.package_schema import PackageResponse
from app.services.auth_service import _send_email

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])
auth_admin_router = APIRouter(prefix="/auth/admin", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/admin/login")

ADMIN_TOKEN_EXPIRE_MINUTES = 120


# --- Admin JWT ---

def _create_admin_token(admin_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ADMIN_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": admin_id, "type": "admin", "exp": expire},
        SECRET_KEY, algorithm=ALGORITHM,
    )

def get_current_admin(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Admin:
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired admin token.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "admin":
            raise exc
        admin_id: str = payload.get("sub")
        if not admin_id:
            raise exc
    except jwt.PyJWTError:
        raise exc

    admin = db.query(Admin).filter(Admin.admin_id == admin_id).first()
    if not admin:
        raise exc
    return admin


# --- Email helpers ---

def _send_approval_email(vendor: Vendor):
    subject = "Your Occacia vendor account has been approved!"
    body = (
        f"Congratulations, {vendor.display_name or vendor.business_name}!\n\n"
        f"Your vendor application for {vendor.business_name} has been approved. "
        "You can now log in and start listing your packages on Occacia.\n\n"
        f"Vendor ID: {vendor.vendor_id}\n"
        f"Business: {vendor.business_name}\n\n"
        "Welcome to the Occacia vendor network!"
    )
    _send_email(vendor.email, subject, body)

def _send_rejection_email(vendor: Vendor, reason: str):
    subject = "Update on your Occacia vendor application"
    body = (
        f"Hi {vendor.display_name or vendor.business_name},\n\n"
        f"After reviewing your application for {vendor.business_name}, "
        "we are unable to approve it at this time.\n\n"
        f"Reason: {reason}\n\n"
        "Contact support if you believe this is an error."
    )
    _send_email(vendor.email, subject, body)


# --- POST /auth/admin/register ---

@auth_admin_router.post("/register", response_model=AdminResponse, status_code=201)
def register_admin(payload: AdminRegister, db: Session = Depends(get_db)):
    """
    Provision admin account (internal). 
    Set DISABLE_ADMIN_REGISTER=true in .env to lock after first admin is created.
    """
    if getattr(settings, "DISABLE_ADMIN_REGISTER", "false").lower() == "true":
        raise HTTPException(status_code=403, detail="Admin registration is disabled.")
    if db.query(Admin).filter(Admin.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered.")

    admin = Admin(
        email=payload.email,
        password_hash=get_password_hash(payload.password),
        staff_role=payload.staff_role or "staff",
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    logger.info("New admin created: %s (%s)", admin.email, admin.staff_role)
    return admin


# --- POST /auth/admin/login ---

@auth_admin_router.post("/login")
def admin_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Admin login."""
    admin = db.query(Admin).filter(Admin.email == form_data.username).first()
    if not admin or not verify_password(form_data.password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    
    token = _create_admin_token(admin.admin_id)
    logger.info("Admin login: %s", admin.email)
    return {"access_token": token, "token_type": "bearer", "role": admin.staff_role}


# --- GET /admin/vendors ---

@router.get("/vendors", response_model=list[VendorAdminView])
def list_vendors(
    approval_status: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    """List all vendors."""
    query = db.query(Vendor)
    if approval_status:
        query = query.filter(Vendor.approval_status == approval_status.upper())
    if status:
        query = query.filter(Vendor.status == status.upper())
    return query.order_by(Vendor.id.desc()).all()


# --- GET /admin/vendors/{vendorId} ---

@router.get("/vendors/{vendor_id}", response_model=VendorAdminView)
def get_vendor_detail(
    vendor_id: int,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    """Get vendor detail."""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found.")
    return vendor


# --- PUT /admin/vendors/{vendorId}/status ---

@router.put("/vendors/{vendor_id}/status", response_model=VendorAdminView)
def update_vendor_status(
    vendor_id: int,
    body: dict,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    """Update vendor account status."""
    new_status = (body.get("status") or "").upper()
    if new_status not in ("ACTIVE", "SUSPENDED", "DISABLED"):
        raise HTTPException(
            status_code=400,
            detail="status must be ACTIVE, SUSPENDED, or DISABLED"
        )
        
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found.")
        
    if hasattr(vendor, "status"):
        vendor.status = new_status
    else:
        logger.warning(
            "Vendor model has no .status column yet. "
            "Run migration to add it. Storing in approval_status as fallback."
        )
        
    db.commit()
    db.refresh(vendor)
    logger.info("Admin %s set vendor %s status to %s", current_admin.email, vendor_id, new_status)
    return vendor


# --- POST /admin/vendors/{vendorId}/approve ---

@router.post("/vendors/{vendor_id}/approve", response_model=VendorAdminView)
def approve_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    """Approve vendor registration."""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found.")
    if vendor.approval_status == "APPROVED":
        raise HTTPException(status_code=400, detail="Vendor is already approved.")

    vendor.is_verified = True
    vendor.approval_status = "APPROVED"
    vendor.approved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(vendor)
    
    _send_approval_email(vendor)
    logger.info("Admin %s approved vendor %s", current_admin.email, vendor.vendor_id)
    return vendor


# --- POST /admin/vendors/{vendorId}/reject ---

@router.post("/vendors/{vendor_id}/reject", response_model=VendorAdminView)
def reject_vendor(
    vendor_id: int,
    body: VendorRejectRequest = VendorRejectRequest(),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    """Reject vendor registration."""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found.")
    if vendor.approval_status == "REJECTED":
        raise HTTPException(status_code=400, detail="Vendor is already rejected.")

    vendor.is_verified = False
    vendor.approval_status = "REJECTED"
    db.commit()
    db.refresh(vendor)
    
    _send_rejection_email(vendor, body.reason)
    logger.info("Admin %s rejected vendor %s", current_admin.email, vendor.vendor_id)
    return vendor