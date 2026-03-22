"""
app/routers/v1/auth_router.py
"""
from __future__ import annotations

from types import SimpleNamespace

from fastapi import APIRouter, Depends, Query, Request
from fastapi import HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_customer, get_current_vendor
from app.models.customer import Customer
from app.models.vendor import Vendor
from app.schemas.auth_schema import (
    AuthMessageResponse,
    AuthResponse,
    CustomerRegister,
    LoginRequest,
    RefreshTokenRequest,
    RegisterResponse,
    ResendVerificationRequest,
)
from app.schemas.vendor_schema import VendorRegisterRequest, VendorResponse
from app.services.auth_service import auth_service
from app.services.vendor_service import vendor_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ── Request schemas ───────────────────────────────────────────────────────────

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str


class ResetPasswordRequest(BaseModel):
    """Used after OTP verification — contains the short-lived reset token."""
    reset_token: str
    new_password: str


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


class AdminOTPVerifyRequest(BaseModel):
    email: EmailStr
    otp: str


# ── Login payload parser (JSON or form-data) ──────────────────────────────────

async def _parse_login_payload(request: Request) -> LoginRequest | SimpleNamespace:
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        body = await request.json()
        return LoginRequest.model_validate(body)
    form     = await request.form()
    username = form.get("username") or form.get("email")
    password = form.get("password")
    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="email/username and password are required.",
        )
    return SimpleNamespace(username=str(username), password=str(password))


# ═══════════════════════════════════════════════════════════════════════════════
# CUSTOMER routes
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/customer/register", response_model=RegisterResponse, status_code=201)
def register_customer(payload: CustomerRegister, db: Session = Depends(get_db)):
    """
    Register a new customer account.
    Sends a verification email with a link — user clicks link to activate.
    """
    return auth_service.register_customer(db, payload)


@router.post("/customer/login", tags=["Authentication"])
async def login_customer(request: Request, db: Session = Depends(get_db)):
    """Customer login — returns JWT access + refresh tokens."""
    payload = await _parse_login_payload(request)
    return auth_service.login_customer(db, payload)


@router.post(
    "/customer/logout",
    response_model=AuthMessageResponse,
    tags=["Authentication"],
)
def logout_customer(
    request: Request,
    db: Session = Depends(get_db),
    _: Customer = Depends(get_current_customer),
):
    """
    [E05] Customer session invalidation.
    Blacklists the current access token in Redis so it cannot be reused.
    The token TTL in Redis matches its remaining lifetime — no stale entries.
    Returns 200 even if Redis is unavailable (best-effort invalidation).
    """
    return auth_service.logout_customer(
        db, authorization=request.headers.get("Authorization")
    )


