from datetime import timedelta
import jwt
import os
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import PyJWTError as JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import ALGORITHM, SECRET_KEY, create_access_token, verify_password
from app.schemas.auth_schema import (
    CustomerRegister, RegisterResponse, VerifyEmailResponse,
    ForgotPasswordRequest, ResetPasswordRequest, AuthMessageResponse
)
from app.schemas.vendor_schema import VendorRegisterRequest, VendorResponse
from app.services.customer_service import customer_service
from app.services.auth_service import auth_service
from app.services.vendor_service import vendor_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_vendor_scheme   = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/vendors/login",   scheme_name="VendorAuth")
oauth2_customer_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/customers/login", scheme_name="CustomerAuth")
oauth2_admin_scheme    = OAuth2PasswordBearer(tokenUrl="/api/v1/admin/login",           scheme_name="AdminAuth")
oauth2_scheme = oauth2_vendor_scheme


def _success_page(title: str, message: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: Arial, sans-serif; background: #f7f8fc; display: flex;
            align-items: center; justify-content: center; min-height: 100vh; }}
    .card {{ background: white; border-radius: 12px; padding: 48px 40px;
             max-width: 480px; width: 90%; text-align: center;
             box-shadow: 0 4px 24px rgba(0,0,0,0.08); }}
    .icon {{ font-size: 56px; margin-bottom: 24px; }}
    h1 {{ color: #2d3748; font-size: 24px; margin-bottom: 12px; }}
    p {{ color: #718096; font-size: 16px; line-height: 1.6; }}
    .badge {{ display: inline-block; background: #c6f6d5; color: #276749;
              padding: 6px 16px; border-radius: 999px; font-size: 14px;
              font-weight: bold; margin-top: 24px; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="icon">&#10003;</div>
    <h1>{title}</h1>
    <p>{message}</p>
    <div class="badge">You can close this tab</div>
  </div>
</body>
</html>"""


def _error_page(title: str, message: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: Arial, sans-serif; background: #f7f8fc; display: flex;
            align-items: center; justify-content: center; min-height: 100vh; }}
    .card {{ background: white; border-radius: 12px; padding: 48px 40px;
             max-width: 480px; width: 90%; text-align: center;
             box-shadow: 0 4px 24px rgba(0,0,0,0.08); }}
    .icon {{ font-size: 56px; margin-bottom: 24px; }}
    h1 {{ color: #2d3748; font-size: 24px; margin-bottom: 12px; }}
    p {{ color: #718096; font-size: 16px; line-height: 1.6; }}
    .badge {{ display: inline-block; background: #fed7d7; color: #9b2c2c;
              padding: 6px 16px; border-radius: 999px; font-size: 14px;
              font-weight: bold; margin-top: 24px; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="icon">&#10007;</div>
    <h1>{title}</h1>
    <p>{message}</p>
    <div class="badge">Please request a new verification email</div>
  </div>
</body>
</html>"""


def _wants_json(request: Request) -> bool:
    accept = request.headers.get("accept", "")
    # If no Accept header or not explicitly requesting HTML, return JSON.
    # Browsers always send text/html in Accept; test clients typically don't.
    if not accept or accept == "*/*":
        return True
    return "application/json" in accept and "text/html" not in accept


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


@router.post("/vendors/register", response_model=VendorResponse, status_code=201)
def register_vendor(vendor_data: VendorRegisterRequest, db: Session = Depends(get_db)):
    if vendor_service.get_vendor_by_email(db, email=vendor_data.email):
        raise HTTPException(status_code=400, detail="Email already taken!")
    if vendor_service.get_vendor_by_display_name(db, name=vendor_data.business_name):
        raise HTTPException(status_code=400, detail="Business name already in use!")
    vendor = vendor_service.create_vendor(db, vendor_data)
    auth_service.register_vendor_verification(vendor.email)
    return vendor


@router.post("/customers/register", response_model=RegisterResponse, status_code=201)
def register_customer(payload: CustomerRegister, db: Session = Depends(get_db)):
    return auth_service.register_customer(db, payload)


@router.get("/customers/verify-email")
def verify_customer_email(request: Request, token: str = Query(...), db: Session = Depends(get_db)):
    try:
        result = auth_service.verify_customer_email(db, token)
        # verify_customer_email returns a dict e.g. {"message": "Email already verified"}
        # or {"message": "Email verified successfully"}
        msg = result.get("message", "Email verified successfully") if isinstance(result, dict) else "Email verified successfully"
        if _wants_json(request):
            return JSONResponse(content={"message": msg})
        return HTMLResponse(content=_success_page(
            "Email Verified!",
            "Your Occacia account has been activated. You can now log in."
        ))
    except HTTPException as e:
        if _wants_json(request):
            return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
        return HTMLResponse(status_code=e.status_code,
                            content=_error_page("Verification Failed", e.detail))
    except Exception:
        if _wants_json(request):
            return JSONResponse(status_code=400, content={"detail": "Invalid verification token."})
        return HTMLResponse(status_code=400,
                            content=_error_page("Verification Failed", "Link invalid or expired."))


@router.get("/vendors/verify-email")
def verify_vendor_email(request: Request, token: str = Query(...), db: Session = Depends(get_db)):
    try:
        auth_service.verify_vendor_email(db, token)
        if _wants_json(request):
            return JSONResponse(content={"message": "Email verified successfully"})
        return HTMLResponse(content=_success_page(
            "Vendor Email Verified!",
            "Your vendor email has been verified. Our team will review your application."
        ))
    except HTTPException as e:
        if _wants_json(request):
            return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
        return HTMLResponse(status_code=e.status_code,
                            content=_error_page("Verification Failed", e.detail))
    except Exception:
        if _wants_json(request):
            return JSONResponse(status_code=400, content={"detail": "Invalid verification token."})
        return HTMLResponse(status_code=400,
                            content=_error_page("Verification Failed", "Link invalid or expired."))


@router.post("/customers/forgot-password", response_model=AuthMessageResponse)
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    return auth_service.request_password_reset(db, request)


@router.post("/customers/reset-password", response_model=AuthMessageResponse)
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    return auth_service.confirm_password_reset(db, request)


@router.post("/customers/login", tags=["Authentication"])
def login_customer(form_data: OAuth2PasswordRequestForm = Depends(),
                   db: Session = Depends(get_db)):
    customer = customer_service.get_customer_by_email(db, email=form_data.username)
    verify_user_login(customer, form_data)
    token = create_access_token(data={"sub": customer.email},
                                expires_delta=timedelta(minutes=60))
    return {"access_token": token, "token_type": "bearer"}


@router.post("/vendors/login", tags=["Authentication"])
def login_vendor(form_data: OAuth2PasswordRequestForm = Depends(),
                 db: Session = Depends(get_db)):
    vendor = vendor_service.get_vendor_by_email(db, email=form_data.username)
    verify_user_login(vendor, form_data)
    token = create_access_token(data={"sub": vendor.email},
                                expires_delta=timedelta(minutes=60))
    return {"access_token": token, "token_type": "bearer"}


@router.get("/vendors/me", response_model=VendorResponse)
def read_current_vendor(current_vendor=Depends(get_current_vendor)):
    return current_vendor


@router.get("/customers/me")
def read_current_customer(current_customer=Depends(get_current_customer)):
    return {
        "id": current_customer.id,
        "email": current_customer.email,
        "full_name": current_customer.full_name,
        "status": current_customer.status,
    }