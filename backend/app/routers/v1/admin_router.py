"""
app/routers/v1/admin_router.py

Admin endpoints:
  POST /admin/register               — create first admin (lock with DISABLE_ADMIN_REGISTER=true)
  POST /admin/login                  — returns JWT
  GET  /admin/vendors/pending        — vendors awaiting approval
  GET  /admin/vendors                — all vendors (?status_filter=PENDING|APPROVED|REJECTED)
  GET  /admin/vendors/{id}           — vendor detail
  POST /admin/vendors/{id}/approve   — approve → is_verified=True → sends email
  POST /admin/vendors/{id}/reject    — reject with reason → sends email
  GET  /admin/packages               — all packages (?vendor_id=X)
  DELETE /admin/packages/{id}        — remove any package
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
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/admin/login")

ADMIN_TOKEN_EXPIRE_MINUTES = 120


# ── Admin JWT ────────────────────────────────────────────────────────

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


# ── Email helpers ────────────────────────────────────────────────────

def _send_approval_email(vendor: Vendor):
    subject = "🎉 Your Occacia vendor account has been approved!"
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:24px;">
        <h2 style="color:#2d3748;">Congratulations, {vendor.display_name or vendor.business_name}! 🎉</h2>
        <p style="color:#4a5568;">
            Your vendor application for <strong>{vendor.business_name}</strong> has been
            <strong style="color:#38a169;">approved</strong>.
            You can now log in and start listing your packages on Occacia.
        </p>
        <div style="background:#f0fff4;border-left:4px solid #38a169;padding:16px;margin:24px 0;border-radius:4px;">
            <p style="color:#276749;margin:0;">
                <strong>Vendor ID:</strong> {vendor.vendor_id}<br>
                <strong>Business:</strong> {vendor.business_name}
            </p>
        </div>
        <p style="color:#718096;font-size:14px;">Welcome to the Occacia vendor network!</p>
    </div>"""
    _send_email(vendor.email, subject, html)


def _send_rejection_email(vendor: Vendor, reason: str):
    subject = "Update on your Occacia vendor application"
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:24px;">
        <h2 style="color:#2d3748;">Application Update</h2>
        <p style="color:#4a5568;">
            Hi {vendor.display_name or vendor.business_name},<br><br>
            After reviewing your application for <strong>{vendor.business_name}</strong>,
            we are unable to approve it at this time.
        </p>
        <div style="background:#fff5f5;border-left:4px solid #e53e3e;padding:16px;margin:24px 0;border-radius:4px;">
            <p style="color:#742a2a;margin:0;"><strong>Reason:</strong> {reason}</p>
        </div>
        <p style="color:#718096;font-size:14px;">Contact support if you believe this is an error.</p>
    </div>"""
    _send_email(vendor.email, subject, html)


# ── Registration ──────────────────────────────────────────────────────

@router.post("/register", response_model=AdminResponse, status_code=201)
def register_admin(payload: AdminRegister, db: Session = Depends(get_db)):
    """
    Create an admin account. Set DISABLE_ADMIN_REGISTER=true in .env after
    creating your first admin to lock this endpoint.
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
    logger.info(f"🔐 New admin created: {admin.email} ({admin.staff_role})")
    return admin


# ── Login ─────────────────────────────────────────────────────────────

@router.post("/login")
def admin_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    admin = db.query(Admin).filter(Admin.email == form_data.username).first()
    if not admin or not verify_password(form_data.password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    token = _create_admin_token(admin.admin_id)
    logger.info(f"🔐 Admin login: {admin.email}")
    return {"access_token": token, "token_type": "bearer", "role": admin.staff_role}


# ── Vendor management ─────────────────────────────────────────────────

@router.get("/vendors/pending", response_model=list[VendorAdminView])
def list_pending_vendors(
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    """Email-verified vendors waiting for admin approval."""
    return (
        db.query(Vendor)
        .filter(Vendor.approval_status == "PENDING", Vendor.is_verified == True)
        .order_by(Vendor.id.desc())
        .all()
    )


@router.get("/vendors", response_model=list[VendorAdminView])
def list_all_vendors(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    """All vendors. Use ?status_filter=PENDING|APPROVED|REJECTED to filter."""
    query = db.query(Vendor)
    if status_filter:
        query = query.filter(Vendor.approval_status == status_filter.upper())
    return query.order_by(Vendor.id.desc()).all()


@router.get("/vendors/{vendor_id}", response_model=VendorAdminView)
def get_vendor_detail(
    vendor_id: int,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found.")
    return vendor


@router.post("/vendors/{vendor_id}/approve", response_model=VendorAdminView)
def approve_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
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
    logger.info(f"✅ Admin {current_admin.email} approved vendor {vendor.vendor_id}")
    return vendor


@router.post("/vendors/{vendor_id}/reject", response_model=VendorAdminView)
def reject_vendor(
    vendor_id: int,
    body: VendorRejectRequest = VendorRejectRequest(),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
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
    logger.info(f"❌ Admin {current_admin.email} rejected vendor {vendor.vendor_id}")
    return vendor


# ── Package oversight ─────────────────────────────────────────────────

@router.get("/packages", response_model=list[PackageResponse])
def list_all_packages(
    vendor_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    """All packages. Filter with ?vendor_id=X"""
    query = db.query(Package)
    if vendor_id:
        query = query.filter(Package.vendor_id == vendor_id)
    return query.order_by(Package.id.desc()).all()


@router.delete("/packages/{package_id}", status_code=204)
def admin_delete_package(
    package_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    pkg = db.query(Package).filter(Package.id == package_id).first()
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found.")
    db.delete(pkg)
    db.commit()
    logger.info(f"🗑️ Admin {current_admin.email} deleted package {package_id}")