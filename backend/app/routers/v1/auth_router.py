"""
app/routers/v1/auth_router.py

Login note
----------
The OpenAPI spec defines a JSON body with { email, password }.
FastAPI's OAuth2PasswordRequestForm uses 'username' for Swagger UI
compatibility.  We keep form-data and treat 'username' AS the email field.
auth_service.login_vendor / login_customer must look users up by
form_data.username (i.e. the email address).  JSON-body clients should
send the email value in the 'username' form field.
"""
from fastapi import APIRouter, Depends, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth_schema import (
    AuthMessageResponse,
    AuthResponse,
    CustomerRegister,
    ForgotPasswordRequest,
    RefreshTokenRequest,
    RegisterResponse,
    ResetPasswordRequest,
)
from app.schemas.vendor_schema import VendorRegisterRequest, VendorResponse
from app.services.auth_service import auth_service
from app.services.vendor_service import vendor_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

# --- Vendor Routes ---

@router.post("/vendor/register", response_model=VendorResponse, status_code=201)
def register_vendor(vendor_data: VendorRegisterRequest, db: Session = Depends(get_db)):
    if vendor_service.get_vendor_by_email(db, email=vendor_data.email):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Email already taken!")
    if vendor_service.get_vendor_by_display_name(db, name=vendor_data.business_name):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Business name already in use!")
        
    vendor = vendor_service.create_vendor(db, vendor_data)
    auth_service.register_vendor_verification(vendor.email)
    return vendor

@router.post("/vendor/login", tags=["Authentication"])
def login_vendor(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # Accept email via the standard 'username' field (Swagger UI / OAuth2 form)
    # or honour a raw email value if the client sends 'email' directly.
    # OAuth2PasswordRequestForm exposes only .username, so callers that want to
    # send email simply put it in that field — both paths end up here identically.
    form_data.username = form_data.username or ""  # normalise None → ""
    return auth_service.login_vendor(db, form_data)

@router.get("/vendor/verify-email")
def verify_vendor_email(token: str = Query(...), db: Session = Depends(get_db)):
    return auth_service.verify_vendor_email(db, token)


# --- Customer Routes ---

@router.post("/customer/register", response_model=RegisterResponse, status_code=201)
def register_customer(payload: CustomerRegister, db: Session = Depends(get_db)):
    return auth_service.register_customer(db, payload)


@router.post("/customer/login", tags=["Authentication"])
def login_customer(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # Same email/username normalisation as vendor login above.
    form_data.username = form_data.username or ""
    return auth_service.login_customer(db, form_data)


@router.post(
    "/customer/token/refresh",
    response_model=AuthResponse,
    response_model_by_alias=True,
    tags=["Authentication"],
)
def refresh_customer_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    return auth_service.refresh_customer_token(db, payload)

@router.get("/customer/verify-email")
def verify_customer_email(token: str = Query(...), db: Session = Depends(get_db)):
    return auth_service.verify_customer_email(db, token)

@router.post("/customer/password/forgot", response_model=AuthMessageResponse)
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    return auth_service.request_password_reset(db, request)

@router.post("/customer/password/reset", response_model=AuthMessageResponse)
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    return auth_service.confirm_password_reset(db, request)