@router.post(
    "/customer/token/refresh",
    response_model=AuthResponse,
    response_model_by_alias=True,
    tags=["Authentication"],
)
def refresh_customer_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh customer access token using a refresh token."""
    return auth_service.refresh_customer_token(db, payload)


@router.get("/customer/verify-email")
def verify_customer_email(token: str = Query(...), db: Session = Depends(get_db)):
    """
    Verify customer email via the link sent in the registration email.
    Frontend should redirect here with the token as a query param.
    """
    return auth_service.verify_customer_email(db, token)


@router.post("/customer/email-verification/resend", response_model=AuthMessageResponse)
def resend_customer_verification_email(
    payload: ResendVerificationRequest,
    db: Session = Depends(get_db),
):
    """Resend customer verification email (link-based)."""
    return auth_service.resend_customer_verification_email(db, payload)


# ── Customer forgot password — 3-step OTP flow ───────────────────────────────

@router.post("/customer/password/forgot", response_model=AuthMessageResponse)
def customer_forgot_password(
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    """
    Step 1 — Forgot password.
    Sends a 6-digit OTP to the customer's email. OTP expires in 5 minutes.
    """
    return auth_service.request_customer_password_reset_otp(db, str(payload.email))


@router.post("/customer/password/verify-otp")
def customer_verify_password_otp(
    payload: VerifyOTPRequest,
    db: Session = Depends(get_db),
):
    """
    Step 2 — Verify OTP.
    Submit the 6-digit OTP from the email.
    Returns a short-lived reset token (valid 10 minutes) on success.

    Response: { "resetToken": "...", "message": "..." }
    """
    return auth_service.verify_customer_password_reset_otp(db, str(payload.email), payload.otp)



@router.post("/customer/password/reset", response_model=AuthMessageResponse)
def customer_reset_password(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    """
    Step 3 — Reset password.
    Submit the reset token from Step 2 along with the new password.
    """
    return auth_service.confirm_customer_password_reset(db, payload.reset_token, payload.new_password)


# ═══════════════════════════════════════════════════════════════════════════════
# VENDOR routes
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/vendor/register", response_model=VendorResponse, status_code=201)
def register_vendor(vendor_data: VendorRegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new vendor account.
    Sends a verification email with a link — user clicks link to activate.
    """
    if vendor_service.get_vendor_by_email(db, email=vendor_data.email):
        raise HTTPException(status_code=400, detail="Email already taken!")
    if vendor_service.get_vendor_by_display_name(db, name=vendor_data.business_name):
        raise HTTPException(status_code=400, detail="Business name already in use!")
    vendor = vendor_service.create_vendor(db, vendor_data)
    auth_service.register_vendor_verification(db, vendor)
    return vendor


@router.post("/vendor/login", tags=["Authentication"])
async def login_vendor(request: Request, db: Session = Depends(get_db)):
    """Vendor login — returns JWT access + refresh tokens."""
    payload = await _parse_login_payload(request)
    return auth_service.login_vendor(db, payload)


@router.post(
    "/vendor/logout",
    response_model=AuthMessageResponse,
    tags=["Authentication"],
)
def logout_vendor(
    request: Request,
    db: Session = Depends(get_db),
    _: Vendor = Depends(get_current_vendor),
):
    """
    [E06] Vendor session invalidation.
    Blacklists the current access token in Redis so it cannot be reused.
    The token TTL in Redis matches its remaining lifetime — no stale entries.
    Returns 200 even if Redis is unavailable (best-effort invalidation).
    """
    return auth_service.logout_vendor(
        db, authorization=request.headers.get("Authorization")
    )


@router.get("/vendor/verify-email")
def verify_vendor_email(token: str = Query(...), db: Session = Depends(get_db)):
    """
    Verify vendor email via the link sent in the registration email.
    Frontend should redirect here with the token as a query param.
    """
    return auth_service.verify_vendor_email(db, token)


@router.post("/vendor/email-verification/resend", response_model=AuthMessageResponse)
def resend_vendor_verification_email(
    payload: ResendVerificationRequest,
    db: Session = Depends(get_db),
):
    """Resend vendor verification email (link-based)."""
    return auth_service.resend_vendor_verification_email(db, payload)


# ── Vendor forgot password — 3-step OTP flow ─────────────────────────────────

