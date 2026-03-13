from __future__ import annotations

import logging
import os
from datetime import UTC, datetime, timedelta

import httpx
import jwt
from fastapi import HTTPException
from jwt.exceptions import ExpiredSignatureError, PyJWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import ALGORITHM, SECRET_KEY, get_password_hash
from app.models.customer import Customer
from app.models.vendor import Vendor
from app.schemas.auth_schema import (
    CustomerRegister,
    ForgotPasswordRequest,
    ResetPasswordRequest
)

logger = logging.getLogger(__name__)

EMAIL_VERIFICATION_TTL_HOURS = 24
PASSWORD_RESET_TTL_MINUTES = 15


# --- Email Utility (Resend) ---

def _send_email(to: str, subject: str, text_body: str) -> bool:
    """
    Sends plain-text email via Resend API.
    Falls back to logger.info() if the SENDGRID_API_KEY environment variable is not set.
    """
    api_key = os.environ.get("SENDGRID_API_KEY", "")
    from_email = os.environ.get("FROM_EMAIL", "onboarding@resend.dev")

    if not api_key:
        logger.warning("No API key set - email not sent. Set SENDGRID_API_KEY in .env")
        logger.info("DEV MOCK | To: %s | Subject: %s", to, subject)
        return False

    try:
        response = httpx.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": f"Occacia <{from_email}>",
                "to": [to],
                "subject": subject,
                "text": text_body,
            },
            timeout=10,
        )
        response.raise_for_status()
        logger.info("Email sent to %s via Resend | Status: %s", to, response.status_code)
        return True
    except Exception as e:
        logger.error("Failed to send email to %s: %s", to, str(e))
        return False


def _build_customer_verification_email(email: str, token: str) -> tuple[str, str]:
    link = f"https://app.occacia.com/verify?token={token}"
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

    # --- Registration & Verification ---

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
            address=payload.address,
            locale=getattr(payload, "locale", None),
            email_verified=False,
            status="PENDING_VERIFICATION",
            verification_token=verification_token,
            verification_token_expires_at=expires_at,
        )
        db.add(customer)
        db.commit()

        subject, body = _build_customer_verification_email(str(payload.email), verification_token)
        _send_email(str(payload.email), subject, body)

        return {"message": "Verification email sent", "email": str(payload.email)}

    def register_vendor_verification(self, email: str) -> None:
        """Generates verification token and sends vendor verification email."""
        verification_token, _ = self._create_verification_token_internal(
            email,
            token_type="verify_vendor_email",
            hours=EMAIL_VERIFICATION_TTL_HOURS,
        )
        subject, body = _build_vendor_verification_email(email, verification_token)
        _send_email(email, subject, body)

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

        subject, body = _build_password_reset_email(str(payload.email), token)
        _send_email(str(payload.email), subject, body)

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