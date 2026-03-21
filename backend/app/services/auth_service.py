"""
app/services/auth_service.py
"""
from __future__ import annotations

import logging
import os
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jwt.exceptions import ExpiredSignatureError, PyJWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    ALGORITHM, 
    SECRET_KEY, 
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.models.customer import Customer
from app.models.vendor import Vendor
from app.schemas.auth_schema import (
    AuthResponse,
    CustomerRegister,
    ForgotPasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    ResendVerificationRequest,
    ResetPasswordRequest
)
from app.services.customer_service import customer_service
from app.services.notification_service import notification_service
from app.services.vendor_service import vendor_service

logger = logging.getLogger(__name__)

EMAIL_VERIFICATION_TTL_HOURS = 24
PASSWORD_RESET_TTL_MINUTES = 15


# --- Email Utility (legacy direct-send wrapper used by a few existing flows) ---

def _send_email(to: str, subject: str, text_body: str) -> bool:
    result = notification_service._send_email(
        to=to,
        subject=subject,
        text_body=text_body,
        html_body=None,
    )
    return result.success


def _build_customer_verification_email(email: str, token: str) -> tuple[str, str]:
    link = f"https://app.occacia.com/customers/register/verify-email?token={token}"
    subject = "Verify your Occacia account"
    body = (
        "Welcome to Occacia!\n\n"
        "Thank you for registering. Please verify your email address to activate your account "
        "by clicking the link below:\n\n"
        f"{link}\n\n"
        "This link expires in 24 hours.\n"
        "If you didn't create an account, you can safely ignore this email."
    )
    return subject, body


def _build_vendor_verification_email(email: str, token: str) -> tuple[str, str]:
    link = f"https://app.occacia.com/vendor-verify?token={token}"
    subject = "Verify your Occacia vendor account"
    body = (
        "Welcome to Occacia Vendors!\n\n"
        "Please verify your email address to complete your vendor registration "
        "by clicking the link below:\n\n"
        f"{link}\n\n"
        "Your account will be reviewed by our team after verification.\n"
        "This link expires in 24 hours."
    )
    return subject, body


def _build_password_reset_email(email: str, token: str) -> tuple[str, str]:
    link = f"https://app.occacia.com/reset-password?token={token}"
    subject = "Reset your Occacia password"
    body = (
        "Password Reset Request\n\n"
        "We received a request to reset the password for your Occacia account. "
        "Click the link below to reset it:\n\n"
        f"{link}\n\n"
        "This link expires in 15 minutes.\n"
        "If you didn't request a password reset, you can safely ignore this email — "
        "your password will not be changed."
    )
    return subject, body


# --- AuthService ---