@router.post("/vendor/password/forgot", response_model=AuthMessageResponse)
def vendor_forgot_password(
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    """
    Step 1 — Forgot password.
    Sends a 6-digit OTP to the vendor's email. OTP expires in 5 minutes.
    """
    return auth_service.request_vendor_password_reset_otp(db, str(payload.email))


@router.post("/vendor/password/verify-otp")
def vendor_verify_password_otp(
    payload: VerifyOTPRequest,
    db: Session = Depends(get_db),
):
    """
    Step 2 — Verify OTP.
    Submit the 6-digit OTP from the email.
    Returns a short-lived reset token (valid 10 minutes) on success.

    Response: { "resetToken": "...", "message": "..." }
    """
    return auth_service.verify_vendor_password_reset_otp(db, str(payload.email), payload.otp)


@router.post("/vendor/password/reset", response_model=AuthMessageResponse)
def vendor_reset_password(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    """
    Step 3 — Reset password.
    Submit the reset token from Step 2 and the new password.
    """
    return auth_service.confirm_vendor_password_reset(db, payload.reset_token, payload.new_password)


# ── Vendor token refresh ──────────────────────────────────────────────────────

@router.post(
    "/vendor/token/refresh",
    response_model=AuthResponse,
    response_model_by_alias=True,
    tags=["Authentication"],
)
def refresh_vendor_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh vendor access token using a refresh token."""
    # Reuse customer refresh logic — claims carry role so it's safe
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token.",
    )
    from jwt.exceptions import PyJWTError
    from app.core.security import decode_token, create_access_token, create_refresh_token
    from datetime import timedelta
    try:
        claims = decode_token(payload.refresh_token)
    except PyJWTError:
        raise exc
    if claims.get("type") != "refresh" or claims.get("role") != "VENDOR":
        raise exc
    email = claims.get("sub")
    if not email:
        raise exc
    vendor = vendor_service.get_vendor_by_email(db, email=email)
    if not vendor:
        raise exc
    access_token  = create_access_token(
        data={"sub": vendor.email, "role": "VENDOR"}, expires_delta=timedelta(minutes=60),
    )
    refresh_token = create_refresh_token(
        data={"sub": vendor.email, "role": "VENDOR"}, expires_delta=timedelta(days=7),
    )
    return {
        "access_token":  access_token,
        "token_type":    "bearer",
        "accessToken":   access_token,
        "refreshToken":  refresh_token,
        "user": {
            "userId": getattr(vendor, "vendor_id", str(getattr(vendor, "id", ""))),
            "email":  vendor.email,
            "role":   "VENDOR",
            "status": getattr(vendor, "status", "ACTIVE"),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN routes
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/admin/login", tags=["Authentication"])
def admin_login(payload: AdminLoginRequest, db: Session = Depends(get_db)):
    """
    Admin login — Step 1.
    Validates email + password. Sends a 6-digit OTP to admin email.
    OTP expires in 5 minutes.

    After this, call POST /auth/admin/login/verify-otp with email + otp
    to receive the JWT token.
    """
    from app.services.admin_service import admin_service
    return admin_service.login_admin(db, payload.email, payload.password)


@router.post("/admin/login/verify-otp", tags=["Authentication"])
def admin_verify_login_otp(payload: AdminOTPVerifyRequest, db: Session = Depends(get_db)):
    """
    Admin login — Step 2.
    Submit the 6-digit OTP sent to admin email.
    Returns JWT access token on success. OTP is single-use.
    """
    from app.services.admin_service import admin_service
    return admin_service.verify_admin_login_otp(db, payload.email, payload.otp)


# ── Admin forgot password — 3-step OTP flow ──────────────────────────────────

@router.post("/admin/password/forgot", response_model=AuthMessageResponse)
def admin_forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Admin forgot password — Step 1.
    Sends a 6-digit password reset OTP to the admin's email.
    OTP expires in 5 minutes.
    """
    from app.services.admin_service import admin_service
    return admin_service.request_admin_password_reset_otp(db, str(payload.email))


@router.post("/admin/password/verify-otp")
def admin_verify_password_otp(payload: AdminOTPVerifyRequest, db: Session = Depends(get_db)):
    """
    Admin forgot password — Step 2.
    Submit the 6-digit OTP from the email.
    Returns a short-lived reset token (valid 10 minutes) on success.

    Response: { "resetToken": "...", "message": "..." }
    """
    from app.services.admin_service import admin_service
    return admin_service.verify_admin_password_reset_otp(db, str(payload.email), payload.otp)


@router.post("/admin/password/reset", response_model=AuthMessageResponse)
def admin_reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Admin forgot password — Step 3.
    Submit the reset token from Step 2 and the new password.
    """
    from app.services.admin_service import admin_service
    return admin_service.confirm_admin_password_reset(db, payload.reset_token, payload.new_password)