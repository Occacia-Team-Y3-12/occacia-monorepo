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
from types import SimpleNamespace

from fastapi import APIRouter, Depends, Query
from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth_schema import (
    AuthMessageResponse,
    AuthResponse,
    CustomerRegister,
    ForgotPasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterResponse,
    ResendVerificationRequest,
    ResetPasswordRequest,
)
from app.schemas.vendor_schema import VendorRegisterRequest, VendorResponse
from app.services.auth_service import auth_service
from app.services.vendor_service import vendor_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


async def _parse_login_payload(request: Request) -> LoginRequest | SimpleNamespace:
    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        body = await request.json()
        return LoginRequest.model_validate(body)

    form = await request.form()
    username = form.get("username") or form.get("email")
    password = form.get("password")
    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="email/username and password are required.",
        )
    return SimpleNamespace(username=str(username), password=str(password))

# --- Vendor Routes ---
# last two commits belongs to OCA-188

@router.post("/vendor/register", response_model=VendorResponse, status_code=201)
def register_vendor(vendor_data: VendorRegisterRequest, db: Session = Depends(get_db)):
    if vendor_service.get_vendor_by_email(db, email=vendor_data.email):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Email already taken!")
    if vendor_service.get_vendor_by_display_name(db, name=vendor_data.business_name):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Business name already in use!")
        
    vendor = vendor_service.create_vendor(db, vendor_data)
    auth_service.register_vendor_verification(db, vendor)
    return vendor


@router.post("/vendor/login", tags=["Authentication"])
async def login_vendor(request: Request, db: Session = Depends(get_db)):
    payload = await _parse_login_payload(request)
    return auth_service.login_vendor(db, payload)


@router.get("/vendor/verify-email")
def verify_vendor_email(token: str = Query(...), db: Session = Depends(get_db)):
    return auth_service.verify_vendor_email(db, token)



@router.post("/vendor/password/forgot", response_model=AuthMessageResponse, tags=["Authentication"])
def forgot_vendor_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    return auth_service.request_vendor_password_reset(db, request)


@router.post("/vendor/password/reset", response_model=AuthMessageResponse, tags=["Authentication"])
def reset_vendor_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    return auth_service.reset_vendor_password(db, request)


# --- Customer Routes ---

@router.post("/customer/register", response_model=RegisterResponse, status_code=201)
def register_customer(payload: CustomerRegister, db: Session = Depends(get_db)):
    return auth_service.register_customer(db, payload)


@router.post("/customer/login", tags=["Authentication"])
async def login_customer(request: Request, db: Session = Depends(get_db)):
    payload = await _parse_login_payload(request)
    return auth_service.login_customer(db, payload)


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


@router.post("/customer/email-verification/resend", response_model=AuthMessageResponse)
def resend_customer_verification_email(
    payload: ResendVerificationRequest,
    db: Session = Depends(get_db),
):
    return auth_service.resend_customer_verification_email(db, payload)


@router.post("/customer/password/forgot", response_model=AuthMessageResponse)
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    return auth_service.request_password_reset(db, request)


@router.post("/customer/password/reset", response_model=AuthMessageResponse)
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    return auth_service.confirm_password_reset(db, request)