class AuthService:

    # --- Customer Registration & Login ---

    def register_customer(self, db: Session, payload: CustomerRegister) -> dict[str, str]:
        existing = db.query(Customer).filter(Customer.email == str(payload.email)).first()
        if existing:
            raise HTTPException(status_code=400, detail="This email is already registered.")

        verification_token, expires_at = self._create_verification_token_internal(
            str(payload.email),
            token_type="verify_customer_email",
            hours=EMAIL_VERIFICATION_TTL_HOURS,
        )

        customer = Customer(
            full_name=payload.full_name,
            email=str(payload.email),
            password_hash=get_password_hash(payload.password),
            phone=payload.phone,
            locale=getattr(payload, "locale", None),
            email_verified=False,
            status="PENDING",
            verification_token=verification_token,
            verification_token_expires_at=expires_at,
        )
        db.add(customer)
        db.commit()

        db.refresh(customer)
        notification_service.queue_customer_verification(
            db,
            customer=customer,
            verification_token=verification_token,
        )

        return {"message": "Registration successful. Please verify your email."}

    def login_customer(self, db: Session, payload: LoginRequest | OAuth2PasswordRequestForm) -> dict:
        # 🚨 DEVSECOPS FIX: Dynamically grab email whether from JSON (.email) or Swagger Form (.username)
        email = getattr(payload, "email", None) or getattr(payload, "username", None)
        password = payload.password

        customer = customer_service.get_customer_by_email(db, email=str(email))
        
        if not customer or not customer.password_hash or not verify_password(password, customer.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        if os.getenv("SKIP_EMAIL_VERIFICATION") != "true" and not customer.email_verified:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email not verified.")
            
        if customer.status != "ACTIVE":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Customer account is not active.")

        access_token = create_access_token(
            data={"sub": customer.email, "role": "CUSTOMER"}, 
            expires_delta=timedelta(minutes=60)
        )
        refresh_token = create_refresh_token(
            data={"sub": customer.email, "role": "CUSTOMER"}, 
            expires_delta=timedelta(days=7)
        )
        
        # 🚨 DEVSECOPS FIX: Return a "Dual-Compatibility" Dictionary
        return {
            "access_token": access_token,      # Required for Swagger UI Padlock
            "token_type": "bearer",            # Required for Swagger UI Padlock
            "accessToken": access_token,       # Kept for Next.js backwards compatibility
            "refreshToken": refresh_token,     # Kept for Next.js backwards compatibility
            "user": {
                "userId": customer.customer_id,
                "email": customer.email,
                "role": "CUSTOMER",
                "status": customer.status,
            }
        }

    def refresh_customer_token(self, db: Session, payload: RefreshTokenRequest) -> dict:
        exc = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token.")
        try:
            claims = decode_token(payload.refresh_token)
        except PyJWTError:
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

        access_token = create_access_token(
            data={"sub": customer.email, "role": "CUSTOMER"}, 
            expires_delta=timedelta(minutes=60)
        )
        refresh_token = create_refresh_token(
            data={"sub": customer.email, "role": "CUSTOMER"}, 
            expires_delta=timedelta(days=7)
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "accessToken": access_token,
            "refreshToken": refresh_token,
            "user": {
                "userId": customer.customer_id,
                "email": customer.email,
                "role": "CUSTOMER",
                "status": customer.status,
            }
        }

    def verify_customer_email(self, db: Session, token: str) -> dict[str, str]:
        claims = self._decode_verification_token(token, expected_type="verify_customer_email")
        email = claims.get("sub")

        customer = db.query(Customer).filter(Customer.email == email).first()
        if not customer:
            raise HTTPException(status_code=400, detail="Invalid verification token.")

        if customer.email_verified:
            return {"message": "Email already verified"}

        if customer.verification_token != token:
            raise HTTPException(status_code=400, detail="Invalid verification token.")

        customer.email_verified = True
        customer.status = "ACTIVE"
        customer.verification_token = None
        customer.verification_token_expires_at = None
        db.add(customer)
        db.commit()

        return {"message": "Email verified successfully"}

    def resend_customer_verification_email(
        self,
        db: Session,
        payload: ResendVerificationRequest,
    ) -> dict[str, str]:
        customer = db.query(Customer).filter(Customer.email == str(payload.email)).first()
        if not customer:
            raise HTTPException(status_code=400, detail="Customer account not found.")

        if customer.email_verified or customer.status == "ACTIVE":
            raise HTTPException(status_code=400, detail="Email already verified.")

        if customer.status not in {"PENDING", "PENDING_VERIFICATION"}:
            raise HTTPException(
                status_code=400,
                detail="Customer account is not pending email verification.",
            )

        verification_token, expires_at = self._create_verification_token_internal(
            str(payload.email),
            token_type="verify_customer_email",
            hours=EMAIL_VERIFICATION_TTL_HOURS,
        )
        customer.verification_token = verification_token
        customer.verification_token_expires_at = expires_at
        db.add(customer)
        db.commit()

        db.refresh(customer)
        notification_service.queue_customer_verification(
            db,
            customer=customer,
            verification_token=verification_token,
        )
        return {"message": "Verification email resent successfully."}

    # --- Vendor Registration & Login ---

    def register_vendor_verification(self, db: Session, vendor: Vendor) -> None:
        verification_token, _ = self._create_verification_token_internal(
            vendor.email,
            token_type="verify_vendor_email",
            hours=EMAIL_VERIFICATION_TTL_HOURS,
        )
        notification_service.queue_vendor_verification(
            db,
            vendor=vendor,
            verification_token=verification_token,
        )

    def login_vendor(self, db: Session, payload: LoginRequest | OAuth2PasswordRequestForm) -> dict:
        # 🚨 DEVSECOPS FIX: Dynamically grab email whether from JSON (.email) or Swagger Form (.username)
        email = getattr(payload, "email", None) or getattr(payload, "username", None)
        password = payload.password
        
        vendor = vendor_service.get_vendor_by_email(db, email=str(email))
        
        if not vendor:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password", headers={"WWW-Authenticate": "Bearer"})
            
        vendor_password = getattr(vendor, 'password_hash', None) or getattr(vendor, 'hashed_password', None)
        if not vendor_password or not verify_password(password, vendor_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password", headers={"WWW-Authenticate": "Bearer"})
            
        if os.getenv("SKIP_EMAIL_VERIFICATION") != "true":
            if not getattr(vendor, 'email_verified', True) and not getattr(vendor, 'is_verified', True):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email not verified.")

        access_token = create_access_token(
            data={"sub": vendor.email, "role": "VENDOR"}, 
            expires_delta=timedelta(minutes=60)
        )
        refresh_token = create_refresh_token(
            data={"sub": vendor.email, "role": "VENDOR"}, 
            expires_delta=timedelta(days=7)
        )

        # 🚨 DEVSECOPS FIX: Return a "Dual-Compatibility" Dictionary
        return {
            "access_token": access_token,      # Swagger UI
            "token_type": "bearer",            # Swagger UI
            "accessToken": access_token,       # Next.js
            "refreshToken": refresh_token,     # Next.js
            "user": {
                "userId": getattr(vendor, "vendor_id", str(getattr(vendor, "id", ""))),
                "email": vendor.email,
                "role": "VENDOR",
                "status": getattr(vendor, "status", "ACTIVE"),
            }
        }

    def verify_vendor_email(self, db: Session, token: str) -> dict[str, str]:
        claims = self._decode_verification_token(token, expected_type="verify_vendor_email")
        email = claims.get("sub")

        vendor = db.query(Vendor).filter(Vendor.email == email).first()
        if not vendor:
            raise HTTPException(status_code=400, detail="Invalid verification token.")

        if vendor.is_verified:
            return {"message": "Email already verified"}

        vendor.is_verified = True
        db.add(vendor)
        db.commit()
        return {"message": "Email verified successfully"}

    # --- Password Reset ---

    def request_password_reset(self, db: Session, payload: ForgotPasswordRequest) -> dict[str, str]:
        customer = db.query(Customer).filter(Customer.email == str(payload.email)).first()

        if not customer:
            logger.info("Reset requested for non-existent email: %s", payload.email)
            return {"message": "If this email is registered, a reset link has been sent."}

        token, _ = self._create_verification_token_internal(
            str(payload.email),
            token_type="password_reset",
            minutes=PASSWORD_RESET_TTL_MINUTES,
        )

        notification_service.queue_password_reset(
            db,
            customer=customer,
            token=token,
        )

        return {"message": "If this email is registered, a reset link has been sent."}

    def confirm_password_reset(self, db: Session, payload: ResetPasswordRequest) -> dict[str, str]:
        claims = self._decode_verification_token(payload.token, expected_type="password_reset")
        email = claims.get("sub")

        customer = db.query(Customer).filter(Customer.email == email).first()
        if not customer:
            raise HTTPException(status_code=404, detail="User not found.")

        customer.password_hash = get_password_hash(payload.new_password)
        db.add(customer)
        db.commit()

        logger.info("Password successfully reset for: %s", email)
        return {"message": "Password updated successfully"}

    # --- Internal Token Helpers ---

    @staticmethod
    def _create_verification_token_internal(
        email: str, token_type: str, hours: int = 0, minutes: int = 0
    ) -> tuple[str, datetime]:
        expires_at = datetime.now(UTC) + timedelta(hours=hours, minutes=minutes)
        payload = {"sub": email, "type": token_type, "exp": expires_at}
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        return token, expires_at

    @staticmethod
    def _decode_verification_token(token: str, expected_type: str) -> dict:
        try:
            claims = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except ExpiredSignatureError as exc:
            raise HTTPException(
                status_code=400, detail="Verification token has expired."
            ) from exc
        except PyJWTError as exc:
            raise HTTPException(
                status_code=400, detail="Invalid verification token."
            ) from exc

        if claims.get("type") != expected_type:
            raise HTTPException(status_code=400, detail="Invalid verification token.")
        return claims


auth_service = AuthService()
