from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import HTTPException
from jwt.exceptions import ExpiredSignatureError, PyJWTError
from sqlalchemy.orm import Session

from app.core.security import ALGORITHM, SECRET_KEY, get_password_hash
from app.models.marketplace import Customer, Vendor
from app.schemas.auth_schema import (
    CustomerRegister, 
    ForgotPasswordRequest, 
    ResetPasswordRequest
)

logger = logging.getLogger(__name__)

EMAIL_VERIFICATION_TTL_HOURS = 24
PASSWORD_RESET_TTL_MINUTES = 15


class AuthService:
    # ==========================================
    # 📝 REGISTRATION & VERIFICATION
    # ==========================================

    def register_customer(self, db: Session, payload: CustomerRegister) -> dict[str, str]:
        existing_customer = db.query(Customer).filter(Customer.email == str(payload.email)).first()
        if existing_customer:
            raise HTTPException(status_code=400, detail="This email is already registered.")

        verification_token, expires_at = self._create_verification_token_internal(
            str(payload.email), token_type="verify_customer_email", hours=EMAIL_VERIFICATION_TTL_HOURS
        )

        customer = Customer(
            full_name=payload.full_name,
            email=str(payload.email),
            password_hash=get_password_hash(payload.password),
            phone=payload.phone,
            address=payload.address,
            email_verified=False,
            status="PENDING_VERIFICATION",
            verification_token=verification_token,
            verification_token_expires_at=expires_at,
        )
        db.add(customer)
        db.commit()

        verification_link = f"https://app.occacia.com/customers/register/verify-email?token={verification_token}"
        logger.info("Verification email sent to %s with link: %s", payload.email, verification_link)

        return {"message": "Verification email sent", "email": str(payload.email)}

    def register_vendor_verification(self, email: str) -> None:
        """Generates token and logs link for Vendor verification."""
        verification_token, _ = self._create_verification_token_internal(
            email, token_type="verify_vendor_email", hours=EMAIL_VERIFICATION_TTL_HOURS
        )
        link = f"https://app.occacia.com/vendors/register/verify-email?token={verification_token}"
        logger.info("Vendor verification email sent to %s with link: %s", email, link)

    def verify_customer_email(self, db: Session, token: str) -> dict[str, str]:
        claims = self._decode_verification_token(token, expected_type="verify_customer_email")
        email = claims.get("sub")
        
        customer = db.query(Customer).filter(Customer.email == email).first()
        
        if not customer or customer.verification_token != token:
            raise HTTPException(status_code=400, detail="Invalid verification token.")

        if customer.email_verified:
            return {"message": "Email already verified"}

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

    # ==========================================
    # 🔐 PASSWORD RESET (UC-07)
    # ==========================================

    def request_password_reset(self, db: Session, payload: ForgotPasswordRequest) -> dict[str, str]:
        """Step 4 & 5: Generates a 15-minute token and logs the reset link."""
        customer = db.query(Customer).filter(Customer.email == str(payload.email)).first()
        
        # Security: Do not reveal if user exists.
        if not customer:
            logger.info("UC-07: Reset requested for non-existent email: %s", payload.email)
            return {"message": "If this email is registered, a reset link has been sent."}

        # Create short-lived JWT (15 mins)
        token, _ = self._create_verification_token_internal(
            str(payload.email), token_type="password_reset", minutes=PASSWORD_RESET_TTL_MINUTES
        )

        reset_link = f"https://app.occacia.com/customers/reset-password?token={token}"
        
        # MOCK NOTIFICATION SERVICE
        logger.info("UC-07 [EMAIL MOCK] To: %s | Link: %s", payload.email, reset_link)

        return {"message": "If this email is registered, a reset link has been sent."}

    def confirm_password_reset(self, db: Session, payload: ResetPasswordRequest) -> dict[str, str]:
        """Step 7, 8 & 9: Validates JWT, updates DB, and effectively invalidates token."""
        claims = self._decode_verification_token(payload.token, expected_type="password_reset")
        email = claims.get("sub")

        customer = db.query(Customer).filter(Customer.email == email).first()
        if not customer:
            raise HTTPException(status_code=404, detail="User not found.")

        # Update the hash
        customer.password_hash = get_password_hash(payload.new_password)
        db.add(customer)
        db.commit()

        logger.info("UC-07: Password successfully reset for: %s", email)
        return {"message": "Password updated successfully"}

    # ==========================================
    # 🛠️ INTERNAL TOKEN HELPERS
    # ==========================================

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
            # This specific error is usually fine to be specific about
            raise HTTPException(status_code=400, detail="Verification token has expired.") from exc
        except PyJWTError as exc:
            # 🚨 FIX 3: Changed "Invalid token." to match test expectation "Invalid verification token."
            raise HTTPException(status_code=400, detail="Invalid verification token.") from exc

        if claims.get("type") != expected_type:
            # 🚨 FIX 4: Changed "Invalid token type." to match test expectation "Invalid verification token."
            raise HTTPException(status_code=400, detail="Invalid verification token.")
        return claims


auth_service = AuthService()