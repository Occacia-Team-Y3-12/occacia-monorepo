"""
app/core/dependencies.py
Global security dependencies and token validation.
"""
import os

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import PyJWTError as JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db
import app.core.security as _security   # module-level import for unified decoding
from app.models.admin import Admin
from app.models.customer import Customer
from app.models.vendor import Vendor

# ── OAuth2 schemes ────────────────────────────────────────────────────────────
# Singular paths so the FastAPI Swagger UI 'Authorize' button works properly
oauth2_customer_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/customer/login", scheme_name="CustomerAuth"
)
oauth2_vendor_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/vendor/login", scheme_name="VendorAuth"
)
oauth2_admin_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/admin/login", scheme_name="AdminAuth"
)


# ── Customer dependency ───────────────────────────────────────────────────────

def get_current_customer(
    token: str = Depends(oauth2_customer_scheme),
    db: Session = Depends(get_db),
) -> Customer:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token. Please log in.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = _security.decode_token(token)
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # [E05] Reject blacklisted (logged-out) tokens
    # Called via _security.is_token_blacklisted so test patches on
    # app.core.security.is_token_blacklisted are visible at call time.
    if _security.is_token_blacklisted(token):
        raise credentials_exception

    customer = db.query(Customer).filter(Customer.email == email).first()
    if customer is None:
        raise credentials_exception

    # Enforce email verification (unless disabled for CI/CD test bots)
    if os.getenv("SKIP_EMAIL_VERIFICATION") != "true" and not customer.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email first.",
        )
    return customer


# ── Vendor dependency ─────────────────────────────────────────────────────────

def get_current_vendor(
    token: str = Depends(oauth2_vendor_scheme),
    db: Session = Depends(get_db),
) -> Vendor:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired vendor token.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = _security.decode_token(token)
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # [E06] Reject blacklisted (logged-out) tokens
    if _security.is_token_blacklisted(token):
        raise credentials_exception

    vendor = db.query(Vendor).filter(Vendor.email == email).first()
    if vendor is None:
        raise credentials_exception
    return vendor


# ── Admin dependency ──────────────────────────────────────────────────────────

def get_current_admin(
    token: str = Depends(oauth2_admin_scheme),
    db: Session = Depends(get_db),
) -> Admin:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired admin token.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = _security.decode_token(token)
        if payload.get("type") != "admin":
            raise credentials_exception
        admin_id = payload.get("sub")
        if admin_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Reject blacklisted (logged-out) admin tokens
    if _security.is_token_blacklisted(token):
        raise credentials_exception

    admin = db.query(Admin).filter(Admin.admin_id == admin_id).first()
    if admin is None:
        raise credentials_exception
    return admin
