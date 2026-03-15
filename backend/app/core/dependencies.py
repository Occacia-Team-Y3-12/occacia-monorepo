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
from app.core.security import ALGORITHM, SECRET_KEY
from app.models.customer import Customer
from app.models.vendor import Vendor
from app.models.admin import Admin

# --- Security Schemes ---
# Singular paths so the FastAPI Swagger UI 'Authorize' button works properly
oauth2_customer_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/customer/login", scheme_name="CustomerAuth")
oauth2_vendor_scheme   = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/vendor/login",   scheme_name="VendorAuth")
oauth2_admin_scheme    = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/admin/login",    scheme_name="AdminAuth")

## ================================= CUSTOMER DEPENDENCY ==========================================##
def get_current_customer(
    token: str = Depends(oauth2_customer_scheme),
    db: Session = Depends(get_db)
) -> Customer:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token. Please log in.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    customer = db.query(Customer).filter(Customer.email == email).first()
    if customer is None:
        raise credentials_exception

    # Enforce email verification (unless disabled for CI/CD test bots)
    if os.getenv("SKIP_EMAIL_VERIFICATION") != "true" and not customer.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email first."
        )

    return customer

## ================================= VENDOR DEPENDENCY ==========================================##
def get_current_vendor(
    token: str = Depends(oauth2_vendor_scheme), 
    db: Session = Depends(get_db)
) -> Vendor:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, 
        detail="Invalid or expired vendor token.",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    vendor = db.query(Vendor).filter(Vendor.email == email).first()
    if vendor is None:
        raise credentials_exception
        
    return vendor

## ================================= ADMIN DEPENDENCY ==========================================##
def get_current_admin(
    token: str = Depends(oauth2_admin_scheme), 
    db: Session = Depends(get_db)
) -> Admin:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, 
        detail="Invalid or expired admin token.",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "admin":
            raise credentials_exception
            
        admin_id = payload.get("sub")
        if admin_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    admin = db.query(Admin).filter(Admin.admin_id == admin_id).first()
    if admin is None:
        raise credentials_exception
        
    return admin