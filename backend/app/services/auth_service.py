"""
app/services/auth_service.py
"""
from __future__ import annotations

import logging
import os
import random
import string
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
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.customer import Customer
from app.models.vendor import Vendor
from app.schemas.auth_schema import (
    AuthResponse,
    CustomerRegister,
    LoginRequest,
    RefreshTokenRequest,
    ResendVerificationRequest,
)
from app.services.customer_service import customer_service
from app.services.notification_service import notification_service
from app.services.vendor_service import vendor_service

logger = logging.getLogger(__name__)

EMAIL_VERIFICATION_TTL_HOURS = 24
OTP_TTL_SECONDS              = 300   # 5 minutes
OTP_LENGTH                   = 6
RESET_TOKEN_TTL_MINUTES      = 10    # reset token after OTP verified


# ── Redis helper ──────────────────────────────────────────────────────────────

def _get_redis():
    try:
        import redis as redis_lib
        client = redis_lib.from_url(
            getattr(settings, "REDIS_URL", "redis://redis:6379"),
            decode_responses=True,
            socket_connect_timeout=3,
        )
        client.ping()
        return client
    except Exception as exc:
        logger.warning("Redis unavailable: %s", exc)
        return None


def _generate_otp() -> str:
    return "".join(random.choices(string.digits, k=OTP_LENGTH))


# ── Legacy direct-send wrapper (used by admin approval/rejection emails) ──────

def _send_email(to: str, subject: str, text_body: str) -> bool:
    result = notification_service._send_email(
        to=to, subject=subject, text_body=text_body, html_body=None,
    )
    return result.success


# ── AuthService ───────────────────────────────────────────────────────────────

