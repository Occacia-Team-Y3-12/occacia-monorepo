import os
from datetime import timedelta

import jwt
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import PyJWTError as JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.models.customer import Customer
from app.schemas.auth_schema import (
    AuthMessageResponse,
    AuthResponse,
    CustomerRegister,
    ForgotPasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterResponse,
    ResetPasswordRequest,
    VerifyEmailResponse,
)
from app.schemas.vendor_schema import VendorRegisterRequest, VendorResponse
from app.services.auth_service import auth_service
from app.services.customer_service import customer_service
from app.services.vendor_service import vendor_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_vendor_scheme   = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/vendor/login",    scheme_name="VendorAuth")
oauth2_customer_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/customer/login",  scheme_name="CustomerAuth")
oauth2_admin_scheme    = OAuth2PasswordBearer(tokenUrl="/api/v1/admin/login",          scheme_name="AdminAuth")
oauth2_scheme = oauth2_vendor_scheme


# --- Dependency Injectors ---

def get_current_vendor(
    token: str = Depends(oauth2_vendor_scheme), db: Session = Depends(get_db)
):
    exc = HTTPException(status_code=401, detail="Could not validate vendor credentials",
                        headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise exc
    except JWTError:
        raise exc
    vendor = vendor_service.get_vendor_by_email(db, email=email)
    if not vendor:
        raise exc
    return vendor

def get_current_customer(
    token: str = Depends(oauth2_customer_scheme), db: Session = Depends(get_db)
):
    exc = HTTPException(status_code=401, detail="Could not validate customer credentials",
                        headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise exc
    except JWTError:
        raise exc
    customer = customer_service.get_customer_by_email(db, email=email)
    if not customer:
        raise exc
    return customer

def get_current_admin(
    token: str = Depends(oauth2_admin_scheme), db: Session = Depends(get_db)
):
    from app.models.admin import Admin
    exc = HTTPException(status_code=401, detail="Could not validate admin credentials",
                        headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise exc
    except JWTError:
        raise exc
    admin = db.query(Admin).filter(Admin.email == email).first()
    if not admin:
        raise exc
    return admin


# --- Login Verification Helpers ---

def verify_user_login(user, form_data: OAuth2PasswordRequestForm):
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password",
                            headers={"WWW-Authenticate": "Bearer"})
    password = getattr(user, 'password_hash', None) or getattr(user, 'hashed_password', None)
    if not password or not verify_password(form_data.password, password):
        raise HTTPException(status_code=401, detail="Incorrect email or password",
                            headers={"WWW-Authenticate": "Bearer"})
    if os.getenv("SKIP_EMAIL_VERIFICATION") != "true":
        if not getattr(user, 'email_verified', True) and not getattr(user, 'is_verified', True):
            raise HTTPException(status_code=403, detail="Email not verified.")

def verify_customer_login(customer: Customer, password: str):
    if not customer:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not customer.password_hash or not verify_password(password, customer.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if os.getenv("SKIP_EMAIL_VERIFICATION") != "true" and not customer.email_verified:
        raise HTTPException(status_code=403, detail="Email not verified.")
    if customer.status != "ACTIVE":
        raise HTTPException(status_code=403, detail="Customer account is not active.")

def build_customer_auth_response(customer: Customer) -> AuthResponse:
    access_token = create_access_token(
        data={"sub": customer.email, "role": "CUSTOMER"},
        expires_delta=timedelta(minutes=60),
    )
    refresh_token = create_refresh_token(
        data={"sub": customer.email, "role": "CUSTOMER"},
        expires_delta=timedelta(days=7),
    )
    return AuthResponse(
        accessToken=access_token,
        refreshToken=refresh_token,
        user={
            "userId": customer.customer_id,
            "email": customer.email,
            "role": "CUSTOMER",
            "status": customer.status,
        },
    )


# --- Vendor Routes ---

@router.post("/vendor/register", response_model=VendorResponse, status_code=201)
def register_vendor(vendor_data: VendorRegisterRequest, db: Session = Depends(get_db)):
    if vendor_service.get_vendor_by_email(db, email=vendor_data.email):
        raise HTTPException(status_code=400, detail="Email already taken!")
    if vendor_service.get_vendor_by_display_name(db, name=vendor_data.business_name):
        raise HTTPException(status_code=400, detail="Business name already in use!")
    vendor = vendor_service.create_vendor(db, vendor_data)
    auth_service.register_vendor_verification(vendor.email)
    return vendor

@router.post("/vendor/login", tags=["Authentication"])
def login_vendor(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    vendor = vendor_service.get_vendor_by_email(db, email=form_data.username)
    verify_user_login(vendor, form_data)
    token = create_access_token(data={"sub": vendor.email}, expires_delta=timedelta(minutes=60))
    return {"access_token": token, "token_type": "bearer"}

@router.get("/vendor/verify-email")
def verify_vendor_email(token: str = Query(...), db: Session = Depends(get_db)):
    try:
        auth_service.verify_vendor_email(db, token)
        return {"message": "Email verified successfully"}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid verification token.")


# --- Customer Routes ---

@router.post("/customer/register", response_model=RegisterResponse, status_code=201)
def register_customer(payload: CustomerRegister, db: Session = Depends(get_db)):
    return auth_service.register_customer(db, payload)

@router.post("/customer/login", response_model=AuthResponse, response_model_by_alias=True, tags=["Authentication"])
def login_customer(payload: LoginRequest, db: Session = Depends(get_db)):
    customer = customer_service.get_customer_by_email(db, email=str(payload.email))
    verify_customer_login(customer, payload.password)
    return build_customer_auth_response(customer)

@router.get("/customer/verify-email")
def verify_customer_email(token: str = Query(...), db: Session = Depends(get_db)):
    try:
        result = auth_service.verify_customer_email(db, token)
        msg = result.get("message", "Email verified successfully") if isinstance(result, dict) else "Email verified successfully"
        return {"message": msg}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid verification token.")

@router.post("/customer/password/forgot", response_model=AuthMessageResponse)
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    return auth_service.request_password_reset(db, request)

@router.post("/customer/password/reset", response_model=AuthMessageResponse)
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    return auth_service.confirm_password_reset(db, request)

@router.post(
    "/customer/token/refresh",
    response_model=AuthResponse,
    response_model_by_alias=True,
    tags=["Authentication"],
)
def refresh_customer_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    exc = HTTPException(status_code=401, detail="Invalid or expired refresh token.")
    try:
        claims = decode_token(payload.refresh_token)
    except JWTError:
        raise exc

    if claims.get("type") != "refresh" or claims.get("role") != "CUSTOMER":
        raise exc

    email = claims.get("sub")
    if not email:
        raise exc

    customer = customer_service.get_customer_by_email(db, email=email)
    if not customer or customer.status != "ACTIVE":
        raise exc
    if os.getenv("SKIP_EMAIL_VERIFICATION") != "true" and not customer.email_verified:
        raise exc

    return build_customer_auth_response(customer)