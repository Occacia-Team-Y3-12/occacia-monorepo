from datetime import timedelta

import jwt
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import PyJWTError as JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import ALGORITHM, SECRET_KEY, create_access_token, verify_password
from app.schemas.auth_schema import (
    CustomerRegister,
    RegisterResponse,
    VerifyEmailResponse,
    ForgotPasswordRequest,   # New for UC-07
    ResetPasswordRequest,    # New for UC-07
    AuthMessageResponse      # New for UC-07
)
from app.schemas.vendor_schema import VendorRegisterRequest, VendorResponse
from app.services.auth_service import auth_service
from app.services.vendor_service import vendor_service

router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/vendors/login")


def get_current_vendor(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str | None = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    vendor = vendor_service.get_vendor_by_email(db, email=email)
    if vendor is None:
        raise credentials_exception
    return vendor

# ==========================================
# 🚀 REGISTRATION & VERIFICATION ROUTES
# ==========================================

@router.post(
    "/vendors/register",
    response_model=VendorResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_vendor(vendor_data: VendorRegisterRequest, db: Session = Depends(get_db)):
    if vendor_service.get_vendor_by_email(db, email=vendor_data.email):
        raise HTTPException(status_code=400, detail="This email is already taken!")
    if vendor_service.get_vendor_by_display_name(db, name=vendor_data.business_name):
        raise HTTPException(status_code=400, detail="Business name already in use!")
    vendor = vendor_service.create_vendor(db, vendor_data)
    auth_service.register_vendor_verification(vendor.email)
    return vendor


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
@router.post(
    "/customers/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_customer(payload: CustomerRegister, db: Session = Depends(get_db)):
    return auth_service.register_customer(db, payload)


@router.get(
    "/customers/verify-email",
    response_model=VerifyEmailResponse,
    status_code=status.HTTP_200_OK,
)
def verify_customer_email(token: str = Query(...), db: Session = Depends(get_db)):
    return auth_service.verify_customer_email(db, token)


@router.get(
    "/vendors/verify-email",
    response_model=VerifyEmailResponse,
    status_code=status.HTTP_200_OK,
)
def verify_vendor_email(token: str = Query(...), db: Session = Depends(get_db)):
    return auth_service.verify_vendor_email(db, token)


# ==========================================
# 🔑 LOGIN ROUTES
# ==========================================

@router.post("/vendors/login")
def login_vendor(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    vendor = vendor_service.get_vendor_by_email(db, email=form_data.username)
    if not vendor or not verify_password(form_data.password, vendor.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": vendor.email}, expires_delta=timedelta(minutes=60)
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/vendors/me", response_model=VendorResponse)
def read_current_vendor(current_vendor=Depends(get_current_vendor)):
    return current_vendor


# ==========================================
# 🔐 PASSWORD RESET ROUTES (UC-07)
# ==========================================

@router.post(
    "/forgot-password", 
    response_model=AuthMessageResponse, 
    status_code=status.HTTP_200_OK
)
async def forgot_password(
    request: ForgotPasswordRequest, 
    db: Session = Depends(get_db)
):
    """
    Triggers the password reset flow. 
    Generates a secure, time-limited JWT and logs it (mocking email).
    """
    return auth_service.request_password_reset(db, request)


@router.post(
    "/reset-password", 
    response_model=AuthMessageResponse, 
    status_code=status.HTTP_200_OK
)
async def reset_password(
    request: ResetPasswordRequest, 
    db: Session = Depends(get_db)
):
    """
    Validates the reset token and updates the customer's password.
    """
    return auth_service.confirm_password_reset(db, request)