class AuthService:

    # ── Customer registration & login ─────────────────────────────────────────

    def register_customer(self, db: Session, payload: CustomerRegister) -> dict[str, str]:
        existing = db.query(Customer).filter(
            Customer.email == str(payload.email)).first()
        if existing:
            raise HTTPException(
                status_code=400, detail="This email is already registered.")

        verification_token, expires_at = self._create_verification_token(
            str(payload.email), token_type="verify_customer_email",
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
            db, customer=customer, verification_token=verification_token,
        )
        return {"message": "Registration successful. Please verify your email."}

    def login_customer(self, db: Session, payload: LoginRequest | OAuth2PasswordRequestForm) -> dict:
        email    = getattr(payload, "email", None) or getattr(payload, "username", None)
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
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Customer account is not active.")

        access_token  = create_access_token(
            data={"sub": customer.email, "role": "CUSTOMER"}, expires_delta=timedelta(minutes=60),
        )
        refresh_token = create_refresh_token(
            data={"sub": customer.email, "role": "CUSTOMER"}, expires_delta=timedelta(days=7),
        )
        return {
            "access_token":  access_token,
            "token_type":    "bearer",
            "accessToken":   access_token,
            "refreshToken":  refresh_token,
            "user": {
                "userId": customer.customer_id,
                "email":  customer.email,
                "role":   "CUSTOMER",
                "status": customer.status,
            },
        }

    def refresh_customer_token(self, db: Session, payload: RefreshTokenRequest) -> dict:
        exc = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        )
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
        access_token  = create_access_token(
            data={"sub": customer.email, "role": "CUSTOMER"}, expires_delta=timedelta(minutes=60),
        )
        refresh_token = create_refresh_token(
            data={"sub": customer.email, "role": "CUSTOMER"}, expires_delta=timedelta(days=7),
        )
        return {
            "access_token":  access_token,
            "token_type":    "bearer",
            "accessToken":   access_token,
            "refreshToken":  refresh_token,
            "user": {
                "userId": customer.customer_id,
                "email":  customer.email,
                "role":   "CUSTOMER",
                "status": customer.status,
            },
        }

    def verify_customer_email(self, db: Session, token: str) -> dict[str, str]:
        claims   = self._decode_verification_token(token, expected_type="verify_customer_email")
        email    = claims.get("sub")
        customer = db.query(Customer).filter(Customer.email == email).first()
        if not customer:
            raise HTTPException(status_code=400, detail="Invalid verification token.")
        if customer.email_verified:
            return {"message": "Email already verified"}
        if customer.verification_token != token:
            raise HTTPException(status_code=400, detail="Invalid verification token.")
        customer.email_verified                = True
        customer.status                        = "ACTIVE"
        customer.verification_token            = None
        customer.verification_token_expires_at = None
        db.add(customer)
        db.commit()
        return {"message": "Email verified successfully"}

    def resend_customer_verification_email(
        self, db: Session, payload: ResendVerificationRequest,
    ) -> dict[str, str]:
        customer = db.query(Customer).filter(
            Customer.email == str(payload.email)).first()
        if not customer:
            raise HTTPException(status_code=400, detail="Customer account not found.")
        if customer.email_verified or customer.status == "ACTIVE":
            raise HTTPException(status_code=400, detail="Email already verified.")
        if customer.status not in {"PENDING", "PENDING_VERIFICATION"}:
            raise HTTPException(status_code=400, detail="Account is not pending verification.")
        verification_token, expires_at = self._create_verification_token(
            str(payload.email), token_type="verify_customer_email",
            hours=EMAIL_VERIFICATION_TTL_HOURS,
        )
        customer.verification_token            = verification_token
        customer.verification_token_expires_at = expires_at
        db.add(customer)
        db.commit()
        db.refresh(customer)
        notification_service.queue_customer_verification(
            db, customer=customer, verification_token=verification_token,
        )
        return {"message": "Verification email resent successfully."}

    # ── Customer forgot password — OTP flow ───────────────────────────────────

    def request_customer_password_reset_otp(
        self, db: Session, email: str,
    ) -> dict[str, str]:
        """Step 1 — send OTP to customer email."""
        customer  = customer_service.get_customer_by_email(db, email=email)
        if not customer:
            return {"message": "If this email is registered, a reset code has been sent."}

        otp_code  = _generate_otp()
        redis     = _get_redis()
        redis_key = f"pwd_otp:customer:{email}"
        if redis:
            redis.setex(redis_key, OTP_TTL_SECONDS, otp_code)
        else:
            logger.warning("Redis unavailable — customer OTP for %s: %s", email, otp_code)

        notification_service.queue_customer_password_reset_otp(
            db, customer=customer, otp_code=otp_code,
        )
        return {"message": "If this email is registered, a reset code has been sent."}

    def resend_customer_password_reset_otp(
        self, db: Session, email: str,
    ) -> dict[str, str]:
        """Resend password reset OTP to customer email."""
        return self.request_customer_password_reset_otp(db, email)

    def verify_customer_password_reset_otp(
        self, db: Session, email: str, otp_code: str,
    ) -> dict[str, str]:
        """Step 2 — verify OTP, return short-lived reset token."""
        redis     = _get_redis()
        redis_key = f"pwd_otp:customer:{email}"
        if not redis:
            raise HTTPException(status_code=503, detail="OTP service temporarily unavailable.")
        stored = redis.get(redis_key)
        if not stored:
            raise HTTPException(status_code=400, detail="OTP has expired or is invalid. Please request a new one.")
        if stored != otp_code.strip():
            raise HTTPException(status_code=400, detail="Invalid OTP code.")
        redis.delete(redis_key)  # consume — one use only

        reset_token = self._create_reset_token(email, role="CUSTOMER")
        return {"resetToken": reset_token, "message": "OTP verified. You may now reset your password."}

    def confirm_customer_password_reset(
        self, db: Session, reset_token: str, new_password: str,
    ) -> dict[str, str]:
        """Step 3 — accept reset token + new password."""
        claims   = self._decode_reset_token(reset_token, expected_role="CUSTOMER")
        email    = claims.get("sub")
        customer = customer_service.get_customer_by_email(db, email=email)
        if not customer:
            raise HTTPException(status_code=404, detail="User not found.")
        customer.password_hash = get_password_hash(new_password)
        db.add(customer)
        db.commit()
        logger.info("Customer password reset: %s", email)
        return {"message": "Password updated successfully."}

    def change_customer_password_authenticated(
        self, db: Session, customer: Customer, current_password: str, new_password: str,
    ) -> dict[str, str]:
        """Change customer password for an authenticated session."""
        if not customer.password_hash or not verify_password(current_password, customer.password_hash):
            raise HTTPException(status_code=400, detail="Current password is incorrect.")
        customer.password_hash = get_password_hash(new_password)
        db.add(customer)
        db.commit()
        logger.info("Customer password changed (authenticated): %s", customer.email)
        return {"message": "Password updated successfully."}

    # ── Vendor registration & login ───────────────────────────────────────────

    def register_vendor_verification(self, db: Session, vendor: Vendor) -> None:
        verification_token, _ = self._create_verification_token(
            vendor.email, token_type="verify_vendor_email",
            hours=EMAIL_VERIFICATION_TTL_HOURS,
        )
        notification_service.queue_vendor_verification(
            db, vendor=vendor, verification_token=verification_token,
        )

    def login_vendor(self, db: Session, payload: LoginRequest | OAuth2PasswordRequestForm) -> dict:
        email    = getattr(payload, "email", None) or getattr(payload, "username", None)
        password = payload.password
        vendor   = vendor_service.get_vendor_by_email(db, email=str(email))
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        vendor_password = getattr(vendor, "password_hash", None) or getattr(vendor, "hashed_password", None)
        if not vendor_password or not verify_password(password, vendor_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if os.getenv("SKIP_EMAIL_VERIFICATION") != "true":
            if not getattr(vendor, "email_verified", True) and not getattr(vendor, "is_verified", True):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email not verified.")
        approval_status = getattr(vendor, "approval_status", None)
        if approval_status != "APPROVED":
            detail = {
                "PENDING": "Your account is pending admin approval.",
                "REJECTED": "Your vendor account has been rejected.",
                "SUSPENDED": "Your vendor account has been suspended.",
                "DISABLED": "Your vendor account has been disabled.",
            }.get(approval_status, "Vendor account is not active.")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

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
                "status": getattr(vendor, "approval_status", getattr(vendor, "status", "ACTIVE")),
            },
        }

    def verify_vendor_email(self, db: Session, token: str) -> dict[str, str]:
        claims = self._decode_verification_token(token, expected_type="verify_vendor_email")
        email  = claims.get("sub")
        vendor = db.query(Vendor).filter(Vendor.email == email).first()
        if not vendor:
            raise HTTPException(status_code=400, detail="Invalid verification token.")
        if vendor.is_verified:
            return {"message": "Email already verified"}
        vendor.is_verified = True
        if getattr(vendor, "approval_status", None) in (None, "", "PENDING_VERIFICATION"):
            vendor.approval_status = "PENDING"
        db.add(vendor)
        db.commit()
        return {"message": "Email verified successfully. Your account is pending admin approval."}

    def resend_vendor_verification_email(
        self, db: Session, payload: ResendVerificationRequest,
    ) -> dict[str, str]:
        vendor = db.query(Vendor).filter(Vendor.email == str(payload.email)).first()
        if not vendor:
            raise HTTPException(status_code=400, detail="Vendor account not found.")
        if getattr(vendor, "is_verified", False):
            raise HTTPException(status_code=400, detail="Email already verified.")
        self.register_vendor_verification(db, vendor)
        return {"message": "Verification email resent successfully."}

    # ── Vendor forgot password — OTP flow ─────────────────────────────────────

    def request_vendor_password_reset_otp(
        self, db: Session, email: str,
    ) -> dict[str, str]:
        """Step 1 — send OTP to vendor email."""
        vendor    = vendor_service.get_vendor_by_email(db, email=email)
        if not vendor:
            return {"message": "If this email is registered, a reset code has been sent."}

        otp_code  = _generate_otp()
        redis     = _get_redis()
        redis_key = f"pwd_otp:vendor:{email}"
        if redis:
            redis.setex(redis_key, OTP_TTL_SECONDS, otp_code)
        else:
            logger.warning("Redis unavailable — vendor OTP for %s: %s", email, otp_code)

        notification_service.queue_vendor_password_reset_otp(
            db, vendor=vendor, otp_code=otp_code,
        )
        return {"message": "If this email is registered, a reset code has been sent."}

    def resend_vendor_password_reset_otp(
        self, db: Session, email: str,
    ) -> dict[str, str]:
        """Resend password reset OTP to vendor email."""
        return self.request_vendor_password_reset_otp(db, email)

    def verify_vendor_password_reset_otp(
        self, db: Session, email: str, otp_code: str,
    ) -> dict[str, str]:
        """Step 2 — verify OTP, return short-lived reset token."""
        redis     = _get_redis()
        redis_key = f"pwd_otp:vendor:{email}"
        if not redis:
            raise HTTPException(status_code=503, detail="OTP service temporarily unavailable.")
        stored = redis.get(redis_key)
        if not stored:
            raise HTTPException(status_code=400, detail="OTP has expired or is invalid. Please request a new one.")
        if stored != otp_code.strip():
            raise HTTPException(status_code=400, detail="Invalid OTP code.")
        redis.delete(redis_key)

        reset_token = self._create_reset_token(email, role="VENDOR")
        return {"resetToken": reset_token, "message": "OTP verified. You may now reset your password."}

    def confirm_vendor_password_reset(
        self, db: Session, reset_token: str, new_password: str,
    ) -> dict[str, str]:
        """Step 3 — accept reset token + new password."""
        claims = self._decode_reset_token(reset_token, expected_role="VENDOR")
        email  = claims.get("sub")
        vendor = vendor_service.get_vendor_by_email(db, email=email)
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found.")
        vendor.password_hash = get_password_hash(new_password)
        db.add(vendor)
        db.commit()
        logger.info("Vendor password reset: %s", email)
        return {"message": "Password updated successfully."}

    def change_vendor_password_authenticated(
        self, db: Session, vendor: Vendor, current_password: str, new_password: str,
    ) -> dict[str, str]:
        """Change vendor password for an authenticated session."""
        vendor_password = getattr(vendor, "password_hash", None) or getattr(vendor, "hashed_password", None)
        if not vendor_password or not verify_password(current_password, vendor_password):
            raise HTTPException(status_code=400, detail="Current password is incorrect.")
        vendor.password_hash = get_password_hash(new_password)
        db.add(vendor)
        db.commit()
        logger.info("Vendor password changed (authenticated): %s", vendor.email)
        return {"message": "Password updated successfully."}

    # ── Session Invalidation [E05] Customer / [E06] Vendor ───────────────────

    def logout_customer(self, db: Session, authorization: str | None) -> dict[str, str]:
        """
        [E05] Invalidate customer session by blacklisting the access token in Redis.
        The token is stored with a TTL equal to its remaining lifetime so Redis
        never holds stale entries. If Redis is unavailable the logout still
        succeeds — the token will expire naturally (best-effort invalidation).
        """
        if authorization and authorization.lower().startswith("bearer "):
            token = authorization[7:]
            self._blacklist_token(token, role="CUSTOMER")
        return {"message": "Logged out successfully."}

    def logout_vendor(self, db: Session, authorization: str | None) -> dict[str, str]:
        """
        [E06] Invalidate vendor session by blacklisting the access token in Redis.
        Same best-effort semantics as logout_customer.
        """
        if authorization and authorization.lower().startswith("bearer "):
            token = authorization[7:]
            self._blacklist_token(token, role="VENDOR")
        return {"message": "Logged out successfully."}

    def _blacklist_token(self, token: str, role: str) -> None:
        """Store the token in Redis with TTL matching its remaining lifetime."""
        try:
            claims = decode_token(token)
            exp    = claims.get("exp")
            if exp:
                ttl = int(exp - datetime.now(UTC).timestamp())
                if ttl > 0:
                    redis = _get_redis()
                    if redis:
                        redis.setex(f"blacklist:{token}", ttl, role)
                        logger.info("Token blacklisted role=%s ttl=%ds", role, ttl)
        except Exception as exc:
            # Never block logout because of Redis / JWT errors
            logger.warning("Token blacklist failed (non-blocking): %s", exc)

    # ── Token helpers ─────────────────────────────────────────────────────────

    def _create_reset_token(self, email: str, role: str) -> str:
        """Short-lived JWT issued after OTP verified. Authorises the final password reset."""
        expires_at = datetime.now(UTC) + timedelta(minutes=RESET_TOKEN_TTL_MINUTES)
        return jwt.encode(
            {"sub": email, "type": "pwd_reset_verified", "role": role, "exp": expires_at},
            SECRET_KEY, algorithm=ALGORITHM,
        )

    def _decode_reset_token(self, token: str, expected_role: str) -> dict:
        try:
            claims = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except ExpiredSignatureError as exc:
            raise HTTPException(
                status_code=400, detail="Reset token has expired. Please request a new OTP.",
            ) from exc
        except PyJWTError as exc:
            raise HTTPException(status_code=400, detail="Invalid reset token.") from exc
        if claims.get("type") != "pwd_reset_verified":
            raise HTTPException(status_code=400, detail="Invalid reset token.")
        if claims.get("role") != expected_role:
            raise HTTPException(status_code=400, detail="Invalid reset token.")
        return claims

    @staticmethod
    def _create_verification_token(
        email: str, token_type: str, hours: int = 0, minutes: int = 0,
    ) -> tuple[str, datetime]:
        expires_at = datetime.now(UTC) + timedelta(hours=hours, minutes=minutes)
        token      = jwt.encode(
            {"sub": email, "type": token_type, "exp": expires_at},
            SECRET_KEY, algorithm=ALGORITHM,
        )
        return token, expires_at

    @staticmethod
    def _decode_verification_token(token: str, expected_type: str) -> dict:
        try:
            claims = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except ExpiredSignatureError as exc:
            raise HTTPException(status_code=400, detail="Verification token has expired.") from exc
        except PyJWTError as exc:
            raise HTTPException(status_code=400, detail="Invalid verification token.") from exc
        if claims.get("type") != expected_type:
            raise HTTPException(
                status_code=400, detail="Invalid verification token.")
        return claims


auth_service = AuthService()
