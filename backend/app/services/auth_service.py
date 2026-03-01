from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import HTTPException
from jwt.exceptions import ExpiredSignatureError, PyJWTError
from sqlalchemy.orm import Session

from app.core.security import ALGORITHM, SECRET_KEY, get_password_hash
from app.models.marketplace import Customer, Vendor
from app.schemas.auth_schema import CustomerRegister

logger = logging.getLogger(__name__)

EMAIL_VERIFICATION_TTL_HOURS = 24


class AuthService:
    def register_customer(self, db: Session, payload: CustomerRegister) -> dict[str, str]:
        existing_customer = db.query(Customer).filter(Customer.email == str(payload.email)).first()
        if existing_customer:
            raise HTTPException(status_code=400, detail="This email is already registered.")

        verification_token, expires_at = self._create_email_verification_token(
            str(payload.email)
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

        verification_link = (
            "https://app.occacia.com/customers/register/verify-email"
            f"?token={verification_token}"
        )
        # MVP behavior: we log the generated link as a stand-in for email delivery.
        logger.info("Verification email sent to %s with link: %s", payload.email, verification_link)

        return {"message": "Verification email sent", "email": str(payload.email)}

    def verify_customer_email(self, db: Session, token: str) -> dict[str, str]:
        claims = self._decode_verification_token(token, expected_type="verify_customer_email")
        email = claims.get("sub")
        if not email:
            raise HTTPException(status_code=400, detail="Invalid verification token.")

        customer = db.query(Customer).filter(Customer.email == email).first()
        if not customer:
            raise HTTPException(status_code=400, detail="Invalid verification token.")

        if customer.email_verified:
            return {"message": "Email already verified"}

        if customer.verification_token != token:
            raise HTTPException(status_code=400, detail="Invalid verification token.")

        token_expires_at = customer.verification_token_expires_at
        if token_expires_at is not None:
            if token_expires_at.tzinfo is None:
                token_expires_at = token_expires_at.replace(tzinfo=UTC)
            if token_expires_at < datetime.now(UTC):
                raise HTTPException(status_code=400, detail="Verification token has expired.")

        customer.email_verified = True
        customer.status = "ACTIVE"
        customer.verification_token = None
        customer.verification_token_expires_at = None
        db.add(customer)
        db.commit()

        return {"message": "Email verified successfully"}

    def register_vendor_verification(self, email: str) -> None:
        verification_token, _ = self._create_email_verification_token(
            email,
            token_type="verify_vendor_email",
        )
        verification_link = (
            "https://app.occacia.com/vendors/register/verify-email"
            f"?token={verification_token}"
        )
        logger.info("Vendor verification email sent to %s with link: %s", email, verification_link)

    def verify_vendor_email(self, db: Session, token: str) -> dict[str, str]:
        claims = self._decode_verification_token(token, expected_type="verify_vendor_email")
        email = claims.get("sub")
        if not email:
            raise HTTPException(status_code=400, detail="Invalid verification token.")

        vendor = db.query(Vendor).filter(Vendor.email == email).first()
        if not vendor:
            raise HTTPException(status_code=400, detail="Invalid verification token.")

        if vendor.is_verified:
            return {"message": "Email already verified"}

        vendor.is_verified = True
        db.add(vendor)
        db.commit()
        return {"message": "Email verified successfully"}

    @staticmethod
    def _create_email_verification_token(
        email: str, token_type: str = "verify_customer_email"
    ) -> tuple[str, datetime]:
        expires_at = datetime.now(UTC) + timedelta(hours=EMAIL_VERIFICATION_TTL_HOURS)
        payload = {"sub": email, "type": token_type, "exp": expires_at}
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
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
            raise HTTPException(status_code=400, detail="Invalid verification token.")
        return claims


auth_service = AuthService()
